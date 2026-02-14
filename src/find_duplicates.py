"""
Скрипт для поиска и удаления дубликатов транзакций в ZenMoney за последние 3 месяца.

Дубликатами считаются транзакции с одинаковыми:
- Датой
- Суммой (income или outcome)
- Валютой (instrument)
- Комментарием (начинающимся с "Импорт:", "Обмен валют:", "Transfer from Deel:", "Снятие наличных:")
"""

import sys
from datetime import datetime
from typing import Dict, List, Tuple

from services.zen_money.zen_money_api import (
    NewZenMoneyState,
    Transaction,
    ZenMoneyState,
    get_state,
    update_state,
)


def find_duplicate_transactions(
    zen_money_state: ZenMoneyState,
) -> Dict[Tuple, List[Transaction]]:
    """
    Находит дубликаты транзакций, сгруппированные по ключу.

    Returns:
        Словарь где ключ - это кортеж (date, amount, currency, comment),
        значение - список транзакций с этим ключом
    """
    # Получаем ID аккаунтов Raiffeisen
    raiffeizen_accounts = set()
    for account in zen_money_state.account:
        if account.title.startswith("Raiffeizen B"):
            raiffeizen_accounts.add(account.id)

    # Группируем транзакции по ключу
    transaction_groups: Dict[Tuple, List[Transaction]] = {}

    for transaction in zen_money_state.transaction:
        # Пропускаем уже удаленные
        if transaction.deleted:
            continue

        # Проверяем только транзакции с аккаунтами Raiffeisen
        if (
            transaction.incomeAccount not in raiffeizen_accounts
            and transaction.outcomeAccount not in raiffeizen_accounts
        ):
            continue

        # Проверяем только импортированные транзакции
        if not transaction.comment:
            continue

        # Фильтруем только наши импортированные транзакции
        if not (
            transaction.comment.startswith("Импорт: ")
            or transaction.comment.startswith("Обмен валют: ")
            or transaction.comment.startswith("Transfer from Deel: ")
            or transaction.comment.startswith("Снятие наличных: ")
        ):
            continue

        # Создаем ключ для группировки
        amount = transaction.outcome if transaction.outcome > 0 else transaction.income
        instrument = (
            transaction.outcomeInstrument
            if transaction.outcome > 0
            else transaction.incomeInstrument
        )

        key = (transaction.date, amount, instrument, transaction.comment)

        if key not in transaction_groups:
            transaction_groups[key] = []

        transaction_groups[key].append(transaction)

    # Оставляем только группы с дубликатами (больше одной транзакции)
    duplicates = {k: v for k, v in transaction_groups.items() if len(v) > 1}

    return duplicates


def select_transactions_to_delete(
    duplicates: Dict[Tuple, List[Transaction]],
) -> List[Transaction]:
    """
    Выбирает транзакции для удаления из групп дубликатов.

    Стратегия: оставляем самую старую (по created), остальные удаляем.
    """
    to_delete = []

    for key, transactions in duplicates.items():
        # Сортируем по времени создания (created)
        sorted_transactions = sorted(transactions, key=lambda t: t.created)

        # Оставляем первую (самую старую), остальные удаляем
        to_delete.extend(sorted_transactions[1:])

    return to_delete


def print_duplicate_report(
    duplicates: Dict[Tuple, List[Transaction]],
    zen_money_state: ZenMoneyState,
):
    """Выводит отчет о найденных дубликатах."""
    if not duplicates:
        print("✅ Дубликаты не найдены!")
        return

    print(f"\n🔍 Найдено {len(duplicates)} групп дубликатов:\n")

    # Создаем словарь для быстрого поиска валют
    instruments = {i.id: i for i in zen_money_state.instrument}

    for i, (key, transactions) in enumerate(duplicates.items(), 1):
        date, amount, instrument_id, comment = key
        instrument = instruments.get(instrument_id)
        currency = instrument.shortTitle if instrument else str(instrument_id)

        print(f"Группа {i}:")
        print(f"  📅 Дата: {date}")
        print(f"  💰 Сумма: {amount} {currency}")
        print(f"  📝 Комментарий: {comment}")
        print(f"  🔢 Количество дубликатов: {len(transactions)}")
        print("  Транзакции:")

        for j, transaction in enumerate(
            sorted(transactions, key=lambda t: t.created), 1
        ):
            created_date = datetime.fromtimestamp(transaction.created).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            mark = "  ✅ СОХРАНИТЬ" if j == 1 else "  ❌ УДАЛИТЬ"
            print(f"    {j}. ID: {transaction.id} | Создана: {created_date}{mark}")

        print()


