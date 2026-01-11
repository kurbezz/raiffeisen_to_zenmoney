from dataclasses import dataclass
from typing import Self

from services.emails_statements.statement import RawOperation


@dataclass
class SimpleOperation:
    customer: str
    amount: float
    currency: str
    date: str

    @classmethod
    def from_raw(cls, raw_operation: RawOperation) -> Self:
        return cls(
            customer=raw_operation.customer,
            amount=raw_operation.amount,
            currency=raw_operation.currency,
            date=raw_operation.data,
        )


@dataclass
class TransitionOperation:
    from_amount: float
    from_currency: str

    to_amount: float
    to_currency: str

    date: str

    @classmethod
    def from_raw(cls, from_operation: RawOperation, to_operation: RawOperation) -> Self:
        return cls(
            from_amount=from_operation.amount,
            from_currency=from_operation.currency,
            to_amount=to_operation.amount,
            to_currency=to_operation.currency,
            date=from_operation.data,
        )


@dataclass
class DeelTransferOperation:
    """Transfer operation from Deel to bank account"""

    customer: str
    amount: float
    currency: str
    date: str

    @classmethod
    def from_raw(cls, raw_operation: RawOperation) -> Self:
        return cls(
            customer=raw_operation.customer,
            amount=raw_operation.amount,
            currency=raw_operation.currency,
            date=raw_operation.data,
        )


@dataclass
class CashWithdrawalOperation:
    """Cash withdrawal operation from ATM or bank branch"""

    customer: str
    amount: float
    currency: str
    date: str

    @classmethod
    def from_raw(cls, raw_operation: RawOperation) -> Self:
        return cls(
            customer=raw_operation.customer,
            amount=raw_operation.amount,
            currency=raw_operation.currency,
            date=raw_operation.data,
        )
