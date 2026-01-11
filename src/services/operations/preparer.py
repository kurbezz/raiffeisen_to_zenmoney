from services.emails_statements.statement import RawOperation, Statement
from services.operations.operations import (
    CashWithdrawalOperation,
    DeelTransferOperation,
    SimpleOperation,
    TransitionOperation,
)


def prepare_operations(
    statements: list[Statement],
    deel_config: dict | None = None,
    cash_withdrawal_config: dict | None = None,
) -> list[
    SimpleOperation
    | TransitionOperation
    | DeelTransferOperation
    | CashWithdrawalOperation
]:
    operations = []
    all_raw_operations = []

    # Дедупликация сырых операций
    seen_operations = set()
    duplicates_count = 0

    for statement in statements:
        for raw_operation in statement.operations:
            # Создаем уникальный ключ для операции
            operation_key = (
                raw_operation.data,
                raw_operation.amount,
                raw_operation.currency,
                raw_operation.customer,
                raw_operation.reference,
                raw_operation.description,
            )

            # Пропускаем дубликаты
            if operation_key in seen_operations:
                duplicates_count += 1
                print(
                    f"ДУБЛИКАТ: {raw_operation.data} - {raw_operation.amount} {raw_operation.currency} - {raw_operation.customer}"
                )
                continue

            seen_operations.add(operation_key)
            all_raw_operations.append((raw_operation, statement.account_number))

    if duplicates_count > 0:
        print(f"\nОбнаружено и пропущено дубликатов: {duplicates_count}")

    processed_operations = set()

    for i, (op1, acc1) in enumerate(all_raw_operations):
        if id(op1) in processed_operations:
            continue

        for j, (op2, acc2) in enumerate(all_raw_operations[i + 1 :], i + 1):
            if id(op2) in processed_operations:
                continue

            if _are_operations_linked(op1, op2):
                if (
                    op1.currency != op2.currency
                    and (
                        (op1.amount < 0 and op2.amount > 0)
                        or (op1.amount > 0 and op2.amount < 0)
                    )
                    and (_is_currency_exchange(op1) or _is_currency_exchange(op2))
                ):
                    if op1.amount < 0:
                        from_op, to_op = op1, op2
                    else:
                        from_op, to_op = op2, op1

                    transition_op = TransitionOperation.from_raw(from_op, to_op)
                    operations.append(transition_op)

                    processed_operations.add(id(op1))
                    processed_operations.add(id(op2))
                    break

    for raw_operation, account_number in all_raw_operations:
        if id(raw_operation) not in processed_operations:
            # Проверяем, является ли это переводом от Deel
            if deel_config and _is_deel_transfer(raw_operation, deel_config):
                deel_op = DeelTransferOperation.from_raw(raw_operation)
                operations.append(deel_op)
            # Проверяем, является ли это снятием наличных
            elif cash_withdrawal_config and _is_cash_withdrawal(
                raw_operation, cash_withdrawal_config
            ):
                cash_withdrawal_op = CashWithdrawalOperation.from_raw(raw_operation)
                operations.append(cash_withdrawal_op)
            else:
                simple_op = SimpleOperation.from_raw(raw_operation)
                operations.append(simple_op)

    return operations


def _are_operations_linked(op1: RawOperation, op2: RawOperation) -> bool:
    """Check if two operations are linked (by references or descriptions)"""

    if op1.reference and op2.reference and op1.reference == op2.reference:
        return True

    if op1.reference and op1.reference in op2.description:
        return True

    if op2.reference and op2.reference in op1.description:
        return True

    return False


def _is_currency_exchange(operation: RawOperation) -> bool:
    """Check if operation is a currency exchange"""
    description_lower = operation.description.lower()
    customer_lower = operation.customer.lower()

    # Exclude cash withdrawals - they have card numbers in description
    if "******" in operation.description:
        return False

    exchange_keywords = [
        "otkup",
        "kupoprodaja deviza",
        "dinarska protivvrednost",
        "po kursu",
        "protivvrednost",
    ]

    return (
        any(keyword in description_lower for keyword in exchange_keywords)
        or "raiffeisen banka" in customer_lower
    )


def _is_deel_transfer(operation: RawOperation, deel_config: dict) -> bool:
    """Check if operation is a transfer from Deel"""
    if not deel_config.get("enabled", False):
        return False

    # Check only incoming payments
    if operation.amount <= 0:
        return False

    # Get keywords for search
    keywords = deel_config.get("keywords", [])
    if not keywords:
        return False

    # Check for keywords in customer or description
    customer_lower = operation.customer.lower()
    description_lower = operation.description.lower()

    for keyword in keywords:
        keyword_lower = keyword.lower()
        if keyword_lower in customer_lower or keyword_lower in description_lower:
            return True

    return False


def _is_cash_withdrawal(operation: RawOperation, cash_withdrawal_config: dict) -> bool:
    """Check if operation is a cash withdrawal from ATM or bank branch"""
    if not cash_withdrawal_config.get("enabled", False):
        return False

    # Check only outgoing payments (withdrawals)
    if operation.amount >= 0:
        return False

    # Get keywords for search
    keywords = cash_withdrawal_config.get("keywords", [])
    if not keywords:
        return False

    # Check for keywords in customer or description
    customer_lower = operation.customer.lower()
    description_lower = operation.description.lower()

    for keyword in keywords:
        keyword_lower = keyword.lower()
        if keyword_lower in customer_lower or keyword_lower in description_lower:
            return True

    return False
