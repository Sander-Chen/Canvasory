"""Typed business receipts for one public Image PPT operation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping
from uuid import UUID, uuid4


BUSINESS_RECEIPT_SCHEMA = "image-pptgen.business-receipt/v1"

DECK_EVENTS = frozenset(
    {"material_accepted", "split_proposed", "split_revised", "split_confirmed"}
)
GENERATION_EVENTS = frozenset(
    {
        "submission_intent",
        "generation_accepted",
        "observation_interrupted",
        "follow_terminal",
        "delivery_interrupted",
        "result_delivered",
        "recovery_started",
        "recovery_exhausted",
    }
)
RUN_READ_EVENTS = frozenset(
    {"observation_interrupted", "follow_terminal", "delivery_interrupted", "result_delivered"}
)

_EVENT_OUTCOMES = {
    "material_accepted": frozenset({"accepted"}),
    "split_proposed": frozenset({"prepared"}),
    "split_revised": frozenset({"prepared"}),
    "split_confirmed": frozenset({"confirmed"}),
    "submission_intent": frozenset({"prepared", "unknown"}),
    "generation_accepted": frozenset({"accepted"}),
    "observation_interrupted": frozenset({"interrupted"}),
    "follow_terminal": frozenset({"completed", "partially_completed", "failed"}),
    "delivery_interrupted": frozenset({"interrupted"}),
    "result_delivered": frozenset({"completed", "partially_completed", "failed"}),
    "recovery_started": frozenset({"prepared"}),
    "recovery_exhausted": frozenset({"exhausted"}),
}


class BusinessReceiptError(ValueError):
    """Raised when a business receipt violates the versioned protocol."""


def _positive_int(value: Any, field_name: str) -> int:
    if type(value) is not int or value <= 0:
        raise BusinessReceiptError(f"{field_name} must be a positive integer")
    return value


def _operation_id(value: Any) -> str:
    if not isinstance(value, str):
        raise BusinessReceiptError("operation_id must be a UUID")
    try:
        parsed = UUID(value)
    except (TypeError, ValueError) as exc:
        raise BusinessReceiptError("operation_id must be a UUID") from exc
    if str(parsed) != value:
        raise BusinessReceiptError("operation_id must use canonical UUID text")
    return value


def terminal_outcome(status: Any) -> str:
    """Map a real backend terminal status to the receipt outcome vocabulary."""

    if status == "completed":
        return "completed"
    if status in {"completed_with_failures", "partially_completed"}:
        return "partially_completed"
    if status in {"failed", "timed_out", "skipped"}:
        return "failed"
    raise BusinessReceiptError("backend status is not terminal")


def validate_business_receipt(receipt: Mapping[str, Any]) -> dict[str, Any]:
    """Return a copy of one valid receipt or fail closed."""

    if not isinstance(receipt, Mapping):
        raise BusinessReceiptError("receipt must be an object")
    value = dict(receipt)
    if value.get("schema") != BUSINESS_RECEIPT_SCHEMA:
        raise BusinessReceiptError("unsupported business receipt schema")
    scope = value.get("scope")
    event = value.get("event")
    outcome = value.get("outcome")
    if not isinstance(event, str) or event not in _EVENT_OUTCOMES:
        raise BusinessReceiptError("unsupported business receipt event")
    if outcome not in _EVENT_OUTCOMES[event]:
        raise BusinessReceiptError("business receipt event/outcome mismatch")

    common = {"schema", "scope", "event", "outcome"}
    if scope == "deck_command":
        if event not in DECK_EVENTS:
            raise BusinessReceiptError("business receipt event/scope mismatch")
        _positive_int(value.get("deck_id"), "deck_id")
        allowed = common | {"deck_id"}
        if event != "material_accepted":
            _positive_int(value.get("draft_id"), "draft_id")
            allowed.add("draft_id")
    elif scope == "generation_operation":
        if event not in GENERATION_EVENTS:
            raise BusinessReceiptError("business receipt event/scope mismatch")
        _operation_id(value.get("operation_id"))
        _positive_int(value.get("deck_id"), "deck_id")
        _positive_int(value.get("receipt_index"), "receipt_index")
        recovery_attempt = value.get("recovery_attempt")
        if type(recovery_attempt) is not int or not 0 <= recovery_attempt <= 3:
            raise BusinessReceiptError("recovery_attempt must be between 0 and 3")
        allowed = common | {
            "operation_id",
            "deck_id",
            "receipt_index",
            "recovery_attempt",
        }
        run_required = event != "submission_intent" or outcome != "unknown"
        if event == "submission_intent" and outcome == "prepared":
            run_required = False
        if run_required:
            _positive_int(value.get("run_id"), "run_id")
            allowed.add("run_id")
        elif "run_id" in value:
            _positive_int(value["run_id"], "run_id")
            allowed.add("run_id")
        if event in {
            "observation_interrupted",
            "follow_terminal",
            "delivery_interrupted",
            "result_delivered",
        }:
            backend_status = value.get("backend_status")
            if not isinstance(backend_status, str) or not backend_status:
                raise BusinessReceiptError("backend_status is required for Run observation")
            allowed.add("backend_status")
    elif scope == "run_read":
        if event not in RUN_READ_EVENTS:
            raise BusinessReceiptError("business receipt event/scope mismatch")
        _positive_int(value.get("run_id"), "run_id")
        if "operation_id" in value or "receipt_index" in value or "recovery_attempt" in value:
            raise BusinessReceiptError("run_read receipt cannot claim operation identity")
        backend_status = value.get("backend_status")
        if not isinstance(backend_status, str) or not backend_status:
            raise BusinessReceiptError("backend_status is required for Run observation")
        allowed = common | {"run_id", "backend_status"}
    else:
        raise BusinessReceiptError("unsupported business receipt scope")

    unexpected = set(value) - allowed
    if unexpected:
        raise BusinessReceiptError(
            "business receipt has unsupported fields: " + ", ".join(sorted(unexpected))
        )
    return value


def deck_receipt(
    event: str, *, deck_id: int, draft_id: int | None = None
) -> dict[str, Any]:
    outcomes = {
        "material_accepted": "accepted",
        "split_proposed": "prepared",
        "split_revised": "prepared",
        "split_confirmed": "confirmed",
    }
    receipt: dict[str, Any] = {
        "schema": BUSINESS_RECEIPT_SCHEMA,
        "scope": "deck_command",
        "event": event,
        "outcome": outcomes.get(event),
        "deck_id": deck_id,
    }
    if draft_id is not None:
        receipt["draft_id"] = draft_id
    return validate_business_receipt(receipt)


def run_read_receipt(
    event: str, *, run_id: int, outcome: str, backend_status: str
) -> dict[str, Any]:
    return validate_business_receipt(
        {
            "schema": BUSINESS_RECEIPT_SCHEMA,
            "scope": "run_read",
            "event": event,
            "outcome": outcome,
            "run_id": run_id,
            "backend_status": backend_status,
        }
    )


@dataclass
class GenerationReceiptSequence:
    """Create strictly ordered receipts for one in-process generation operation."""

    deck_id: int
    operation_id: str = field(default_factory=lambda: str(uuid4()))
    _last_index: int = field(default=0, init=False, repr=False)

    def __post_init__(self) -> None:
        _positive_int(self.deck_id, "deck_id")
        _operation_id(self.operation_id)

    def next(
        self,
        event: str,
        *,
        outcome: str,
        run_id: int | None = None,
        backend_status: str | None = None,
        recovery_attempt: int = 0,
    ) -> dict[str, Any]:
        self._last_index += 1
        receipt: dict[str, Any] = {
            "schema": BUSINESS_RECEIPT_SCHEMA,
            "scope": "generation_operation",
            "event": event,
            "outcome": outcome,
            "operation_id": self.operation_id,
            "deck_id": self.deck_id,
            "receipt_index": self._last_index,
            "recovery_attempt": recovery_attempt,
        }
        if run_id is not None:
            receipt["run_id"] = run_id
        if backend_status is not None:
            receipt["backend_status"] = backend_status
        return validate_business_receipt(receipt)


def validate_generation_ledger(
    receipts: Iterable[Mapping[str, Any]], *, require_delivery: bool = True
) -> list[dict[str, Any]]:
    """Validate identity, ordering and the normal producer-consumer lifecycle."""

    values = [validate_business_receipt(receipt) for receipt in receipts]
    if not values:
        raise BusinessReceiptError("generation receipt ledger is empty")
    if any(value["scope"] != "generation_operation" for value in values):
        raise BusinessReceiptError("generation receipt ledger has a foreign scope")
    if [value["receipt_index"] for value in values] != list(range(1, len(values) + 1)):
        raise BusinessReceiptError("generation receipt indexes are not contiguous")
    if len({value["operation_id"] for value in values}) != 1:
        raise BusinessReceiptError("generation receipt operation_id mismatch")
    if len({value["deck_id"] for value in values}) != 1:
        raise BusinessReceiptError("generation receipt deck_id mismatch")

    events = [value["event"] for value in values]
    if events[0] != "submission_intent" or events.count("generation_accepted") != 1:
        raise BusinessReceiptError("generation ledger lacks one accepted submission")
    accepted_index = events.index("generation_accepted")
    if accepted_index <= 0:
        raise BusinessReceiptError("generation acceptance precedes intent")
    run_ids = {value["run_id"] for value in values if "run_id" in value}
    if len(run_ids) != 1:
        raise BusinessReceiptError("generation receipt run_id mismatch")
    if "follow_terminal" in events and events.index("follow_terminal") < accepted_index:
        raise BusinessReceiptError("terminal follow precedes generation acceptance")
    if require_delivery:
        if events.count("follow_terminal") != 1 or events.count("result_delivered") != 1:
            raise BusinessReceiptError("generation ledger lacks terminal follow or delivery")
        if events.index("result_delivered") < events.index("follow_terminal"):
            raise BusinessReceiptError("result delivery precedes terminal follow")
    return values


def with_receipt(payload: Mapping[str, Any], receipt: Mapping[str, Any]) -> dict[str, Any]:
    """Add one validated receipt without replacing legacy top-level fields."""

    value = dict(payload)
    if "receipt" in value:
        raise BusinessReceiptError("payload already contains a business receipt")
    value["receipt"] = validate_business_receipt(receipt)
    return value
