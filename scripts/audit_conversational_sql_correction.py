"""Read-only SQL audit of historical anonymized conversational cases."""
from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
import math
import os
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from evaluation.conversational_dataset import (
    EVALUATION_START, EVALUATION_END, GROUP_ORDER, IDENTITY_FIELDS,
    _anonymized_case, classify_result, select_results,
)
from src.analytical_service import AnalyticalService
from src.sql_repository import SqlHistoricalRepository, REQUIRED_ENVIRONMENT_VARIABLES

ABSOLUTE_CONSUMPTION = {
    'consumo_litros', 'consumo_l_100km', 'consumption_liters',
    'liters_per_100km', 'baseline', 'mad', 'robust_scale',
}
REL_TOL = 1e-9
ABS_TOL = 1e-9


def equal(a, b, rel_tol=REL_TOL, abs_tol=ABS_TOL):
    if isinstance(a, bool) or isinstance(b, bool):
        return type(a) is type(b) and a == b
    if isinstance(a, (float, int)) and isinstance(b, (float, int)):
        return math.isfinite(a) and math.isfinite(b) and math.isclose(a, b, rel_tol=rel_tol, abs_tol=abs_tol)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(equal(x, y, rel_tol, abs_tol) for x, y in zip(a, b))
    return a == b


def invariant_fields(case):
    for key, value in case.items():
        if key not in ('case_id', 'signals'):
            yield key, value
    for signal, values in case['signals'].items():
        for key, value in values.items():
            if key in IDENTITY_FIELDS:
                continue
            if signal == 'consumption' and key in ABSOLUTE_CONSUMPTION:
                continue
            yield f'signals.{signal}.{key}', value


def get_field(candidate, path):
    value = candidate
    for key in path.split('.'):
        if not isinstance(value, dict) or key not in value:
            return False, None
        value = value[key]
    return True, value


def compatible(original, result, rel_tol=REL_TOL, abs_tol=ABS_TOL):
    candidate = _anonymized_case(result, classify_result(result), 1)
    # Optional historical identity metadata can further constrain a match.
    for key in ('trip_id', 'vehicle_id', 'timestamp', 'distance_km'):
        if key in original:
            candidate[key] = result.get(key)
    return all(found and equal(value, corrected, rel_tol, abs_tol)
               for path, value in invariant_fields(original)
               for found, corrected in [get_field(candidate, path)])


def match_case(original, results, rel_tol=REL_TOL, abs_tol=ABS_TOL):
    matches = [r for r in results if compatible(original, r, rel_tol, abs_tol)]
    status = 'UNIQUE_MATCH' if len(matches) == 1 else 'MULTIPLE_MATCHES' if matches else 'NO_MATCH'
    return status, matches


def compare_case(original, corrected, rel_tol=REL_TOL, abs_tol=ABS_TOL):
    rows = []
    fields = [(k, original.get(k), corrected.get(k))
              for k in ('overall_status', 'analysis_coverage', 'review_signals')]
    for signal in sorted(set(original['signals']) | set(corrected['signals'])):
        a, b = original['signals'].get(signal, {}), corrected['signals'].get(signal, {})
        fields.extend((f'signals.{signal}.{k}', a.get(k), b.get(k))
                      for k in sorted(set(a) | set(b)) if k not in IDENTITY_FIELDS)
    for field, a, b in fields:
        numeric = (isinstance(a, (int, float)) and not isinstance(a, bool)
                   and isinstance(b, (int, float)) and not isinstance(b, bool))
        ratio = a / b if numeric and b != 0 and math.isfinite(a) and math.isfinite(b) else None
        absolute = field.startswith('signals.consumption.') and field.split('.')[-1] in ABSOLUTE_CONSUMPTION
        rows.append({'case_id': original['case_id'], 'field': field, 'original': a,
                     'corrected': b, 'ratio_original_to_corrected': ratio,
                     'equal': equal(a, b, rel_tol, abs_tol),
                     'factor_1000': absolute and ratio is not None and equal(ratio, 1000, rel_tol, abs_tol),
                     'absolute_consumption': absolute})
    return rows


def validate_cases(document):
    cases = document.get('cases', [])
    if len(cases) != 20 or document.get('total_selected') != 20:
        raise ValueError('Expected exactly 20 original cases')
    ids = [c.get('case_id') for c in cases]
    if any(not isinstance(x, str) or not x for x in ids) or len(set(ids)) != 20:
        raise ValueError('Expected 20 distinct case_id values')
    if Counter(c.get('stratum') for c in cases) != Counter({g: 5 for g in GROUP_ORDER}):
        raise ValueError('Expected four original strata with five cases each')
    for case in cases:
        if classify_result(case) != case['stratum'] or set(case.get('signals', {})) != {'consumption', 'temporal'}:
            raise ValueError('Invalid original stratum or signals')
    expected = {'from': '2026-01-01', 'to_exclusive': '2027-01-01'}
    if document.get('source_period') != expected:
        raise ValueError('Original source period differs from the existing generator')
    return cases


