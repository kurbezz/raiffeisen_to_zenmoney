from datetime import datetime

from services.operations.operations import (
    CashWithdrawalOperation,
    DeelTransferOperation,
    SimpleOperation,
    TransitionOperation,
)
from services.zen_money.zen_money_api import ZenMoneyState


def _convert_date_to_iso(date_str: str) -> str:
    try:
        if "." in date_str:
            dt = datetime.strptime(date_str, "%d.%m.%Y")
            return dt.strftime("%Y-%m-%d")
        return date_str
    except ValueError:
        return date_str


def filter_operations(
    operations: list[
        SimpleOperation
        | TransitionOperation
        | DeelTransferOperation
        | CashWithdrawalOperation
    ],
    zen_money_state: ZenMoneyState,
) -> list[
    SimpleOperation
    | TransitionOperation
    | DeelTransferOperation
    | CashWithdrawalOperation
]:
    raiffeizen_accounts = {}
    for account in zen_money_state.account:
        if account.title.startswith("Raiffeizen B"):
            instrument = next(
                (i for i in zen_money_state.instrument if i.id == account.instrument),
                None,
            )
            if instrument:
                raiffeizen_accounts[instrument.shortTitle] = account.id

    existing_transactions = set()
    existing_import_operations = set()

    for transaction in zen_money_state.transaction:
        if transaction.deleted:
            continue

        if (
            transaction.incomeAccount in raiffeizen_accounts.values()
            or transaction.outcomeAccount in raiffeizen_accounts.values()
        ):
            instrument = next(
                (
                    i
                    for i in zen_money_state.instrument
                    if i.id == transaction.incomeInstrument
                    or i.id == transaction.outcomeInstrument
                ),
                None,
            )

            if instrument:
                if transaction.outcome > 0:
                    key = (transaction.date, transaction.outcome, instrument.shortTitle)
                elif transaction.income > 0:
                    key = (transaction.date, transaction.income, instrument.shortTitle)
                else:
                    continue

                existing_transactions.add(key)

                if transaction.comment and (
                    transaction.comment.startswith("Импорт: ")
                    or transaction.comment.startswith("Обмен валют: ")
                    or transaction.comment.startswith("Transfer from Deel: ")
                    or transaction.comment.startswith("Снятие наличных: ")
                ):
                    if transaction.comment.startswith("Обмен валют: "):
                        if transaction.outcome > 0:
                            outcome_instrument = next(
                                (
                                    i
                                    for i in zen_money_state.instrument
                                    if i.id == transaction.outcomeInstrument
                                ),
                                None,
                            )
                            if outcome_instrument:
                                outcome_key = (
                                    transaction.date,
                                    transaction.outcome,
                                    outcome_instrument.shortTitle,
                                    transaction.comment,
                                )
                                existing_import_operations.add(outcome_key)

                        if transaction.income > 0:
                            income_instrument = next(
                                (
                                    i
                                    for i in zen_money_state.instrument
                                    if i.id == transaction.incomeInstrument
                                ),
                                None,
                            )
                            if income_instrument:
                                income_key = (
                                    transaction.date,
                                    transaction.income,
                                    income_instrument.shortTitle,
                                    transaction.comment,
                                )
                                existing_import_operations.add(income_key)
                    else:
                        amount = (
                            transaction.outcome
                            if transaction.outcome > 0
                            else transaction.income
                        )
                        import_key = (
                            transaction.date,
                            amount,
                            instrument.shortTitle,
                            transaction.comment,
                        )
                        existing_import_operations.add(import_key)

    filtered_operations = []

    for operation in operations:
        if isinstance(operation, SimpleOperation):
            if operation.currency not in raiffeizen_accounts:
                continue

            amount = abs(operation.amount)
            iso_date = _convert_date_to_iso(operation.date)
            key = (iso_date, amount, operation.currency)

            expected_comment = f"Импорт: {operation.customer} ({operation.currency})"

            import_key = (iso_date, amount, operation.currency, expected_comment)

            if (
                key not in existing_transactions
                and import_key not in existing_import_operations
            ):
                filtered_operations.append(operation)

        elif isinstance(operation, TransitionOperation):
            expected_comment = f"Обмен валют: {operation.from_amount} {operation.from_currency} → {operation.to_amount} {operation.to_currency}"

            iso_date = _convert_date_to_iso(operation.date)
            from_import_key = (
                iso_date,
                abs(operation.from_amount),
                operation.from_currency,
                expected_comment,
            )
            to_import_key = (
                iso_date,
                abs(operation.to_amount),
                operation.to_currency,
                expected_comment,
            )

            if (
                from_import_key in existing_import_operations
                and to_import_key in existing_import_operations
            ):
                continue

            from_exists = False
            to_exists = False

            if operation.from_currency in raiffeizen_accounts:
                from_key = (
                    iso_date,
                    abs(operation.from_amount),
                    operation.from_currency,
                )
                from_exists = from_key in existing_transactions

            if operation.to_currency in raiffeizen_accounts:
                to_key = (
                    iso_date,
                    abs(operation.to_amount),
                    operation.to_currency,
                )
                to_exists = to_key in existing_transactions

            if from_exists and to_exists:
                continue

            filtered_operations.append(operation)

        elif isinstance(operation, DeelTransferOperation):
            # Deel transfers are always incoming
            amount = abs(operation.amount)
            iso_date = _convert_date_to_iso(operation.date)
            expected_comment = f"Transfer from Deel: {operation.customer}"

            import_key = (iso_date, amount, operation.currency, expected_comment)

            # Check that this Deel transfer hasn't been imported yet
            if import_key not in existing_import_operations:
                filtered_operations.append(operation)

        elif isinstance(operation, CashWithdrawalOperation):
            # Cash withdrawals are always outgoing (negative amount)
            amount = abs(operation.amount)
            iso_date = _convert_date_to_iso(operation.date)
            expected_comment = f"Снятие наличных: {operation.customer}"

            import_key = (iso_date, amount, operation.currency, expected_comment)

            # Check that this cash withdrawal hasn't been imported yet
            if import_key not in existing_import_operations:
                filtered_operations.append(operation)

    return filtered_operations
