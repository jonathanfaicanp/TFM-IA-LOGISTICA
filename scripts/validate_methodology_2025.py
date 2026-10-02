"""Reconstruct existing experiments using 2024 references and 2025 only."""

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

import evaluate_baseline_strategies as baselines
import evaluate_detector_candidates as candidates
import analyze_distance_threshold_sensitivity as distance
import analyze_temporal_robustness as temporal
import analyze_b30_mad as mad
import evaluate_synthetic_benchmark as consumption_benchmark
import evaluate_temporal_synthetic_benchmark as temporal_benchmark
from compare_baselines import write_csv


def run(input_path: Path, output_dir: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    split = ((2024,), 2025)
    original = baselines.run(input_path, output_dir / 'baseline_original')
    history, evaluation = candidates.load_records(input_path, *split)
    counts = Counter(r['vehicle'] for r in history)
    eligible = {v for v, n in counts.items() if n >= 100}
    eligible_history = [r for r in history if r['vehicle'] in eligible]
    vehicle, context = baselines.build_baselines(eligible_history)
    summaries, ranges = [], []
    for name, minimum in baselines.STRATEGIES.items():
        summary, rows = baselines.evaluate_strategy(name, minimum, evaluation, vehicle, context)
        summaries.append(summary)
        ranges.extend(rows)
    write_csv(output_dir / 'baseline_eligible_by_range.csv', list(ranges[0]), ranges)
    candidates.run(input_path, output_dir / 'candidates_original', *split)
    scored = candidates.evaluate_records(eligible_history, evaluation)
    candidate_rows, candidate_ranges = [], []
    for definition in candidates.scenario_definitions():
        summary, rows = candidates.summarize_scenario(*definition, scored)
        candidate_rows.append(summary)
        candidate_ranges.extend(rows)
    write_csv(output_dir / 'candidates_eligible.csv', list(candidate_rows[0]), candidate_rows)
    write_csv(output_dir / 'candidates_eligible_by_range.csv', list(candidate_ranges[0]), candidate_ranges)
    distance.run(input_path, output_dir / 'distance_consumption_original', *split)
    consumption_distance, consumption_ranges = [], []
    for name, minimum in distance.SCENARIOS:
        summary, rows = distance.scenario_summary(name, minimum, evaluation, vehicle, context)
        summary['coverage_pct_of_remaining'] = distance.pct(summary['records_evaluable_b30'], summary['records_after_distance_filter'])
        consumption_distance.append(summary)
        consumption_ranges.extend(rows)
    write_csv(output_dir / 'distance_consumption_eligible.csv', list(consumption_distance[0]), consumption_distance)
    write_csv(output_dir / 'distance_consumption_eligible_by_range.csv', list(consumption_ranges[0]), consumption_ranges)
    mad_summary = mad.run(input_path, output_dir / 'mad_original', *split)
    th, te = temporal.load_records(input_path, *split)
    temporal_full = temporal.analyze(th, te, evaluation_year=2025)
    temporal_scenarios = []
    for mode in ('fixed_history', 'filtered_history'):
        for name, minimum in distance.SCENARIOS:
            selected = [r for r in te if r['reason'] is None and (minimum is None or r['distance_km'] > minimum)]
            reference = th if mode == 'fixed_history' else [r for r in th if minimum is None or r['distance_km'] > minimum]
            result = temporal.analyze(reference, selected, evaluation_year=2025)
            tv, tc = temporal.build_scopes(reference)
            row = {'history_mode': mode, 'scenario': name, 'minimum_distance_km_strict': minimum,
                   'valid_records_initial': temporal_full['valid_temporal_2025'],
                   'records_after_distance_filter': len(selected),
                   'records_discarded_by_filter': temporal_full['valid_temporal_2025'] - len(selected),
                   'history_valid_records': len(reference), 'history_eligible_vehicles': len(tv),
                   'history_eligible_contexts': len(tc), **result}
            row['minutes_per_km'] = temporal.distribution([r['minutes_per_km'] for r in selected])
            temporal_scenarios.append(row)
    consumption_benchmark.run(input_path, output_dir / 'consumption_benchmark', *split)
    consumption_benchmark.build_rule_comparison(output_dir / 'consumption_benchmark/synthetic_benchmark_summary.csv', output_dir / 'consumption_benchmark/synthetic_benchmark_rule_comparison.csv')
    temporal_benchmark.run(input_path, output_dir / 'temporal_benchmark', *split)
    result = {'construction_years': [2024], 'evaluation_year': 2025,
              'input_sha256': hashlib.sha256(input_path.read_bytes()).hexdigest(),
              'history_valid_consumption': len(history), 'history_vehicles': len(counts),
              'history_eligible_vehicles_ge_100': len(eligible), 'history_eligible_records_ge_100': len(eligible_history),
              'history_vehicle_count_distribution': temporal.distribution(list(counts.values())),
              'history_contexts': len(context),
              'history_contexts_ge_30': sum(n >= 30 for _, n in context.values()),
              'history_contexts_ge_50': sum(n >= 50 for _, n in context.values()),
              'baseline_original': original, 'baseline_eligible': summaries,
              'candidates_eligible': candidate_rows, 'distance_consumption_eligible': consumption_distance,
              'mad_original': mad_summary, 'temporal_full': temporal_full,
              'temporal_distance_scenarios': temporal_scenarios,
              'selection_status': 'PENDING_TECHNICAL_CONFIRMATION', 'final_2026_executed': False}
    (output_dir / 'validation_2025.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=Path('data/datos_operativa.csv'))
    parser.add_argument('--output-dir', type=Path, default=Path('data/validation_2025'))
    args = parser.parse_args()
    result = run(args.input, args.output_dir)
    print(json.dumps({k: result[k] for k in ('history_valid_consumption', 'history_eligible_vehicles_ge_100', 'selection_status', 'final_2026_executed')}, indent=2))
