# Parker's Morning Briefing

A standalone Home Assistant custom integration for gathering selected home data, asking Cerebras to phrase a short briefing, and announcing it through the configured Home Assistant script. Home Assistant runs the schedule and the action; the AI receives facts only and has no Home Assistant tools.

## What the briefing includes

- Date and weekday.
- Weather from one selected weather entity.
- Calendar events for **today and tomorrow** from either selected Home Assistant calendar entities or direct CalDAV access. iCloud Calendar is supported through CalDAV.
- To-do items from selected Home Assistant lists or CalDAV VTODO collections where the provider exposes them.
- Optional selected people, low-battery sensors, and concise summaries of important unread Gmail messages.
- One action, `morning_briefing.generate`, for the wake-up automation.
- A `sensor.morning_briefing_last_run` entity with the last run time and per-source result only. It does not contain event subjects, email headers, or message content.

If Cerebras is unavailable, the integration speaks a deterministic summary from the data it did retrieve. Failed sources are logged by source name and marked in the status sensor; one source failure does not discard other sections.

## Install

### HACS

Add this repository's GitHub URL in **HACS → Integrations → ⋮ → Custom repositories**, choose **Integration**, then install **Parker's Morning Briefing** and restart Home Assistant. The repository must contain `custom_components/morning_briefing/` at its root.

### Manual install

Copy the complete `custom_components/morning_briefing` directory into `/config/custom_components/morning_briefing/`, then restart Home Assistant.

After restart, open **Settings → Devices & services → Add integration**, search for **Parker's Morning Briefing**, and complete the flow. The Cerebras API key is required. CalDAV and Gmail are optional.

## Cerebras setup

