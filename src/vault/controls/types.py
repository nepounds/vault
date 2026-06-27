"""Official control flag type values."""

from __future__ import annotations

from enum import StrEnum


class ControlFlagType(StrEnum):
    """Supported initial control flag types."""

    MISSING_INVOICE_NUMBER = "missing_invoice_number"
    MISSING_INVOICE_DATE = "missing_invoice_date"
    MISSING_DUE_DATE = "missing_due_date"
    NON_USD_CURRENCY = "non_usd_currency"
    HIGH_AMOUNT = "high_amount"
    DUPLICATE_FILE_HASH = "duplicate_file_hash"
    DUPLICATE_INVOICE_ATTRIBUTES = "duplicate_invoice_attributes"


FLAG_TYPE_VALUES: tuple[str, ...] = tuple(
    flag_type.value for flag_type in ControlFlagType
)
