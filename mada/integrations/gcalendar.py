from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from config import GOOGLE_CREDENTIALS_FILE, GOOGLE_TOKEN_FILE, GOOGLE_SCOPES, TIMEZONE


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
    return build("calendar", "v3", credentials=creds)


def _tz():
    try:
        return ZoneInfo(TIMEZONE)
    except Exception:
        return ZoneInfo("UTC")


def get_events(days_ahead: int = 7, max_results: int = 20) -> list[dict]:
    service = _get_service()
    tz = _tz()
    now = datetime.now(tz)
    end = now + timedelta(days=days_ahead)

    result = service.events().list(
        calendarId="primary",
        timeMin=now.isoformat(),
        timeMax=end.isoformat(),
        maxResults=max_results,
        singleEvents=True,
        orderBy="startTime",
    ).execute()

    events = []
    for e in result.get("items", []):
        start = e["start"].get("dateTime", e["start"].get("date", ""))
        end_t = e["end"].get("dateTime", e["end"].get("date", ""))
        events.append({
            "id": e["id"],
            "title": e.get("summary", "(no title)"),
            "start": start,
            "end": end_t,
            "location": e.get("location", ""),
            "description": e.get("description", ""),
            "attendees": [a["email"] for a in e.get("attendees", [])],
        })
    return events


def create_event(
    title: str,
    start_time: str,
    end_time: str,
    description: str = "",
    location: str = "",
    attendees: list[str] | None = None,
) -> str:
    service = _get_service()
    body = {
        "summary": title,
        "description": description,
        "location": location,
        "start": {"dateTime": start_time, "timeZone": TIMEZONE},
        "end": {"dateTime": end_time, "timeZone": TIMEZONE},
    }
    if attendees:
        body["attendees"] = [{"email": a} for a in attendees]

    event = service.events().insert(calendarId="primary", body=body).execute()
    return f"Event created: '{title}' on {start_time} (ID: {event['id']})"


def update_event(
    event_id: str,
    title: str | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
    description: str | None = None,
    location: str | None = None,
) -> str:
    service = _get_service()
    event = service.events().get(calendarId="primary", eventId=event_id).execute()

    if title:
        event["summary"] = title
    if description is not None:
        event["description"] = description
    if location is not None:
        event["location"] = location
    if start_time:
        event["start"] = {"dateTime": start_time, "timeZone": TIMEZONE}
    if end_time:
        event["end"] = {"dateTime": end_time, "timeZone": TIMEZONE}

    service.events().update(calendarId="primary", eventId=event_id, body=event).execute()
    return f"Event updated: '{event.get('summary')}'"


def delete_event(event_id: str) -> str:
    service = _get_service()
    event = service.events().get(calendarId="primary", eventId=event_id).execute()
    title = event.get("summary", event_id)
    service.events().delete(calendarId="primary", eventId=event_id).execute()
    return f"Event deleted: '{title}'"
