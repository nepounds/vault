"""Service functions for Vault accounting-control flags."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from vault.controls.models import ControlFlag
from vault.controls.severities import SEVERITY_VALUES, ControlFlagSeverity
from vault.controls.types import FLAG_TYPE_VALUES, ControlFlagType
from vault.documents.models import Document, DocumentFact
from vault.exceptions import ControlFlagNotFoundError, ControlFlagValidationError

HIGH_AMOUNT_THRESHOLD_CENTS = 100_000

_SEVERITY_ORDER = {
    ControlFlagSeverity.BLOCKER.value: 0,
    ControlFlagSeverity.WARNING.value: 1,
    ControlFlagSeverity.INFO.value: 2,
}


def create_control_flag(
    session: Session,
    *,
    document_id: UUID,
    flag_type: str,
    severity: str,
    reason: str,
) -> ControlFlag:
    """Create one accounting-control flag for a document."""
    clean_flag_type = _validate_flag_type(flag_type)
    clean_severity = _validate_severity(severity)
    clean_reason = _require_non_blank(reason, field_name="reason")

    flag = ControlFlag(
        document_id=document_id,
        flag_type=clean_flag_type,
        severity=clean_severity,
        reason=clean_reason,
    )
    session.add(flag)
    session.flush()

    return flag


def find_duplicate_documents_by_hash(
    session: Session,
    *,
    document_id: UUID,
) -> list[Document]:
    """Find same-organization documents with the same SHA-256 hash."""
    target_document = session.get(Document, document_id)
    if target_document is None:
        return []

    statement = (
        select(Document)
        .where(
            Document.organization_id == target_document.organization_id,
            Document.sha256_hash == target_document.sha256_hash,
            Document.id != target_document.id,
        )
        .order_by(Document.created_at.asc(), Document.id.asc())
    )

    return list(session.scalars(statement))


def find_duplicate_invoice_facts(
    session: Session,
    *,
    document_id: UUID,
) -> list[DocumentFact]:
    """Find same-organization invoice facts with matching key attributes."""
    target_document = session.get(Document, document_id)
    if target_document is None:
        return []

    target_facts = _list_duplicate_candidate_facts(
        session,
        document_id=document_id,
    )
    duplicate_facts_by_id: dict[UUID, DocumentFact] = {}

    for fact in target_facts:
        statement = (
            select(DocumentFact)
            .join(Document, Document.id == DocumentFact.document_id)
            .where(
                Document.organization_id == target_document.organization_id,
                DocumentFact.document_id != document_id,
                func.lower(DocumentFact.vendor_name) == fact.vendor_name.lower(),
                DocumentFact.invoice_number == fact.invoice_number,
                DocumentFact.amount_cents == fact.amount_cents,
            )
            .order_by(DocumentFact.created_at.asc(), DocumentFact.id.asc())
        )
        for duplicate_fact in session.scalars(statement):
            duplicate_facts_by_id[duplicate_fact.id] = duplicate_fact

    return sorted(
        duplicate_facts_by_id.values(),
        key=lambda fact: (fact.created_at, fact.id),
    )


def generate_duplicate_control_flags_for_document(
    session: Session,
    *,
    document_id: UUID,
) -> list[ControlFlag]:
    """Generate duplicate-oriented control flags for one document."""
    created_flags: list[ControlFlag] = []

    duplicate_documents = find_duplicate_documents_by_hash(
        session,
        document_id=document_id,
    )
    if duplicate_documents:
        created_flags.append(
            create_control_flag(
                session,
                document_id=document_id,
                flag_type=ControlFlagType.DUPLICATE_FILE_HASH.value,
                severity=ControlFlagSeverity.BLOCKER.value,
                reason=_duplicate_file_hash_reason(duplicate_documents),
            )
        )

    duplicate_facts = find_duplicate_invoice_facts(
        session,
        document_id=document_id,
    )
    if duplicate_facts:
        created_flags.append(
            create_control_flag(
                session,
                document_id=document_id,
                flag_type=ControlFlagType.DUPLICATE_INVOICE_ATTRIBUTES.value,
                severity=ControlFlagSeverity.WARNING.value,
                reason=_duplicate_invoice_attributes_reason(duplicate_facts),
            )
        )

    if created_flags:
        session.flush()

    return created_flags


def list_control_flags(
    session: Session,
    *,
    document_id: UUID,
) -> list[ControlFlag]:
    """List control flags for one document, highest severity first."""
    statement = (
        select(ControlFlag)
        .where(ControlFlag.document_id == document_id)
        .order_by(ControlFlag.created_at.asc(), ControlFlag.id.asc())
    )
    flags = list(session.scalars(statement))

    return sorted(
        flags,
        key=lambda flag: (
            _SEVERITY_ORDER.get(flag.severity, len(_SEVERITY_ORDER)),
            flag.created_at,
            flag.id,
        ),
    )


def get_control_flag(
    session: Session,
    *,
    document_id: UUID,
    flag_id: UUID,
) -> ControlFlag | None:
    """Return one document-scoped control flag, or None when missing."""
    statement = select(ControlFlag).where(
        ControlFlag.document_id == document_id,
        ControlFlag.id == flag_id,
    )

    return session.scalar(statement)


def require_control_flag(
    session: Session,
    *,
    document_id: UUID,
    flag_id: UUID,
) -> ControlFlag:
    """Return one document-scoped flag or raise a safe not-found error."""
    flag = get_control_flag(session, document_id=document_id, flag_id=flag_id)
    if flag is None:
        raise ControlFlagNotFoundError("Control flag was not found.")

    return flag


def generate_control_flags_for_document(
    session: Session,
    *,
    document_id: UUID,
) -> list[ControlFlag]:
    """Generate initial control flags from facts for one document."""
    facts = _list_facts_for_generation(session, document_id=document_id)
    created_flags: list[ControlFlag] = []

    for fact in facts:
        created_flags.extend(_generate_flags_for_fact(session, fact=fact))

    if created_flags:
        session.flush()

    return created_flags


def _list_duplicate_candidate_facts(
    session: Session,
    *,
    document_id: UUID,
) -> list[DocumentFact]:
    statement = (
        select(DocumentFact)
        .where(
            DocumentFact.document_id == document_id,
            DocumentFact.invoice_number.is_not(None),
            func.length(func.trim(DocumentFact.invoice_number)) > 0,
        )
        .order_by(DocumentFact.created_at.asc(), DocumentFact.id.asc())
    )

    return list(session.scalars(statement))


def _duplicate_file_hash_reason(duplicate_documents: list[Document]) -> str:
    duplicate_count = len(duplicate_documents)
    return (
        "Duplicate file hash detected against "
        f"{duplicate_count} other document(s) in this organization."
    )


def _duplicate_invoice_attributes_reason(
    duplicate_facts: list[DocumentFact],
) -> str:
    duplicate_count = len(duplicate_facts)
    return (
        "Duplicate vendor/invoice/amount attributes detected against "
        f"{duplicate_count} fact(s) on other document(s) in this organization."
    )

def _list_facts_for_generation(
    session: Session,
    *,
    document_id: UUID,
) -> list[DocumentFact]:
    statement = (
        select(DocumentFact)
        .where(DocumentFact.document_id == document_id)
        .order_by(DocumentFact.created_at.asc(), DocumentFact.id.asc())
    )

    return list(session.scalars(statement))


def _generate_flags_for_fact(
    session: Session,
    *,
    fact: DocumentFact,
) -> list[ControlFlag]:
    created_flags: list[ControlFlag] = []

    if fact.invoice_number is None:
        created_flags.append(
            create_control_flag(
                session,
                document_id=fact.document_id,
                flag_type=ControlFlagType.MISSING_INVOICE_NUMBER.value,
                severity=ControlFlagSeverity.WARNING.value,
                reason="Invoice number is missing, so the invoice is harder to match.",
            )
        )

    if fact.invoice_date is None:
        created_flags.append(
            create_control_flag(
                session,
                document_id=fact.document_id,
                flag_type=ControlFlagType.MISSING_INVOICE_DATE.value,
                severity=ControlFlagSeverity.WARNING.value,
                reason="Invoice date is missing, so the accounting period is unclear.",
            )
        )

    if fact.due_date is None:
        created_flags.append(
            create_control_flag(
                session,
                document_id=fact.document_id,
                flag_type=ControlFlagType.MISSING_DUE_DATE.value,
                severity=ControlFlagSeverity.INFO.value,
                reason="Due date is missing, so payment timing cannot be reviewed.",
            )
        )

    if fact.currency != "USD":
        created_flags.append(
            create_control_flag(
                session,
                document_id=fact.document_id,
                flag_type=ControlFlagType.NON_USD_CURRENCY.value,
                severity=ControlFlagSeverity.WARNING.value,
                reason=(
                    "Currency is not USD, so the invoice may need "
                    "conversion review."
                ),
            )
        )

    if fact.amount_cents >= HIGH_AMOUNT_THRESHOLD_CENTS:
        created_flags.append(
            create_control_flag(
                session,
                document_id=fact.document_id,
                flag_type=ControlFlagType.HIGH_AMOUNT.value,
                severity=ControlFlagSeverity.BLOCKER.value,
                reason="Invoice amount is high enough to require extra review.",
            )
        )

    return created_flags


def _validate_flag_type(flag_type: str) -> str:
    clean_flag_type = _require_non_blank(flag_type, field_name="flag_type")
    if clean_flag_type not in FLAG_TYPE_VALUES:
        raise ControlFlagValidationError("flag_type is not supported")

    return clean_flag_type


def _validate_severity(severity: str) -> str:
    clean_severity = _require_non_blank(severity, field_name="severity")
    if clean_severity not in SEVERITY_VALUES:
        raise ControlFlagValidationError("severity is not supported")

    return clean_severity


def _require_non_blank(value: str, *, field_name: str) -> str:
    clean_value = value.strip()
    if not clean_value:
        raise ControlFlagValidationError(f"{field_name} is required")

    return clean_value
