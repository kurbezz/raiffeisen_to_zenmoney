"""
Auto-cleanup module for removing SMS and import duplicates from ZenMoney.

This module automatically detects and removes duplicate transactions that occur when:
1. SMS operations are added twice (with and without "Stanje: ***" suffix)
2. Import operations are duplicated with the same date, amount, and currency

Runs automatically during the sync process.
"""

from datetime import datetime

from .zen_money_api import (
    NewZenMoneyState,
    ZenMoneyState,
    get_state,
    update_state,
)


def _normalize_payee(payee: str) -> str:
    """Normalize payee name for comparison."""
    if not payee:
        return ""

    # Remove "Stanje: ***" suffix
    payee = payee.replace("Stanje: ***", "").replace("Stanje:", "").strip()

    # Convert to lowercase for comparison
    return payee.lower()


def find_duplicate_transactions(
    zen_money_state: ZenMoneyState,
) -> dict:
    """
    Find duplicate transactions (SMS and import duplicates).

    Returns:
        Dictionary with duplicate groups:
        {
            'sms': {key: [transactions]},  # SMS duplicates
            'import': {key: [transactions]},  # Import duplicates
            'cross_type': [transactions_to_delete]  # SMS+Import cross-type pairs
        }
    """
    # Get Raiffeisen accounts
    raiffeisen_accounts = {
        a.id for a in zen_money_state.account if a.title.startswith("Raiffeizen B")
    }

    instruments = {i.id: i for i in zen_money_state.instrument}

    sms_groups = {}
    import_groups = {}
    cross_type_duplicates = []

    for transaction in zen_money_state.transaction:
        if transaction.deleted:
            continue

        if (
            transaction.incomeAccount not in raiffeisen_accounts
            and transaction.outcomeAccount not in raiffeisen_accounts
        ):
            continue

        # Determine amount and currency
        amount = transaction.outcome if transaction.outcome > 0 else transaction.income
        currency_id = (
            transaction.outcomeInstrument
            if transaction.outcome > 0
            else transaction.incomeInstrument
        )
        currency = instruments.get(currency_id)
        currency_str = currency.shortTitle if currency else str(currency_id)

        is_import = transaction.comment and (
            transaction.comment.startswith("Импорт:")
            or transaction.comment.startswith("Обмен валют:")
            or transaction.comment.startswith("Transfer from Deel:")
            or transaction.comment.startswith("Снятие наличных:")
        )

        if is_import:
            # Import duplicates: same date, amount, currency, comment
            key = (
                transaction.date,
                abs(amount),
                currency_str,
                transaction.comment,
            )

            if key not in import_groups:
                import_groups[key] = []

            import_groups[key].append(transaction)
        else:
            # SMS duplicates: same date, amount, currency, normalized payee
            normalized_payee = (
                _normalize_payee(transaction.payee) if transaction.payee else ""
            )
            key = (transaction.date, abs(amount), currency_str, normalized_payee)

            if key not in sms_groups:
                sms_groups[key] = []

            sms_groups[key].append(transaction)

    # Find cross-type duplicates (SMS + Import with same date, amount, currency)
    for sms_transactions in sms_groups.values():
        for sms_tx in sms_transactions:
            sms_amount = sms_tx.outcome if sms_tx.outcome > 0 else sms_tx.income
            sms_currency_id = (
                sms_tx.outcomeInstrument
                if sms_tx.outcome > 0
                else sms_tx.incomeInstrument
            )
            sms_currency = instruments.get(sms_currency_id)
            sms_currency_str = (
                sms_currency.shortTitle if sms_currency else str(sms_currency_id)
            )

            # Look for import transactions with same date, amount, currency
            for import_transactions in import_groups.values():
                for import_tx in import_transactions:
                    # Determine amount and currency for import transaction
                    import_amount = (
                        import_tx.outcome if import_tx.outcome > 0 else import_tx.income
                    )
                    import_currency_id = (
                        import_tx.outcomeInstrument
                        if import_tx.outcome > 0
                        else import_tx.incomeInstrument
                    )
                    import_currency = instruments.get(import_currency_id)
                    import_currency_str = (
                        import_currency.shortTitle
                        if import_currency
                        else str(import_currency_id)
                    )
                    
                    # Check if this could be the same transaction
                    if (
                        sms_tx.date == import_tx.date
                        and abs(sms_amount) == abs(import_amount)
                        and sms_currency_str == import_currency_str
                    ):
                        # This is a cross-type duplicate
                        # Keep the import version (more detailed), delete SMS version
                        if sms_tx not in cross_type_duplicates:
                            cross_type_duplicates.append(sms_tx)

    # Filter to keep only actual duplicates
    sms_duplicates = {k: v for k, v in sms_groups.items() if len(v) > 1}
    import_duplicates = {k: v for k, v in import_groups.items() if len(v) > 1}

    return {
        "sms": sms_duplicates,
        "import": import_duplicates,
        "cross_type": cross_type_duplicates,
    }


