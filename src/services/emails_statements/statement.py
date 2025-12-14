from dataclasses import dataclass
from typing import Self

from lxml import etree  # pyright: ignore


@dataclass
class RawOperation:
    customer: str
    amount: float
    currency: str
    reference: str
    data: str
    description: str


@dataclass
class Statement:
    account_number: str
    operations: list[RawOperation]

    @classmethod
    def from_xml(cls, xml_content: str) -> Self:
        tree = etree.fromstring(xml_content)

        account_info = tree.find("Zaglavlje")
        account_number = account_info.attrib.get("Partija")
        currency = account_info.attrib.get("OznakaValute", "RSD")

        operations = []

        operations_info = tree.findall("Stavke")
        for operation in operations_info:
            if operation.attrib.get("Duguje", "0") != "0":
                amount = -float(operation.attrib.get("Duguje"))
            elif operation.attrib.get("Potrazuje", "0") != "0":
                amount = float(operation.attrib.get("Potrazuje"))
            else:
                continue

            operations.append(
                RawOperation(
                    customer=operation.attrib.get("NalogKorisnik", ""),
                    amount=amount,
                    currency=currency,
                    data=operation.attrib.get("DatumValute", ""),
                    reference=operation.attrib.get("Referenca", ""),
                    description=operation.attrib.get("Opis", ""),
                )
            )

        return cls(account_number=account_number, operations=operations)
