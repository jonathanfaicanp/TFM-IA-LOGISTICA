import sys
import unittest
import csv
import tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from evaluation.benchmark_metrics import paired_review_metrics
from evaluate_synthetic_benchmark import evaluate_group, build_rule_comparison, RULES
from evaluate_temporal_synthetic_benchmark import evaluate_rule, build_comparison


class PairedBenchmarkTests(unittest.TestCase):
    def test_final_consumption_25_percent(self):
        before = {i: i < 455 for i in range(6230)}
        after = {i: i < 1181 for i in range(6230)}
        result = paired_review_metrics(before, after)
        self.assertEqual(result['new_reviews'], 726)
        self.assertEqual(result['non_review_before'], 5775)
        self.assertEqual(result['incremental_detection_rate'], 726 / 5775)
        self.assertAlmostEqual(100 * result['incremental_detection_rate'], 12.5714285714)

    def test_already_review_not_new_and_losses_counted(self):
        result = paired_review_metrics({'a': True, 'b': True, 'c': False},
                                       {'a': True, 'b': False, 'c': True})
        self.assertEqual(result['new_reviews'], 1)
        self.assertEqual(result['review_lost'], 1)
        self.assertEqual(result['incremental_detection_rate'], 1)
        self.assertEqual(result['review_before'], result['review_after'])

    def test_mismatched_populations_rejected(self):
        with self.assertRaises(ValueError): paired_review_metrics({'a': False}, {'b': True})

    def test_undefined_denominators(self):
        self.assertIsNone(paired_review_metrics({}, {})['baseline_review_rate'])
        self.assertIsNone(paired_review_metrics({'a': True}, {'a': True})['incremental_detection_rate'])

    def test_final_observed_monotonic_counts_without_imposing_monotonicity(self):
        # Audited snapshot counts: regression fixture, not a fresh statistical audit.
        for n, basal, counts in ((6230, 455, [1181, 2944, 5118, 5777, 6126]),
                                  (9644, 1257, [2395, 3875, 6350, 8422, 9515])):
            before = {i: i < basal for i in range(n)}
            rates = []
            for count in counts:
                result = paired_review_metrics(before, {i: i < count for i in range(n)})
                self.assertEqual(result['review_lost'], 0)
                rates.append(result['incremental_detection_rate'])
            self.assertEqual(rates, sorted(rates))
        # A declining scenario must still be valid input, with losses reported.
        self.assertEqual(paired_review_metrics({0: True}, {0: False})['review_lost'], 1)

    def test_both_evaluators_export_paired_metrics(self):
        rule = next(r for r in RULES if r[0] == 'D3_AND_relative_gt_50pct_z_gt_2')
        consumption = [{'trip_id': str(i), 'l_100km': v, 'consumption_liters': v/10,
                        'distance_km': 10, 'centre': 10, 'scale': 1.4826}
                       for i, v in enumerate((10, 14, 20))]
        temporal = [{'trip_id': str(i), 'minutes_per_km': v, 'duration_minutes': v*10,
                     'distance_km': 10, 'baseline': 10, 'mad': 1}
                    for i, v in enumerate((10, 14, 20))]
        for result in (evaluate_group(consumption, .25, rule), evaluate_rule(temporal, .25, rule)):
            self.assertEqual(result['review_before'], 1)
            self.assertEqual(result['review_after'], 2)
            self.assertEqual(result['new_reviews'], 1)
            self.assertEqual(result['incremental_detection_rate'], .5)
            self.assertFalse(any('recall' in k or 'specificity' in k for k in result))
        with self.assertRaises(ValueError): evaluate_group(consumption + consumption, .25, rule)

    def test_temporal_comparison_uses_only_current_names(self):
        rows = []
        for name, *_ in RULES:
            for level in (25, 50, 100, 200, 500):
                rows.append({'scenario': name, 'perturbation_pct': level,
                             **paired_review_metrics({0: False}, {0: True})})
        for result in build_comparison(rows):
            self.assertEqual(result['incremental_detection_rate_plus_25'], 1)
            self.assertFalse(any('recall' in k or 'specificity' in k for k in result))

    def test_consumption_comparison_preserves_current_rates_and_empty_populations(self):
        for flags in ({0: False}, {}):
            after = {key: True for key in flags}
            metrics = paired_review_metrics(flags, after)
            rows = [{'scenario': name, 'scope': 'completo', 'perturbation_pct': level, **metrics}
                    for name, *_ in RULES for level in (25, 50, 100, 200, 500)]
            with tempfile.TemporaryDirectory() as directory:
                source, output = Path(directory)/'summary.csv', Path(directory)/'comparison.csv'
                with source.open('w', encoding='utf-8', newline='') as file:
                    writer = csv.DictWriter(file, fieldnames=list(rows[0]))
                    writer.writeheader()
                    writer.writerows(rows)
                comparison = build_rule_comparison(source, output)
            self.assertEqual(comparison[0]['incremental_detection_rate_plus_25'],
                             metrics['incremental_detection_rate'])
            self.assertEqual(comparison[0]['baseline_review_rate'], metrics['baseline_review_rate'])

if __name__ == '__main__': unittest.main()
