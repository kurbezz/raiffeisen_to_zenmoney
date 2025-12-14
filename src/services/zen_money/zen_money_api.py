from datetime import datetime, timedelta
from typing import List, Optional

import requests
from pydantic import BaseModel

from envs import ZEN_MONEY_API_KEY


class Instrument(BaseModel):
    id: int
    title: str
    shortTitle: str
    symbol: str
    rate: float
    changed: int


class Account(BaseModel):
    id: str
    user: int
    instrument: int
    type: str
    role: Optional[str] = None
    private: bool
    savings: bool
    title: str
    inBalance: bool
    creditLimit: float
    startBalance: float
    balance: float
    company: Optional[int] = None
    archive: bool
    enableCorrection: bool
    balanceCorrectionType: str
    startDate: Optional[str] = None
    capitalization: Optional[str] = None
    percent: Optional[str] = None
    changed: int
    syncID: Optional[List[str]] = None
    enableSMS: bool
    endDateOffset: Optional[str] = None
    endDateOffsetInterval: Optional[str] = None
    payoffStep: Optional[str] = None
    payoffInterval: Optional[str] = None


class Budget(BaseModel):
    user: int
    changed: int
    date: str
    tag: Optional[str] = None
    income: float
    outcome: float
    incomeLock: bool
    outcomeLock: bool
    isIncomeForecast: bool
    isOutcomeForecast: bool


class Reminder(BaseModel):
    id: str
    user: int
    income: float
    outcome: float
    changed: int
    incomeInstrument: int
    outcomeInstrument: int
    step: int
    points: List[int]
    tag: Optional[List[str]] = None
    startDate: str
    endDate: Optional[str] = None
    notify: bool
    interval: Optional[str] = None
    incomeAccount: str
    outcomeAccount: str
    comment: Optional[str] = None
    payee: Optional[str] = None
    merchant: Optional[str] = None


class ReminderMarker(BaseModel):
    id: str
    user: int
    date: str
    income: float
    outcome: float
    changed: int
    incomeInstrument: int
    outcomeInstrument: int
    state: str
    isForecast: bool
    reminder: str
    incomeAccount: str
    outcomeAccount: str
    comment: Optional[str] = None
    payee: Optional[str] = None
    merchant: Optional[str] = None
    notify: bool
    tag: Optional[List[str]] = None


class Transaction(BaseModel):
    id: str
    user: int
    date: str
    income: float
    outcome: float
    changed: int
    incomeInstrument: int
    outcomeInstrument: int
    created: int
    originalPayee: Optional[str] = None
    deleted: bool
    viewed: bool
    hold: Optional[bool] = None
    qrCode: Optional[str] = None
    source: Optional[str] = None
    incomeAccount: str
    outcomeAccount: Optional[str] = None
    tag: Optional[List[str]] = None
    comment: Optional[str] = None
    payee: Optional[str] = None
    opIncome: Optional[float] = None
    opOutcome: Optional[float] = None
    opIncomeInstrument: Optional[int] = None
    opOutcomeInstrument: Optional[int] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    merchant: Optional[str] = None
    incomeBankID: Optional[str] = None
    outcomeBankID: Optional[str] = None
    reminderMarker: Optional[str] = None


class ZenMoneyState(BaseModel):
    serverTimestamp: int
    instrument: List[Instrument]
    account: List[Account]
    budget: Optional[List[Budget]] = None
    reminder: Optional[List[Reminder]] = None
    reminderMarker: List[ReminderMarker]
    transaction: List[Transaction]


class NewZenMoneyState(BaseModel):
    currentClientTimestamp: int
    serverTimestamp: int

    instrument: Optional[List[Instrument]] = None
    account: Optional[List[Account]] = None
    budget: Optional[List[Budget]] = None
    reminder: Optional[List[Reminder]] = None
    reminderMarker: Optional[List[ReminderMarker]] = None
    transaction: Optional[List[Transaction]] = None

    deletion: Optional[List[dict]] = None


def get_state(days: int) -> ZenMoneyState:
    currentTimestamp = int(datetime.today().timestamp())

    serverTimestamp = int(
        (datetime.today() - timedelta(days=days))
        .replace(hour=0, minute=0, second=0, microsecond=0)
        .timestamp()
    )

    r = requests.post(
        "https://api.zenmoney.ru/v8/diff/",
        headers={"Authorization": f"Bearer {ZEN_MONEY_API_KEY}"},
        json={
            "currentClientTimestamp": currentTimestamp,
            "serverTimestamp": serverTimestamp,
        },
    )

    if r.status_code != 200:
        raise Exception(f"Error: {r.status_code} {r.text}")

    return ZenMoneyState.model_validate(r.json())


def update_state(state: NewZenMoneyState):
    data = state.model_dump()

    entity_fields = [
        "instrument",
        "account",
        "budget",
        "reminder",
        "reminderMarker",
        "deletion",
    ]
    for field in entity_fields:
        if field in data and data[field] is None:
            del data[field]

    r = requests.post(
        "https://api.zenmoney.ru/v8/diff/",
        headers={"Authorization": f"Bearer {ZEN_MONEY_API_KEY}"},
        json=data,
    )

    if r.status_code != 200:
        raise Exception(f"Error updating state: {r.status_code} {r.text}")

    return r.json()