def validate_paths(cases_path, output_dir, data_root=None):
    source, output = cases_path.resolve(), output_dir.resolve()
    data = (data_root or ROOT / 'data').resolve()
    if not output.is_relative_to(data) or output == data:
        raise ValueError('Audit outputs, including private identifiers, must remain under data/')
    if output.is_relative_to(source.parent) or source.is_relative_to(output):
        raise ValueError('Output cannot overlap the historical artifact directory')
    if output.exists():
        raise ValueError('Use a new output directory; existing audit files are never overwritten')


def audit(cases_path, output_dir, repository, *, data_root=None,
          rel_tol=REL_TOL, abs_tol=ABS_TOL):
    validate_paths(cases_path, output_dir, data_root)
    if not math.isfinite(rel_tol) or not math.isfinite(abs_tol) or min(rel_tol, abs_tol) < 0:
        raise ValueError('Tolerances must be finite and nonnegative')
    source = cases_path.read_bytes()
    document = json.loads(source.decode('utf-8-sig'))
    cases = validate_cases(document)
    history = repository.load_historical_rows()  # Existing 2024+2025 SQL query/adapter.
    service = AnalyticalService.from_history(history)
    raw_rows = repository.load_rows_between(EVALUATION_START, EVALUATION_END)
    results = [service.evaluate(row).to_dict() for row in raw_rows]
    selected, available = select_results(results)
    selected_results = [r for group in GROUP_ORDER for r in selected[group]]
    mapping, comparisons, corrected_cases = [], [], []
    matches_by_case = {}
    for case in cases:
        status, matches = match_case(case, results, rel_tol, abs_tol)
        matches_by_case[case['case_id']] = matches
        mapping.append({'case_id': case['case_id'], 'matching': status,
                        'candidate_count': len(matches),
                        'trip_id': matches[0]['trip_id'] if status == 'UNIQUE_MATCH' else None,
                        'matched_invariant_fields': [key for key, _ in invariant_fields(case)],
                        'candidate_identities': [{'trip_id': r['trip_id'], 'vehicle_id': r['vehicle_id'],
                                                  'timestamp': r['timestamp']} for r in matches]})
        if status == 'UNIQUE_MATCH':
            # Reevaluate the same already-adapted SQL row with the same frozen history.
            position = next(i for i, result in enumerate(results) if result is matches[0])
            result = service.evaluate(raw_rows[position]).to_dict()
            corrected = _anonymized_case(result, case['stratum'], 1)
            corrected['case_id'] = case['case_id']
            comparisons.extend(compare_case(case, corrected, rel_tol, abs_tol))
            corrected_cases.append(corrected)
    counts = Counter(m['matching'] for m in mapping)
    unique = [m for m in mapping if m['matching'] == 'UNIQUE_MATCH']
    unique_trips = len({m['trip_id'] for m in unique})
    can_reuse = counts['UNIQUE_MATCH'] == 20 and unique_trips == 20
    same_selection = can_reuse and [matches_by_case[c['case_id']][0]['trip_id'] for c in cases] == [r['trip_id'] for r in selected_results]
    def changed(fields):
        return len({r['case_id'] for r in comparisons if r['field'] in fields and not r['equal']})
    absolute_changes = [r for r in comparisons if r['absolute_consumption'] and not r['equal']]
    unexpected_absolute_cases = {r['case_id'] for r in absolute_changes if not r['factor_1000']}
    summary = {'total_cases': 20,
               'original_consumption_evaluable': sum(c['signals']['consumption']['status'] != 'NOT_EVALUABLE' for c in cases),
               'matching': {s: counts[s] for s in ('UNIQUE_MATCH', 'MULTIPLE_MATCHES', 'NO_MATCH')},
               'unique_distinct_trips': unique_trips,
               'scale_affected_cases': len({r['case_id'] for r in comparisons if r['factor_1000']}),
               'absolute_consumption_changes_all_factor_1000': all(r['factor_1000'] for r in absolute_changes) if absolute_changes else None,
               'unexpected_absolute_change_cases': len(unexpected_absolute_cases),
               'state_changed_cases': changed({'overall_status', 'signals.consumption.status', 'signals.temporal.status'}),
               'coverage_changed_cases': changed({'analysis_coverage'}),
               'review_signals_changed_cases': changed({'review_signals'}),
               'relative_deviation_changed_cases': changed({'signals.consumption.relative_deviation'}),
               'robust_z_changed_cases': changed({'signals.consumption.robust_z'}),
               'corrected_cases_generated': can_reuse,
               'same_current_deterministic_selection': same_selection,
               'sql_candidate_rows': len(raw_rows), 'historical_rows': len(history),
               'current_stratum_availability': available,
               'original_sha256': hashlib.sha256(source).hexdigest(),
               'float_tolerances': {'relative': rel_tol, 'absolute': abs_tol}}
    if cases_path.read_bytes() != source:
        raise ValueError('Original cases changed during execution; audit cancelled')
    output_dir.mkdir(parents=True, exist_ok=False)
    def write_json(name, value):
        (output_dir / name).write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n', encoding='utf-8')
    write_json('case_mapping_private.json', mapping)
    write_json('comparison.json', {'summary': summary, 'comparisons': comparisons})
    with (output_dir / 'comparison.csv').open('w', encoding='utf-8', newline='') as file:
        columns = ['case_id', 'field', 'original', 'corrected', 'ratio_original_to_corrected', 'equal', 'factor_1000', 'absolute_consumption']
        writer = csv.DictWriter(file, columns); writer.writeheader()
        for row in comparisons:
            writer.writerow({k: json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v for k, v in row.items()})
    if can_reuse:
        corrected = copy.deepcopy(document)
        corrected['cases'] = corrected_cases
        corrected['selection'] = {group: {'requested': 5, 'available': available[group],
                                          'selected': 5, 'shortage': 0} for group in GROUP_ORDER}
        corrected['audit_provenance'] = {'original_sha256': summary['original_sha256'], 'same_current_deterministic_selection': same_selection}
        write_json('corrected_cases.json', corrected)
    lines = ['# Auditoría SQL de corrección de consumo', '',
             'Referencias y adaptador actuales; histórico 2024+2025, candidatos 2026.',
             'Se reutilizan AnalyticalService, clasificación, selección y anonimización originales.',
             'El matching examina todos los candidatos; la selección no desambigua coincidencias.',
             'Los ratios son original/corregido. NULL y ceros no demuestran un factor.', '',
             '| Caso | Resultado | Candidatos |', '| --- | --- | ---: |']
    lines += [f"| {m['case_id']} | {m['matching']} | {m['candidate_count']} |" for m in mapping]
    lines += ['', '## Resumen', '', '```json', json.dumps(summary, ensure_ascii=False, indent=2), '```', '',
              'Los cambios se calculan solo para UNIQUE_MATCH. Estados y métricas invariantes',
              'son también condiciones del matching: cero cambios en casos emparejados no',
              'demuestra invariancia de los casos NO_MATCH o MULTIPLE_MATCHES.',
              'Cambios en SQL/histórico desde el experimento pueden impedir reconstruir la identidad.',
              'No se atribuyen automáticamente esas diferencias al adaptador.', '',
              '## Campos absolutos comparados', '']
    lines += [f"- {r['case_id']} / {r['field']}: {r['original']} → {r['corrected']}; ratio {r['ratio_original_to_corrected']}"
              for r in comparisons if r['absolute_consumption'] and not r['equal']]
    lines += ['', 'Los identificadores reales están solo en case_mapping_private.json, fuera de Git.',
              'Todos los resultados permanecen bajo data/. No hay respuestas ni puntuaciones nuevas.',
              'Mismos 20 viajes reutilizables: ' + ('sí.' if can_reuse else 'no acreditado: faltan 20 matches únicos de viajes distintos.'),
              'Siguiente paso: ' + ('revisar comparación y diferencias inesperadas antes de preparar n8n.' if can_reuse else 'resolver ambigüedades o recuperar un mapping/snapshot histórico; no generar nuevas respuestas.')]
    if unexpected_absolute_cases:
        lines += ['Cambios absolutos distintos del factor 1000: detener la preparación de n8n',
                  'y revisar las diferencias; corrected_cases.json, si existe, no implica aprobación de esas diferencias.']
    (output_dir / 'audit_summary.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cases', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    try:
        validate_paths(args.cases, args.output_dir)
        validate_cases(json.loads(args.cases.read_text(encoding='utf-8-sig')))
        missing = [name for name in REQUIRED_ENVIRONMENT_VARIABLES if not os.environ.get(name)]
        if missing:
            print('Missing SQL environment variables: ' + ', '.join(missing), file=sys.stderr)
            return 1
        repository = SqlHistoricalRepository.from_environment()
        summary = audit(args.cases, args.output_dir, repository)
    except Exception:
        # SQL driver exceptions may disclose host/connection details; never print them.
        print('Audit failed: check input (20 cases/4 strata), a fresh output under data/, and local TFM_DB_* configuration/SQL access. No credentials are accepted as arguments.', file=sys.stderr)
        return 1
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
