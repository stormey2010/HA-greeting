"""Small asynchronous CalDAV reader for calendar events and VTODO tasks."""

from __future__ import annotations

import datetime as dt
import html
import re
import xml.etree.ElementTree as ET
from typing import Any
from urllib.parse import urljoin
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from aiohttp import BasicAuth, ClientSession, ClientTimeout
from homeassistant.util import dt as dt_util

DAV = "DAV:"
CALDAV = "urn:ietf:params:xml:ns:caldav"
TIMEOUT = ClientTimeout(total=18)


def _tag(ns: str, value: str) -> str:
    return f"{{{ns}}}{value}"


async def _request(session: ClientSession, url: str, method: str, body: str, depth: str, auth: BasicAuth) -> str:
    async with session.request(
        method, url, data=body.encode(), auth=auth, headers={"Depth": depth, "Content-Type": "application/xml; charset=utf-8"}, timeout=TIMEOUT,
    ) as response:
        response.raise_for_status()
        return await response.text()


def _hrefs(xml_text: str) -> list[tuple[str, str, bool]]:
    """Return href, display name and whether the resource is a calendar."""
    root = ET.fromstring(xml_text)
    result = []
    for item in root.findall(f".//{_tag(DAV, 'response')}"):
        href = item.findtext(_tag(DAV, "href"))
        if not href:
            continue
        prop = item.find(f".//{_tag(DAV, 'prop')}")
        if prop is None:
            continue
        name = prop.findtext(_tag(DAV, "displayname")) or href.rstrip("/").split("/")[-1]
        resource = prop.find(f".//{_tag(CALDAV, 'calendar')}") is not None
        result.append((href, name, resource))
    return result


async def async_discover_calendars(
    session: ClientSession, url: str, username: str, password: str
) -> list[dict[str, str]]:
    """Discover collections using the CalDAV principal and home-set properties."""
    auth = BasicAuth(username, password)
    root_url = url.rstrip("/") + "/"
    principal_query = f'''<?xml version="1.0"?><d:propfind xmlns:d="DAV:"><d:prop><d:current-user-principal/></d:prop></d:propfind>'''
    xml_text = await _request(session, root_url, "PROPFIND", principal_query, "0", auth)
    principal_root = ET.fromstring(xml_text)
    principal_href = principal_root.findtext(f".//{_tag(DAV, 'current-user-principal')}/{_tag(DAV, 'href')}")
    if principal_href is None:
        # Some CalDAV services expose the principal's home directly at the configured URL.
        principal_url = root_url
    else:
        principal_url = urljoin(root_url, principal_href)
    home_query = f'''<?xml version="1.0"?><d:propfind xmlns:d="DAV:" xmlns:c="{CALDAV}"><d:prop><c:calendar-home-set/></d:prop></d:propfind>'''
    home_xml = await _request(session, principal_url, "PROPFIND", home_query, "0", auth)
    home_root = ET.fromstring(home_xml)
    home_href = home_root.findtext(f".//{_tag(CALDAV, 'calendar-home-set')}/{_tag(DAV, 'href')}")
    if not home_href:
        raise ValueError("caldav_calendar_home_not_found")
    home_url = urljoin(root_url, home_href)
    calendar_query = f'''<?xml version="1.0"?><d:propfind xmlns:d="DAV:" xmlns:c="{CALDAV}"><d:prop><d:displayname/><d:resourcetype/></d:prop></d:propfind>'''
    calendar_xml = await _request(session, home_url, "PROPFIND", calendar_query, "1", auth)
    calendars = []
    for href, name, is_calendar in _hrefs(calendar_xml):
        if is_calendar:
            calendars.append({"name": name, "url": urljoin(home_url, href)})
    if not calendars:
        raise ValueError("caldav_no_calendars_found")
    return calendars


def _unescape(value: str) -> str:
    return html.unescape(value.replace(r"\n", " ").replace(r"\,", ",").replace(r"\;", ";").replace(r"\\", "\\"))


def _unfold(ical: str) -> list[str]:
    lines: list[str] = []
    for line in ical.replace("\r\n", "\n").split("\n"):
        if line.startswith((" ", "\t")) and lines:
            lines[-1] += line[1:]
        else:
            lines.append(line)
    return lines


def _ical_datetime(value: str | None, timezone_name: str | None = None) -> str | None:
    """Convert a basic iCalendar DATE/DATE-TIME to an ISO string."""
    if not value:
        return None
    if re.fullmatch(r"\d{8}", value):
        return dt.datetime.strptime(value, "%Y%m%d").date().isoformat()
    utc = value.endswith("Z")
    clean = value.rstrip("Z")
    for fmt in ("%Y%m%dT%H%M%S", "%Y%m%dT%H%M"):
        try:
            parsed = dt.datetime.strptime(clean, fmt)
            if utc:
                parsed = parsed.replace(tzinfo=dt.UTC)
            else:
                try:
                    timezone = ZoneInfo(timezone_name) if timezone_name else dt_util.get_default_time_zone()
                except ZoneInfoNotFoundError:
                    timezone = dt_util.get_default_time_zone()
                parsed = parsed.replace(tzinfo=timezone)
            return parsed.isoformat()
        except ValueError:
            pass
    return None


