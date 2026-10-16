# ARGUS Sample Data

All files in this directory contain **clearly synthetic** security events for
demonstration and testing purposes only.

| File | Description |
|------|-------------|
| `sample_auth_events.jsonl` | JSON Lines format authentication events including brute-force and privilege escalation patterns |

## Important Notes

- All IP addresses use RFC 5737 documentation ranges (`192.0.2.0/24`, `198.51.100.0/24`, `203.0.113.0/24`)
- All hostnames use `.argus.local` or `.invalid` TLDs
- All events are marked `"is_synthetic": true`
- **Do not** use real infrastructure IP addresses or hostnames in this directory
- **Do not** import files from untrusted sources — ARGUS validates but never executes log content