def delete_duplicate_transactions(
    to_delete: List[Transaction], server_timestamp: int
) -> bool:
    """
    Удаляет дублирующиеся транзакции из ZenMoney.

    Returns:
        True если удаление прошло успешно
    """
    if not to_delete:
        print("Нет транзакций для удаления.")
        return False

    print(f"\n🗑️  Удаление {len(to_delete)} дублирующихся транзакций...")

    # Формируем список для удаления
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

    # Создаем новое состояние с удалениями
    current_timestamp = int(datetime.now().timestamp())
    new_state = NewZenMoneyState(
        currentClientTimestamp=current_timestamp,
        serverTimestamp=server_timestamp,
        deletion=deletion,
        transaction=[],  # Пустой массив транзакций, чтобы API не ругался
    )

    try:
        update_state(new_state)
        print("✅ Дубликаты успешно удалены!")
        return True
    except Exception as e:
        print(f"❌ Ошибка при удалении: {e}")
        return False


def main():
    """Основная функция скрипта."""
    print("=" * 70)
    print("🔍 ПОИСК И УДАЛЕНИЕ ДУБЛИКАТОВ ТРАНЗАКЦИЙ В ZENMONEY")
    print("=" * 70)

    # Проверяем флаги командной строки
    if "--help" in sys.argv or "-h" in sys.argv:
        print("\nИспользование:")
        print("  python src/find_duplicates.py [--auto-confirm|-y]")
        print("\nОпции:")
        print("  --auto-confirm, -y  Автоматически подтвердить удаление без запроса")
        print("  --help, -h          Показать это сообщение")
        print()
        return

    # Получаем данные за последние 90 дней (3 месяца)
    DAYS = 90
    print(f"\n📥 Загружаем данные за последние {DAYS} дней...")

    zen_money_state = get_state(DAYS)

    total_transactions = len([t for t in zen_money_state.transaction if not t.deleted])
    print(f"📊 Всего активных транзакций: {total_transactions}")

    # Находим дубликаты
    print("\n🔎 Анализируем транзакции...")
    duplicates = find_duplicate_transactions(zen_money_state)

    # Выводим отчет
    print_duplicate_report(duplicates, zen_money_state)

    if not duplicates:
        return

    # Выбираем транзакции для удаления
    to_delete = select_transactions_to_delete(duplicates)

    total_duplicates = sum(len(transactions) for transactions in duplicates.values())
    print("📋 Итого:")
    print(f"  - Всего транзакций в дубликатах: {total_duplicates}")
    print(f"  - Будет сохранено: {len(duplicates)} (по 1 из каждой группы)")
    print(f"  - Будет удалено: {len(to_delete)}")

    # Запрашиваем подтверждение
    auto_confirm = "--auto-confirm" in sys.argv or "-y" in sys.argv

    if auto_confirm:
        print("\n⚠️  ВНИМАНИЕ! Используется автоматическое подтверждение!")
        print("Дубликаты будут удалены автоматически...")
        response = "да"
    else:
        print("\n⚠️  ВНИМАНИЕ! Это действие нельзя отменить!")
        try:
            response = input("Удалить дубликаты? (да/нет): ").strip().lower()
        except EOFError:
            print(
                "\nНе удалось получить ввод. Используйте флаг --auto-confirm для автоматического подтверждения."
            )
            response = "нет"

    if response in ["да", "yes", "y", "д"]:
        success = delete_duplicate_transactions(
            to_delete, zen_money_state.serverTimestamp
        )
        if success:
            print(f"\n✨ Готово! Удалено {len(to_delete)} дублирующихся транзакций.")
    else:
        print("\n❌ Операция отменена пользователем.")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
