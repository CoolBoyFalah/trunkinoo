"""Tool definitions for Claude + executor that routes calls to real integrations."""

from __future__ import annotations

TOOLS = [
    {
        "name": "read_emails",
        "description": (
            "Read emails from Gmail inbox. Use this to check the latest emails, "
            "look for emails from specific senders, or search by keyword."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "max_results": {
                    "type": "integer",
                    "description": "How many emails to fetch (default 10)",
                    "default": 10,
                },
                "query": {
                    "type": "string",
                    "description": "Gmail search query e.g. 'from:boss@company.com' or 'subject:invoice'",
                    "default": "",
                },
            },
        },
    },
    {
        "name": "send_email",
        "description": "Send an email via Gmail on behalf of the user.",
        "input_schema": {
            "type": "object",
            "properties": {
                "to":      {"type": "string", "description": "Recipient email address"},
                "subject": {"type": "string", "description": "Email subject line"},
                "body":    {"type": "string", "description": "Email body text"},
                "cc":      {"type": "string", "description": "CC recipients, comma-separated", "default": ""},
            },
            "required": ["to", "subject", "body"],
        },
    },
    {
        "name": "reply_to_email",
        "description": "Reply to an existing email thread.",
        "input_schema": {
            "type": "object",
            "properties": {
                "message_id": {"type": "string", "description": "The ID of the email to reply to"},
                "body":       {"type": "string", "description": "Reply body text"},
                "reply_all":  {"type": "boolean", "description": "Reply-all instead of reply", "default": False},
            },
            "required": ["message_id", "body"],
        },
    },
    {
        "name": "get_schedule",
        "description": "Get upcoming calendar events from Google Calendar.",
        "input_schema": {
            "type": "object",
            "properties": {
                "days_ahead":  {"type": "integer", "description": "How many days ahead to look", "default": 7},
                "max_results": {"type": "integer", "description": "Max events to return", "default": 20},
            },
        },
    },
    {
        "name": "create_event",
        "description": "Create a new event in Google Calendar.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title":       {"type": "string", "description": "Event title"},
                "start_time":  {"type": "string", "description": "Start time ISO 8601, e.g. '2026-06-15T14:00:00'"},
                "end_time":    {"type": "string", "description": "End time ISO 8601"},
                "description": {"type": "string", "description": "Event description or agenda", "default": ""},
                "location":    {"type": "string", "description": "Location or meeting link", "default": ""},
                "attendees":   {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of attendee email addresses",
                    "default": [],
                },
            },
            "required": ["title", "start_time", "end_time"],
        },
    },
    {
        "name": "update_event",
        "description": "Update an existing Google Calendar event.",
        "input_schema": {
            "type": "object",
            "properties": {
                "event_id":    {"type": "string", "description": "Calendar event ID"},
                "title":       {"type": "string"},
                "start_time":  {"type": "string"},
                "end_time":    {"type": "string"},
                "description": {"type": "string"},
                "location":    {"type": "string"},
            },
            "required": ["event_id"],
        },
    },
    {
        "name": "delete_event",
        "description": "Delete a Google Calendar event.",
        "input_schema": {
            "type": "object",
            "properties": {
                "event_id": {"type": "string", "description": "Calendar event ID to delete"},
            },
            "required": ["event_id"],
        },
    },
    {
        "name": "web_search",
        "description": "Search the web for information, news, facts, or research.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "save_memory",
        "description": (
            "Save something important to long-term memory so you remember it in future conversations. "
            "Use this for preferences, important facts, recurring contacts, habits, etc."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "key":   {"type": "string", "description": "Short label / category for this memory"},
                "value": {"type": "string", "description": "What to remember"},
            },
            "required": ["key", "value"],
        },
    },
    {
        "name": "recall_memory",
        "description": "Recall something from long-term memory. Use key='all' to see everything stored.",
        "input_schema": {
            "type": "object",
            "properties": {
                "key": {"type": "string", "description": "Memory key to recall, or 'all' for everything"},
            },
            "required": ["key"],
        },
    },
    {
        "name": "delete_memory",
        "description": "Delete a specific memory entry.",
        "input_schema": {
            "type": "object",
            "properties": {
                "key": {"type": "string", "description": "Memory key to delete"},
            },
            "required": ["key"],
        },
    },
]


def execute_tool(name: str, args: dict, memory) -> str:
    """Route a tool call from Claude to the correct integration."""

    # ── memory tools ──────────────────────────────────────────────────────────
    if name == "save_memory":
        return memory.save(args["key"], args["value"])

    if name == "recall_memory":
        return memory.recall(args["key"])

    if name == "delete_memory":
        return memory.delete(args["key"])

    # ── email tools ───────────────────────────────────────────────────────────
    if name == "read_emails":
        from integrations.gmail import read_emails
        emails = read_emails(
            max_results=args.get("max_results", 10),
            query=args.get("query", ""),
        )
        if not emails:
            return "No emails found."
        lines = []
        for e in emails:
            lines.append(
                f"[ID: {e['id']}] From: {e['from']} | Subject: {e['subject']} | Date: {e['date']}\n"
                f"Preview: {e['snippet']}\n"
                f"Body: {e['body'][:800]}\n"
            )
        return "\n---\n".join(lines)

    if name == "send_email":
        from integrations.gmail import send_email
        return send_email(
            to=args["to"],
            subject=args["subject"],
            body=args["body"],
            cc=args.get("cc", ""),
        )

    if name == "reply_to_email":
        from integrations.gmail import reply_to_email
        return reply_to_email(
            message_id=args["message_id"],
            body=args["body"],
            reply_all=args.get("reply_all", False),
        )

    # ── calendar tools ────────────────────────────────────────────────────────
    if name == "get_schedule":
        from integrations.gcalendar import get_events
        events = get_events(
            days_ahead=args.get("days_ahead", 7),
            max_results=args.get("max_results", 20),
        )
        if not events:
            return "No upcoming events found."
        lines = []
        for e in events:
            att = ", ".join(e["attendees"]) if e["attendees"] else "just you"
            lines.append(
                f"[ID: {e['id']}] {e['title']}\n"
                f"  Start: {e['start']}  End: {e['end']}\n"
                f"  Location: {e['location'] or 'N/A'}  Attendees: {att}\n"
                f"  Notes: {e['description'][:200] or 'None'}"
            )
        return "\n---\n".join(lines)

    if name == "create_event":
        from integrations.gcalendar import create_event
        return create_event(
            title=args["title"],
            start_time=args["start_time"],
            end_time=args["end_time"],
            description=args.get("description", ""),
            location=args.get("location", ""),
            attendees=args.get("attendees", []),
        )

    if name == "update_event":
        from integrations.gcalendar import update_event
        return update_event(
            event_id=args["event_id"],
            title=args.get("title"),
            start_time=args.get("start_time"),
            end_time=args.get("end_time"),
            description=args.get("description"),
            location=args.get("location"),
        )

    if name == "delete_event":
        from integrations.gcalendar import delete_event
        return delete_event(event_id=args["event_id"])

    # ── web search ────────────────────────────────────────────────────────────
    if name == "web_search":
        from integrations.websearch import web_search
        results = web_search(args["query"])
        if not results:
            return "No search results found."
        lines = [f"- {r['title']}: {r['body'][:300]}" for r in results]
        return "\n".join(lines)

    return f"Unknown tool: {name}"
