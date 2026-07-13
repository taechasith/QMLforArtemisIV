"""Post-Gate-5 exploratory protocol guards."""

from __future__ import annotations

from typing import Any, Mapping

from .gate4 import FinalTestAccessError


LOCKED_DATA_SCOPES = {
    "calibration",
    "uncertainty_calibration",
    "final_test",
    "in_distribution_final_test",
    "out_of_distribution_final_test",
    "gate6",
}


def _post_gate5_block(config: Mapping[str, Any]) -> Mapping[str, Any]:
    if "post_gate5_exploratory_protocol" in config:
        block = config["post_gate5_exploratory_protocol"]
    else:
        block = config
    if not isinstance(block, Mapping):
        raise ValueError("Post-Gate-5 config block must be a mapping")
    return block


def assert_post_gate5_scope(
    config: Mapping[str, Any],
    *,
    action: str,
    data_scope: str,
) -> None:
    """Enforce D008's implementation/synthetic-only acceptance boundary."""

    block = _post_gate5_block(config)
    if data_scope in LOCKED_DATA_SCOPES:
        raise FinalTestAccessError(f"{data_scope} remains locked after D008")
    if data_scope != "synthetic":
        if not bool(block.get("research_data_fitting_authorized", False)):
            raise PermissionError(
                "D008 does not authorize research-data fitting or execution"
            )
        if action not in {"preflight", "research_fit"}:
            raise PermissionError(f"Unexpected post-Gate-5 action: {action}")
        return
    if action == "implementation" and bool(block.get("implementation_authorized")):
        return
    if action == "synthetic_validation" and bool(
        block.get("synthetic_validation_authorized")
    ):
        return
    raise PermissionError(f"D008 does not authorize {action} on {data_scope} data")


def validate_future_research_discussion_row(
    row: Mapping[str, Any],
    required_fields: list[str],
) -> None:
    """Validate the D008 future-research firewall row shape and booleans."""

    missing = [field for field in required_fields if field not in row]
    if missing:
        raise ValueError(f"Future-research discussion row missing fields: {missing}")
    expected = {
        "new_protocol_required": True,
        "active_pipeline_change_authorized": False,
        "post_outcome_retry_authorized": False,
    }
    for field, expected_value in expected.items():
        actual = row[field]
        if isinstance(actual, str):
            actual = actual.strip().lower() == "true"
        if bool(actual) != expected_value:
            raise ValueError(f"{field} must be {expected_value}")
