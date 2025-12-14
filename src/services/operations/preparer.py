from services.emails_statements.statement import RawOperation, Statement
from services.operations.operations import SimpleOperation, TransitionOperation


def prepare_operations(
    statements: list[Statement],
) -> list[SimpleOperation | TransitionOperation]:
    operations = []
    all_raw_operations = []

    for statement in statements:
        for raw_operation in statement.operations:
            all_raw_operations.append((raw_operation, statement.account_number))

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
            simple_op = SimpleOperation.from_raw(raw_operation)
            operations.append(simple_op)

    return operations


def _are_operations_linked(op1: RawOperation, op2: RawOperation) -> bool:
    """Проверяет, связаны ли две операции (по референсам или описаниям)"""

    if op1.reference and op2.reference and op1.reference == op2.reference:
        return True

    if op1.reference and op1.reference in op2.description:
        return True

    if op2.reference and op2.reference in op1.description:
        return True

    return False


def _is_currency_exchange(operation: RawOperation) -> bool:
    """Проверяет, является ли операция обменом валют"""
    description_lower = operation.description.lower()
    customer_lower = operation.customer.lower()

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