def select_transactions_to_delete(duplicates: dict) -> list:
    """
    Select transactions to delete from duplicate groups.

    Strategy: 
    - Keep the newest (by created time) for SMS duplicates
    - Keep the newest (by created time) for import duplicates
    - Delete SMS version for cross-type duplicates (keep import)

    Returns:
        List of Transaction objects to delete
    """
    to_delete = []

    # Process SMS duplicates
    for _key, transactions in duplicates["sms"].items():
        sorted_txs = sorted(transactions, key=lambda t: t.created)
        # Delete all but the newest
        to_delete.extend(sorted_txs[:-1])

    # Process import duplicates
    for _key, transactions in duplicates["import"].items():
        sorted_txs = sorted(transactions, key=lambda t: t.created)
        # Delete all but the newest
        to_delete.extend(sorted_txs[:-1])

    # Process cross-type duplicates (delete SMS, keep import)
    to_delete.extend(duplicates["cross_type"])

    return to_delete


def auto_cleanup_duplicates(days: int = 90) -> bool:
    """
    Automatically detect and remove duplicate transactions.

    Args:
        days: Number of days to check for duplicates

    Returns:
        True if cleanup was performed, False if no duplicates found
    """
    # Get current state
    zen_money_state = get_state(days)

    # Find duplicates
    duplicates = find_duplicate_transactions(zen_money_state)

    total_duplicates = (
        len(duplicates["sms"])
        + len(duplicates["import"])
        + len(duplicates["cross_type"])
    )

    if total_duplicates == 0:
        return False

    # Print summary of what was found
    if duplicates["cross_type"]:
        print(
            f"⚠️ Найдено {len(duplicates['cross_type'])} кросс-типных дубликатов (SMS + Import)"
        )
        for tx in duplicates["cross_type"]:
            print(
                f"   - Дата: {tx.date}, Сумма: {tx.income if tx.income > 0 else tx.outcome}, Payee: {tx.payee}"
            )

    # Select which transactions to delete
    to_delete = select_transactions_to_delete(duplicates)

    if not to_delete:
        return False

    # Prepare deletion list
    deletion = []
    for transaction in to_delete:
        deletion.append(
            {
                "id": transaction.id,
                "object": "transaction",
                "stamp": transaction.changed,
                "user": transaction.user,
            }
        )

    # Create new state with deletions
    current_timestamp = int(datetime.now().timestamp())
    new_state = NewZenMoneyState(
        currentClientTimestamp=current_timestamp,
        serverTimestamp=zen_money_state.serverTimestamp,
        deletion=deletion,
        transaction=[],
    )

    try:
        update_state(new_state)
        return True
    except Exception as e:
        # Log error but don't fail the sync
        print(f"Warning: Auto-cleanup encountered an error: {e}")
        return False
