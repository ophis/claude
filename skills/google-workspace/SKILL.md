---
name: google-workspace
description: >-
  Google Workspace from the command line via the `gws` CLI — Gmail, Drive, Docs,
  Sheets, Slides, Calendar, Chat, Tasks, and more. Use for sending/reading email,
  searching or uploading Drive files, reading/writing spreadsheets, creating docs
  or slides, calendar events, or any Google Workspace API call.
---

# Google Workspace (`gws`)

One CLI over every Google Workspace API (dynamically built from Google's Discovery
service). Two layers: hand-crafted `+` helpers for common tasks, and the generic
`<service> <resource> <method>` passthrough for everything else.

## Command pattern

```
gws <service> <resource> <method> --params '{...}' --json '{request body}'
```
- `--params` — path/query params (ids, ranges, pageSize…)
- `--json` — request body
- Every response is JSON. Add `--page-all` to stream all pages (NDJSON).

## Discover any command — do this instead of guessing flags

```
gws <service> --help                       # resources + helpers for a service
gws <service> +<helper> --help             # flags for a helper
gws schema <service>.<resource>.<method>   # exact params/body for a raw call
```

## Common helpers (`+`)

| Task | Command |
|------|---------|
| Send email | `gws gmail +send --to a@x.com --subject S --body B [--html] [-a file]` |
| Reply (threaded) | `gws gmail +reply ...` |
| Read sheet | `gws sheets +read ...` |
| Append row | `gws sheets +append ...` |
| Agenda | `gws calendar +agenda` |
| Upload | `gws drive +upload ...` |

## Examples

```
gws gmail +send --to me@x.com --subject 'Hi' --body '<b>Bold</b>' --html -a report.pdf
gws drive files list --params '{"pageSize": 10}' --page-all
gws sheets spreadsheets values get --params '{"spreadsheetId":"ID","range":"Sheet1!A1:C10"}'
```

## Auth

```
gws auth login      # one-time, opens browser
gws auth status     # check account/scopes
```

## Gotchas

- **403 `serviceusage` / quota-project:** the signed-in account needs `roles/serviceUsageConsumer`
  on the OAuth client's GCP project (gws sends `x-goog-user-project`; a plain OAuth app does not).
- **Multiple accounts:** no native switch. Export each (`gws auth export --unmasked > a.json`)
  and select per call: `GOOGLE_WORKSPACE_CLI_CREDENTIALS_FILE=a.json gws ...`.
