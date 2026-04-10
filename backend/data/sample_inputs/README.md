# Sample Inputs

This folder contains quick test files for the call center analysis app:

- `good_call_billing_resolved.mp3` — strong customer-support call with a successful resolution
- `bad_call_unresolved.mp3` — poor-quality call with weak empathy and no clear resolution
- `bad_call_shipping_issue.json` — JSON object-format transcript for a poor unresolved shipping/support call
- `good_call_account_lockout.json` — speaker-turn JSON transcript for a well-handled account lockout case

Notes:

- The two MP3 files are ready-made audio validation samples for the upload flow.
- Use `good_call_billing_resolved.mp3` to test a likely high QA score path.
- Use `bad_call_unresolved.mp3` to test a likely poor QA score path.
- Use `bad_call_shipping_issue.json` to validate the `{"transcript": "..."}` JSON path.
- Use `good_call_account_lockout.json` to validate the speaker-turn JSON list path.

Use these with the three input modes in the app:

- Paste Transcript
- Upload Audio File
- Upload JSON Transcript
