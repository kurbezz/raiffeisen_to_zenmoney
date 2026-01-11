import uuid
from datetime import datetime

from envs import CATEGORY_CONFIG, CURRENCY_CONFIG, DEEL_CONFIG, USER_ID
from services.operations.operations import (
    CashWithdrawalOperation,
    DeelTransferOperation,
    SimpleOperation,
    TransitionOperation,
)
from services.zen_money.zen_money_api import NewZenMoneyState, Transaction


def prepare_new_state(
    operations: list[
        SimpleOperation
        | TransitionOperation
        | DeelTransferOperation
        | CashWithdrawalOperation
    ],
) -> NewZenMoneyState:
    current_timestamp = int(datetime.now().timestamp())
    transactions = []

    for operation in operations:
        if isinstance(operation, SimpleOperation):
            transaction = _create_simple_transaction(operation, current_timestamp)
            transactions.append(transaction)
        elif isinstance(operation, TransitionOperation):
            transaction = _create_transition_transaction(operation, current_timestamp)
            transactions.append(transaction)
        elif isinstance(operation, DeelTransferOperation):
            transaction = _create_deel_transfer_transaction(
                operation, current_timestamp
            )
            transactions.append(transaction)
        elif isinstance(operation, CashWithdrawalOperation):
            transaction = _create_cash_withdrawal_transaction(
                operation, current_timestamp
            )
            transactions.append(transaction)

    return NewZenMoneyState(
        currentClientTimestamp=current_timestamp,
        serverTimestamp=0,
        transaction=transactions if transactions else None,
    )


def _get_category_for_payee(payee: str) -> list[str]:
    if not payee:
        return []

    for key, category_id in CATEGORY_CONFIG.items():
        if key.upper() in payee.upper():
            return [category_id]

    return []


def _create_simple_transaction(
    operation: SimpleOperation, current_timestamp: int
) -> Transaction:
    is_income = operation.amount > 0
    abs_amount = abs(operation.amount)

    currency_config = CURRENCY_CONFIG.get(operation.currency)
    if not currency_config:
        currency_config = CURRENCY_CONFIG["RSD"]

    instrument_id = currency_config["instrument_id"]
    bank_account_id = currency_config["account_id"]
    cash_account_id = currency_config.get("cash_account_id", bank_account_id)

    categories = _get_category_for_payee(operation.customer)

    return Transaction(
        id=str(uuid.uuid4()),
        user=USER_ID,
        date=operation.date,
        income=abs_amount if is_income else 0.0,
        outcome=abs_amount if not is_income else 0.0,
        changed=current_timestamp,
        incomeInstrument=instrument_id,
        outcomeInstrument=instrument_id,
        created=current_timestamp,
        deleted=False,
        viewed=False,
        incomeAccount=bank_account_id if is_income else cash_account_id,
        outcomeAccount=cash_account_id if is_income else bank_account_id,
        payee=operation.customer,
        comment=f"Импорт: {operation.customer} ({operation.currency})",
        tag=categories,
        merchant=None,
    )


def _create_transition_transaction(
    operation: TransitionOperation, current_timestamp: int
) -> Transaction:
    from_amount = abs(operation.from_amount)
    to_amount = abs(operation.to_amount)

    from_config = CURRENCY_CONFIG.get(operation.from_currency, CURRENCY_CONFIG["RSD"])
    to_config = CURRENCY_CONFIG.get(operation.to_currency, CURRENCY_CONFIG["RSD"])

    return Transaction(
        id=str(uuid.uuid4()),
        user=USER_ID,
        date=operation.date,
        income=to_amount,
        outcome=from_amount,
        changed=current_timestamp,
        incomeInstrument=to_config["instrument_id"],
        outcomeInstrument=from_config["instrument_id"],
        created=current_timestamp,
        deleted=False,
        viewed=False,
        incomeAccount=to_config["account_id"],
        outcomeAccount=from_config["account_id"],
        comment=f"Обмен валют: {operation.from_amount} {operation.from_currency} → {operation.to_amount} {operation.to_currency}",
        tag=[],
        merchant=None,
    )


def _create_deel_transfer_transaction(
    operation: DeelTransferOperation, current_timestamp: int
) -> Transaction:
    """Create transfer transaction from Deel to bank account"""
    abs_amount = abs(operation.amount)

    # Get configuration for bank account currency (where money is received)
    bank_currency_config = CURRENCY_CONFIG.get(operation.currency)
    if not bank_currency_config:
        bank_currency_config = CURRENCY_CONFIG["RSD"]

    # Get Deel configuration
    deel_account_id = DEEL_CONFIG.get("account_id")
    deel_currency = DEEL_CONFIG.get("currency", "USD")
    deel_currency_config = CURRENCY_CONFIG.get(deel_currency, CURRENCY_CONFIG["USD"])

    return Transaction(
        id=str(uuid.uuid4()),
        user=USER_ID,
        date=operation.date,
        income=abs_amount,
        outcome=abs_amount,
        changed=current_timestamp,
        incomeInstrument=bank_currency_config["instrument_id"],
        outcomeInstrument=deel_currency_config["instrument_id"],
        created=current_timestamp,
        deleted=False,
        viewed=False,
        incomeAccount=bank_currency_config["account_id"],
        outcomeAccount=deel_account_id,
        payee=operation.customer,
        comment=f"Transfer from Deel: {operation.customer}",
        tag=[],
        merchant=None,
    )


def _create_cash_withdrawal_transaction(
    operation: CashWithdrawalOperation, current_timestamp: int
) -> Transaction:
    """Create transfer transaction for cash withdrawal from bank to cash account"""
    abs_amount = abs(operation.amount)

    # Get configuration for the currency
    currency_config = CURRENCY_CONFIG.get(operation.currency)
    if not currency_config:
        currency_config = CURRENCY_CONFIG["RSD"]

    instrument_id = currency_config["instrument_id"]
    bank_account_id = currency_config["account_id"]
    cash_account_id = currency_config.get("cash_account_id", bank_account_id)

    return Transaction(
        id=str(uuid.uuid4()),
        user=USER_ID,
        date=operation.date,
        income=abs_amount,
        outcome=abs_amount,
        changed=current_timestamp,
        incomeInstrument=instrument_id,
        outcomeInstrument=instrument_id,
        created=current_timestamp,
        deleted=False,
        viewed=False,
        incomeAccount=cash_account_id,
        outcomeAccount=bank_account_id,
        payee=operation.customer,
        comment=f"Снятие наличных: {operation.customer}",
        tag=[],
        merchant=None,
    )
