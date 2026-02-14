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
            'import': {key: [transactions]}  # Import duplicates
        }
    """
    # Get Raiffeisen accounts
    raiffeisen_accounts = {
        a.id for a in zen_money_state.account if a.title.startswith("Raiffeizen B")
    }

    instruments = {i.id: i for i in zen_money_state.instrument}

    sms_groups = {}
    import_groups = {}

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

    # Filter to keep only actual duplicates
    sms_duplicates = {k: v for k, v in sms_groups.items() if len(v) > 1}
    import_duplicates = {k: v for k, v in import_groups.items() if len(v) > 1}

    return {
        "sms": sms_duplicates,
        "import": import_duplicates,
    }


def select_transactions_to_delete(duplicates: dict) -> list:
    """
    Select transactions to delete from duplicate groups.

    Strategy: Keep the newest (by created time), delete older ones.

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

    total_duplicates = len(duplicates["sms"]) + len(duplicates["import"])

    if total_duplicates == 0:
        return False

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