Create an API key in [Cerebras Cloud](https://cloud.cerebras.ai/). Enter it in the integration setup flow; it is stored with the Home Assistant config entry, not in this repository or the Python source. Choose one of the offered model IDs in setup. The default is `gpt-oss-120b`.

The integration sends a normalized facts object to Cerebras. Calendar titles, selected presence/battery facts, and—if enabled—sender/subject/date plus text excerpts of unread email leave the Home Assistant host for summarization. Email excerpt size is configurable (250 to 10,000 characters per message); attachments are not downloaded or sent. Leave Gmail disabled if you do not want email content sent to Cerebras.

## Calendar setup

### iCloud Calendar / CalDAV

During setup, enter:

- Server URL: `https://caldav.icloud.com`
- Username: your Apple Account email address
- Password: an Apple **app-specific password**, not your Apple Account password

Generate an app-specific password at [account.apple.com](https://account.apple.com/) under **Sign-In and Security → App-Specific Passwords**. Apple requires two-factor authentication for app-specific passwords.

After setup, open the integration's **Configure** page. Set **Calendar source** to **CalDAV**, enable calendar events, and choose calendars in **CalDAV calendars**:

- Select one or more names to include only those calendars; clear the selection to include every discovered calendar.
- Add or remove calendars by changing the multi-select and saving. Reopen the page after changing CalDAV credentials to refresh the available calendar list.
- Optionally map calendar names to people under **Calendar labels**, one per line as `calendar name = person or label` (for example, `Emily's calendar = Emily`). Home Assistant calendar entity names and CalDAV calendar names are included with events.

No `calendar.*` entities are required for this direct CalDAV path. Event requests cover local midnight today through local midnight after tomorrow, so both today and tomorrow are included and date boundaries follow Home Assistant's time zone.

### Other CalDAV providers

Use that provider's CalDAV service URL and credentials. Some providers require an app password. The server needs CalDAV principal discovery, calendar-query reports, and calendar data support.

### Home Assistant calendar entities

Alternatively set **Calendar source** to **Home Assistant**, enable calendar events, and select one or more `calendar.*` entities. The integration asks Home Assistant for events in the same today-plus-tomorrow time window.

### Apple Reminders / PyRemindKit

The integration can try CalDAV `VTODO` task lists, which works only when the calendar provider exposes them. iCloud Reminders availability can vary by account/list and isn't guaranteed. [PyRemindKit](https://github.com/namuan/pyremindkit) itself uses Apple's EventKit/Foundation through PyObjC; those macOS frameworks are not available inside a normal Home Assistant host. This integration therefore does not import PyRemindKit. If CalDAV does not expose your reminder lists, using that library would require a separate Mac process with Reminders permission.

## Gmail setup (optional)

The integration does not need a manually pasted refresh token. Home Assistant stores the OAuth token set and refreshes the access token automatically. A refresh token is still required internally by Google's offline OAuth flow so Gmail continues to work after short-lived access tokens expire.

1. In Google Cloud Console, create a project and enable the Gmail API.
2. Configure the OAuth consent screen and add your Google account as a test user when the app is in Testing.
3. Create a Google OAuth **Web application** client. Add `https://my.home-assistant.io/redirect/oauth` as an authorized redirect URI.
4. In Home Assistant, open **Settings → Devices & services → ⋮ → Application credentials** and register the Google client ID and secret for **Parker's Morning Briefing**.
5. Add the integration and turn on **Connect Gmail (optional)**. Home Assistant opens Google's consent flow and stores the OAuth result. The integration requests `gmail.readonly` to screen unread Inbox messages and summarize short text excerpts from the most relevant ones. Gmail promotional, social, and forum categories are filtered before summarization. Attachments are not downloaded or sent. If Gmail was linked before the scope changed, use **Reconfigure**, keep Gmail enabled, and select **Reconnect Gmail and grant message-read access**. This updates the token without removing the integration or its settings.

`gmail.readonly` is a restricted Google scope. A personal OAuth app left in Testing may issue refresh tokens that expire after seven days; in that case Google authorization must be repeated periodically. Public HACS distribution can require Google's OAuth verification and security review, so users may need their own Google OAuth app credentials. A later token revocation starts Home Assistant's reauthentication flow.

## Configure the sources and speaker

Open **Settings → Devices & services → Parker's Morning Briefing → Configure**. All non-secret behavior settings live here, and saving them updates the existing entry without removing it. You can:

- Enable or disable weather, calendar, to-do, presence, battery, and Gmail independently.
- Select the weather, calendar, to-do, person, and battery entities.
- Change between CalDAV and Home Assistant calendars.
- Add/remove CalDAV calendars through the multi-select.
- Edit the full AI prompt, choose a Cerebras model, and adjust AI creativity (temperature). The integration does not impose a word limit on the generated briefing.
- Set the low battery threshold, maximum calendar and to-do items, unread Gmail review count (up to 20), per-email excerpt size, and which Gmail categories to exclude.
- Choose the announcement script, speaker, and volume.

The Cerebras API key and Gmail authorization are managed separately in **Reconfigure**. Leave the API key field blank to keep the saved key; use the Gmail reconnect checkbox only when authorization needs refreshing. Reconfigure does not reset the Configure options. CalDAV server credentials can be edited in Configure, and calendar selection and person labels can be changed there too.

The initial speaker defaults preserve the existing path: `script.new_script`, `media_player.parker_s_echo_dot`, and volume `29`. The script is called with `text`, `device`, and `volume` variables. Change these in options if your delivery script uses different input names.

## Call it from the wake-up automation

Add one action to the automation:

```yaml
action: morning_briefing.generate
```

Or in older YAML form:

```yaml
service: morning_briefing.generate
```

Home Assistant controls when this action runs. You can also run `morning_briefing.generate` manually from **Developer tools → Actions**.

## Privacy and limits

- The Cerebras key, CalDAV password, and OAuth tokens are stored in the Home Assistant config entry and are never written to source code or logs.
- Gmail is opt-in. The integration checks unread Inbox counts, excludes the selected categories, and sends up to 20 selected message excerpts (with a configurable excerpt size) to Cerebras for importance filtering and summarization. Attachments are never fetched.
- The default entity selections are explicit, and the integration never reads all Home Assistant states.
- Email excerpts/headers and selected calendar/task titles are included in the Cerebras request when their sections are enabled.
- The status entity stores only a timestamp and source-level success/failure labels, not the briefing text or source payloads.
- CalDAV recurrence expansion depends on the provider's CalDAV implementation. CalDAV VTODO support varies.

## Earlier single-file approach

This integration replaces the earlier single-file approach. Do not run an older script version alongside it, or it may announce duplicate briefings.

## References

- [Home Assistant config flows](https://developers.home-assistant.io/docs/core/integration/config_flow/)
- [Home Assistant OAuth 2.0 support](https://developers.home-assistant.io/docs/oauth2/)
- [Home Assistant application credentials](https://developers.home-assistant.io/docs/core/platform/application_credentials/)
- [HACS integration repository requirements](https://www.hacs.dev/docs/publish/integration/)
- [Gmail API scopes](https://developers.google.com/workspace/gmail/api/auth/scopes)
- [Gmail message list API](https://developers.google.com/workspace/gmail/api/reference/rest/v1/users.messages/list)
- [Google OAuth application publishing requirements](https://support.google.com/cloud/answer/15549945)
- [Cerebras Inference documentation](https://inference-docs.cerebras.ai/)
- [Apple app-specific passwords](https://support.apple.com/en-us/102654)
- [CalDAV protocol (RFC 4791)](https://www.rfc-editor.org/rfc/rfc4791.html)
- [PyRemindKit](https://github.com/namuan/pyremindkit)