def _parse_date(value: str) -> dt.datetime | dt.date | None:
    if not value:
        return None
    if re.fullmatch(r"\d{8}", value):
        return dt.datetime.strptime(value, "%Y%m%d").date()
    clean = value.rstrip("Z")
    for fmt in ("%Y%m%dT%H%M%S", "%Y%m%dT%H%M"):
        try:
            stamp = dt.datetime.strptime(clean, fmt)
            return stamp.replace(tzinfo=dt.UTC) if value.endswith("Z") else stamp
        except ValueError:
            pass
    return None


def parse_icalendar(ical: str, calendar_name: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Extract limited event and incomplete task fields without descriptions."""
    events: list[dict[str, Any]] = []
    todos: list[dict[str, Any]] = []
    current_type: str | None = None
    fields: dict[str, str] = {}
    for line in _unfold(ical):
        if line in ("BEGIN:VEVENT", "BEGIN:VTODO"):
            current_type = line[6:]
            fields = {}
            continue
        if line in ("END:VEVENT", "END:VTODO") and current_type:
            summary = _unescape(fields.get("SUMMARY", "")).strip()
            if summary and current_type == "VEVENT":
                events.append({"calendar": calendar_name, "summary": summary[:140], "start": _ical_datetime(fields.get("DTSTART"), fields.get("DTSTART_TZID")), "end": _ical_datetime(fields.get("DTEND"), fields.get("DTEND_TZID"))})
            elif summary and current_type == "VTODO":
                status = fields.get("STATUS", "").upper()
                percent = int(fields.get("PERCENT-COMPLETE", "0") or 0)
                if status not in ("COMPLETED", "CANCELLED") and not fields.get("COMPLETED") and percent < 100:
                    due = fields.get("DUE") or fields.get("DUE-DATE")
                    todos.append({"list": calendar_name, "summary": summary[:120], "due": _ical_datetime(due, fields.get("DUE_TZID"))})
            current_type = None
            continue
        if current_type and ":" in line:
            left, value = line.split(":", 1)
            pieces = left.split(";")
            prop = pieces[0].upper()
            params = {piece.split("=", 1)[0].upper(): piece.split("=", 1)[1].strip('"') for piece in pieces[1:] if "=" in piece}
            if prop in {"SUMMARY", "DTSTART", "DTEND", "DUE", "DUE-DATE", "STATUS", "PERCENT-COMPLETE", "COMPLETED"}:
                fields[prop] = value
                if params.get("TZID"):
                    fields[f"{prop}_TZID"] = params["TZID"]
    return events, todos


async def async_get_calendar_data(
    session: ClientSession, settings: dict[str, Any], start: dt.datetime, end: dt.datetime,
    selected_names: list[str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], str | None]:
    """Get selected calendars for an explicit local time window."""
    calendars = await async_discover_calendars(session, settings["url"], settings["username"], settings["password"])
    if selected_names:
        calendars = [item for item in calendars if item["name"] in selected_names]
    if not calendars:
        raise ValueError("caldav_no_selected_calendars")
    start_stamp = start.astimezone(dt.UTC).strftime("%Y%m%dT%H%M%SZ")
    end_stamp = end.astimezone(dt.UTC).strftime("%Y%m%dT%H%M%SZ")
    body = f'''<?xml version="1.0"?><c:calendar-query xmlns:d="DAV:" xmlns:c="{CALDAV}"><d:prop><c:calendar-data><c:expand start="{start_stamp}" end="{end_stamp}"/></c:calendar-data></d:prop><c:filter><c:comp-filter name="VCALENDAR"><c:comp-filter name="VEVENT"><c:time-range start="{start_stamp}" end="{end_stamp}"/></c:comp-filter></c:comp-filter></c:filter></c:calendar-query>'''
    todo_body = f'''<?xml version="1.0"?><c:calendar-query xmlns:d="DAV:" xmlns:c="{CALDAV}"><d:prop><c:calendar-data/></d:prop><c:filter><c:comp-filter name="VCALENDAR"><c:comp-filter name="VTODO"/></c:comp-filter></c:filter></c:calendar-query>'''
    auth = BasicAuth(settings["username"], settings["password"])
    events: list[dict[str, Any]] = []
    todos: list[dict[str, Any]] = []
    todo_error: str | None = None
    for calendar in calendars:
        xml_text = await _request(session, calendar["url"], "REPORT", body, "1", auth)
        root = ET.fromstring(xml_text)
        for data in root.findall(f".//{_tag(CALDAV, 'calendar-data')}"):
            if data.text:
                found_events, found_todos = parse_icalendar(data.text, calendar["name"])
                events.extend(found_events)
                todos.extend(found_todos)
        try:
            todo_xml = await _request(session, calendar["url"], "REPORT", todo_body, "1", auth)
            todo_root = ET.fromstring(todo_xml)
            for data in todo_root.findall(f".//{_tag(CALDAV, 'calendar-data')}"):
                if data.text:
                    _, found_todos = parse_icalendar(data.text, calendar["name"])
                    todos.extend(found_todos)
        except Exception as err:  # Some CalDAV providers do not expose VTODO.
            todo_error = type(err).__name__
    events.sort(key=lambda item: item.get("start") or "")
    return events, todos, todo_error
