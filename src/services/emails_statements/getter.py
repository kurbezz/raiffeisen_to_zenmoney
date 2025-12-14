import base64
from datetime import date, timedelta

import mailparser
from imapclient import IMAPClient

from envs import EMAIL_ALLOWED_SUBJECTS, EMAIL_PASSWORD, EMAIL_USERNAME

from .statement import Statement


def get_statements(days: int = 1) -> list[Statement]:
    server = IMAPClient("imap.gmail.com", use_uid=True, ssl=True)
    server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
    server.select_folder("INBOX")

    since_date = (date.today() - timedelta(days=days)).strftime("%d-%b-%Y")

    messages = server.search(
        f'(FROM "RaiffeisenOnline@raiffeisenbank.rs" SINCE {since_date})'
    )

    statements = []

    for _uid, message_data in server.fetch(messages, "RFC822").items():
        mail = mailparser.parse_from_bytes(message_data[b"RFC822"])

        if mail.subject not in EMAIL_ALLOWED_SUBJECTS:
            continue

        for attachment in mail.attachments:
            if not attachment.get("filename", "").lower().endswith(".xml"):
                continue

            payload = attachment.get("payload")
            if not payload:
                continue

            statements.append(Statement.from_xml(base64.b64decode(payload).decode()))

    return statements
