import base64
import email as email_lib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from config import GOOGLE_CREDENTIALS_FILE, GOOGLE_TOKEN_FILE, GOOGLE_SCOPES


def _get_service():
    creds = None
    if GOOGLE_TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(GOOGLE_TOKEN_FILE), GOOGLE_SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not GOOGLE_CREDENTIALS_FILE.exists():
                raise FileNotFoundError(
                    "credentials.json not found. Download it from Google Cloud Console "
                    "and place it in the mada/ folder."
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                str(GOOGLE_CREDENTIALS_FILE), GOOGLE_SCOPES
            )
            creds = flow.run_local_server(port=0)
        with open(GOOGLE_TOKEN_FILE, "w") as f:
            f.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def _decode_body(payload) -> str:
    """Recursively extract plain text from a message payload."""
    if payload.get("mimeType") == "text/plain":
        data = payload.get("body", {}).get("data", "")
        if data:
            return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
    if payload.get("mimeType") == "text/html":
        data = payload.get("body", {}).get("data", "")
        if data:
            import re
            html = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
            return re.sub(r"<[^>]+>", "", html)
    for part in payload.get("parts", []):
        result = _decode_body(part)
        if result:
            return result
    return ""


def _parse_message(msg: dict) -> dict:
    headers = {h["name"]: h["value"] for h in msg["payload"].get("headers", [])}
    return {
        "id": msg["id"],
        "thread_id": msg.get("threadId", ""),
        "from": headers.get("From", ""),
        "to": headers.get("To", ""),
        "subject": headers.get("Subject", "(no subject)"),
        "date": headers.get("Date", ""),
        "body": _decode_body(msg["payload"])[:3000],
        "snippet": msg.get("snippet", ""),
    }


def read_emails(max_results: int = 10, query: str = "") -> list[dict]:
    """Fetch emails from Gmail inbox."""
    service = _get_service()
    q = f"in:inbox {query}".strip()
    results = service.users().messages().list(
        userId="me", q=q, maxResults=max_results
    ).execute()
    messages = results.get("messages", [])
    emails = []
    for m in messages:
        full = service.users().messages().get(
            userId="me", id=m["id"], format="full"
        ).execute()
        emails.append(_parse_message(full))
    return emails


def send_email(to: str, subject: str, body: str, cc: str = "") -> str:
    """Send an email via Gmail."""
    service = _get_service()
    msg = MIMEMultipart()
    msg["To"] = to
    msg["Subject"] = subject
    if cc:
        msg["Cc"] = cc
    msg.attach(MIMEText(body, "plain"))
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    service.users().messages().send(userId="me", body={"raw": raw}).execute()
    return f"Email sent to {to} with subject: '{subject}'"


def reply_to_email(message_id: str, body: str, reply_all: bool = False) -> str:
    """Reply to an existing email thread."""
    service = _get_service()
    original = service.users().messages().get(
        userId="me", id=message_id, format="full"
    ).execute()
    parsed = _parse_message(original)

    msg = MIMEMultipart()
    msg["To"] = parsed["from"]
    msg["Subject"] = f"Re: {parsed['subject']}"
    msg["In-Reply-To"] = message_id
    msg["References"] = message_id
    if reply_all and parsed["to"]:
        msg["Cc"] = parsed["to"]
    msg.attach(MIMEText(body, "plain"))

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    service.users().messages().send(
        userId="me",
        body={"raw": raw, "threadId": parsed["thread_id"]}
    ).execute()
    return f"Reply sent to {parsed['from']} on thread: '{parsed['subject']}'"


def get_email_by_id(message_id: str) -> dict:
    service = _get_service()
    msg = service.users().messages().get(
        userId="me", id=message_id, format="full"
    ).execute()
    return _parse_message(msg)
