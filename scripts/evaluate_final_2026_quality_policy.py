"""Reproduce the final 2026 quality policy without modifying production rules.

Explicit CSV input; aggregate-only JSON output. No hypothetical unit conversion,
benchmark, LLM invocation or historical-output overwrite is performed.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
from dataclasses import replace
from datetime import date, datetime
import hashlib
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.analytical_service import AnalyticalService
from src.consolidation import consolidate_results
from src.models import DetectionResult, DetectionStatus

BOUNDARY = date(2026, 8, 20)
QUALITY_REASON = 'DATA_QUALITY_NON_COMPARABLE_CONSUMPTION_FINAL_EVALUATION'


def apply_quality_policy(consumption: DetectionResult) -> DetectionResult:
    """Evaluation-layer policy only; leave source-derived magnitudes intact."""
    if datetime.fromisoformat(consumption.fecha).date() < BOUNDARY:
        return consumption
    return replace(consumption, status=DetectionStatus.NOT_EVALUABLE,
                   reason=QUALITY_REASON, baseline=None, mad=None,
                   relative_deviation=None, robust_z=None, baseline_type=None,
                   historical_observations=None)


def signal_counts(results: list[DetectionResult]) -> dict:
    counts = Counter(result.status.value for result in results)
    return {'population': len(results),
            'evaluable': len(results) - counts['NOT_EVALUABLE'],
            **{status.value: counts[status.value] for status in DetectionStatus}}


def consolidation_counts(results: list[dict]) -> dict:
    overall = Counter(result['overall_status'] for result in results)
    coverage = Counter(result['analysis_coverage'] for result in results)
    c = sum('consumption' in result['review_signals'] for result in results)
    t = sum('temporal' in result['review_signals'] for result in results)
    both = sum(len(result['review_signals']) == 2 for result in results)
    assert overall['REVIEW'] == c + t - both
    return {'total_trips': len(results),
            'overall_status': {status.value: overall[status.value] for status in DetectionStatus},
            'analysis_coverage': {name: coverage[name] for name in ('COMPLETE', 'PARTIAL', 'NONE')},
            'review_signals': {'consumption': c, 'temporal': t, 'both': both,
                               'only_consumption': c-both, 'only_temporal': t-both}}


def evaluate_rows(rows: list[dict]) -> dict:
    history = [row for row in rows if datetime.fromisoformat(row['Fecha de inicio']).year in (2024, 2025)]
    evaluation = [row for row in rows if datetime.fromisoformat(row['Fecha de inicio']).year == 2026]
    identifiers = [row['Codigo Viaje'] for row in evaluation]
    if len(set(identifiers)) != len(identifiers):
        raise ValueError('Duplicate trip identifiers in the evaluation population')
    service = AnalyticalService.from_history(history)
    before, after, comparable, affected = [], [], [], []
    original_consolidated, final_consolidated = [], []
    for row in evaluation:
        c = service.consumption_detector.evaluate(row)
        t = service.temporal_detector.evaluate(row)
        policy_c = apply_quality_policy(c)
        before.append(c); after.append(policy_c)
        original = consolidate_results(c, t).to_dict()
        final = consolidate_results(policy_c, t).to_dict()
        assert original['signals']['temporal'] == final['signals']['temporal']
        original_consolidated.append(original); final_consolidated.append(final)
        if datetime.fromisoformat(c.fecha).date() < BOUNDARY:
            assert c == policy_c
            comparable.append(policy_c)
        elif c.status != DetectionStatus.NOT_EVALUABLE:
            affected.append(c)
        assert (c.consumo_litros, c.consumo_l_100km) == (policy_c.consumo_litros, policy_c.consumo_l_100km)
    removed_review = sum(result.status == DetectionStatus.REVIEW for result in affected)
    all_review = removed_review == len(affected) if affected else None
    return {
        'history_years': [2024, 2025], 'history_rows': len(history),
        'evaluation_year': 2026, 'consumption_quality_exclusion_from': BOUNDARY.isoformat(),
        'quality_reason': QUALITY_REASON,
        'consumption_before_policy_all_2026': signal_counts(before),
        'consumption_final_comparable': signal_counts(comparable),
        # All trips are retained: recent excluded trips add to NOT_EVALUABLE.
        'consumption_with_policy_all_2026': signal_counts(after),
        'delta': {'evaluable_removed': len(affected), 'review_removed_from_comparison': removed_review,
                  'affected_evaluable_before': len(affected), 'affected_review_before': removed_review,
                  'affected_review_rate': removed_review/len(affected) if affected else None,
                  'all_affected_evaluable_were_review': all_review},
        'consolidation_before_policy': consolidation_counts(original_consolidated),
        'consolidation_final': consolidation_counts(final_consolidated),
        'consolidation_changes': {field: sum(a[field] != b[field] for a, b in zip(original_consolidated, final_consolidated))
                                  for field in ('overall_status', 'analysis_coverage', 'review_signals')},
        'temporal_preserved': True,
    }


def run(input_path: Path) -> dict:
    digest = hashlib.sha256(input_path.read_bytes()).hexdigest()
    with input_path.open(encoding='utf-8-sig', newline='') as source:
        rows = list(csv.DictReader(source, delimiter=';'))
    result = evaluate_rows(rows)
    if hashlib.sha256(input_path.read_bytes()).hexdigest() != digest:
        raise RuntimeError('Input changed while evaluation was running')
    return {'input_sha256': digest, **result}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, help='Optional NEW JSON file; existing files are never overwritten')
    args = parser.parse_args()
    if args.output is not None and args.output.exists():
        parser.error('Output already exists; select a new file')
    text = json.dumps(run(args.input), ensure_ascii=False, indent=2, allow_nan=False) + '\n'
    if args.output is None:
        print(text, end='')
    else:
        with args.output.open('x', encoding='utf-8') as destination:
            destination.write(text)


if __name__ == '__main__':
    main()
