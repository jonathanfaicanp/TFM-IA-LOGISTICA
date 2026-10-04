"""Paired experimental marking rates, without real ground-truth labels.

Rates are fractions in [0, 1]; multiply by 100 for percentage presentation.
Undefined rates are None. Pair keys identify the same trips before and after.
"""
from collections.abc import Mapping


def paired_review_metrics(before: Mapping[object, bool], after: Mapping[object, bool]) -> dict:
    if before.keys() != after.keys():
        raise ValueError("Before/after must contain exactly the same trip identifiers")
    if any(type(value) is not bool for value in (*before.values(), *after.values())):
        raise ValueError("Review flags must be boolean")
    total = len(before)
    reviewed = sum(before.values())
    non_reviewed = total - reviewed
    marked_after = sum(after.values())
    new = sum(not before[key] and after[key] for key in before)
    lost = sum(before[key] and not after[key] for key in before)
    return {
        "n_total": total,
        "review_before": reviewed,
        "non_review_before": non_reviewed,
        "review_after": marked_after,
        "new_reviews": new,
        "review_lost": lost,
        "baseline_review_rate": reviewed / total if total else None,
        "baseline_non_review_rate": non_reviewed / total if total else None,
        "post_perturbation_review_rate": marked_after / total if total else None,
        "incremental_detection_rate": new / non_reviewed if non_reviewed else None,
    }


def record_keys(records: list[dict]) -> list:
    """Use explicit trip identities when supplied, otherwise stable input positions.

    Old loaders never retained trip IDs. Their in-memory copies preserve order;
    position thus identifies the same record, without requiring private IDs.
    """
    keys = [record.get("trip_id", index) for index, record in enumerate(records)]
    if len(set(keys)) != len(keys):
        raise ValueError("Duplicate trip identifiers")
    return keys
