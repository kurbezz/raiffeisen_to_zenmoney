from envs import CASH_WITHDRAWAL_CONFIG, DEEL_CONFIG
from services.emails_statements.getter import get_statements
from services.operations.filter import filter_operations
from services.operations.operations import (
    CashWithdrawalOperation,
    DeelTransferOperation,
    SimpleOperation,
    TransitionOperation,
)
from services.operations.preparer import prepare_operations
from services.zen_money.preparer import prepare_new_state
from services.zen_money.zen_money_api import get_state, update_state


def main():
    DAYS = 7

    statements = get_statements(DAYS)
    print(f"Получено выписок: {len(statements)}")

    # Подсчитываем общее количество операций из выписок
    total_raw_operations = sum(len(stmt.operations) for stmt in statements)
    print(f"Всего операций в выписках: {total_raw_operations}")

    zen_money_state = get_state(DAYS)

    operations = prepare_operations(
        statements,
        deel_config=DEEL_CONFIG,
        cash_withdrawal_config=CASH_WITHDRAWAL_CONFIG,
    )
    print(f"После дедупликации и обработки: {len(operations)} операций")

    filtered_operations = filter_operations(operations, zen_money_state)
    print(
        f"После фильтрации существующих в ZenMoney: {len(filtered_operations)} операций"
    )

    if filtered_operations:
        print(f"Найдено {len(filtered_operations)} новых операций для импорта")

        print("\nНовые операции:")
        for i, operation in enumerate(filtered_operations, 1):
            if isinstance(operation, SimpleOperation):
                print(
                    f"{i}. {operation.date} - {operation.amount} {operation.currency} - {operation.customer}"
                )
            elif isinstance(operation, TransitionOperation):
                print(
                    f"{i}. {operation.date} - {operation.from_amount} {operation.from_currency} → {operation.to_amount} {operation.to_currency}"
                )
            elif isinstance(operation, DeelTransferOperation):
                print(
                    f"{i}. [DEEL] {operation.date} - {operation.amount} {operation.currency} - {operation.customer}"
                )
            elif isinstance(operation, CashWithdrawalOperation):
                print(
                    f"{i}. [CASH] {operation.date} - {operation.amount} {operation.currency} - {operation.customer}"
                )

        new_zen_money_state = prepare_new_state(filtered_operations)
        update_state(new_zen_money_state)
        print("\nОперации успешно импортированы!")
    else:
        print("Новых операций для импорта не найдено")


if __name__ == "__main__":
    main()
