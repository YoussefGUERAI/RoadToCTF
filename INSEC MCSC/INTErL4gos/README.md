# INTErL4gos

**Category:** Threat Intel
**Flag:** `INSEC{G00d_Hun7_EZ_SHIT}`

A guided OSINT/threat-intel challenge that walks through attribution of a malware hash. The whole chain points at the SolarWinds compromise.

## Answers

| # | Question | Answer |
|---|----------|--------|
| 1 | Malware name associated with the hash | `SUNSPOT` |
| 2 | Filename used to deliver the malware | `taskhostw.exe` |
| 3 | Campaign linked to the malware | `SolarWinds Compromise` |
| 4 | APT linked to it | `APT29` |
| 5 | Number of similar programs in the campaign (incl. this one) | `11` |
| 6 | Hardcoded value delineating log entries in the log file | `3278a5e71a7991ac` |
| 7 | Other process name associated with execution | `MsBuild.exe` |
| 8 | MITRE persistence technique ID | `T1053.005` (Scheduled Task) |
| 9 | Other campaign linked to the group (`id:name`) | `C0023:Operation Ghost` |

## How to approach it

Everything is derivable from the MITRE ATT&CK page for the malware once you have the name:

- Hash → **VirusTotal** / MalwareBazaar → gives malware name (**SUNSPOT**).
- Malware name → **MITRE ATT&CK software page** → campaign, associated group, other software, techniques.
- Campaign page (**C0024 — SolarWinds Compromise**) → lists all 11 software entries.
- Group page (**G0016 — APT29**) → lists all linked campaigns, including **C0023 Operation Ghost**.
- Technique `T1053.005` = *Scheduled Task/Job: Scheduled Task*, the persistence mechanism SUNSPOT uses.
- The hardcoded log delimiter `3278a5e71a7991ac` comes from CrowdStrike's original SUNSPOT report — it's the marker the implant writes between log entries.

## Takeaway

Threat-intel questions rarely need live investigation — the workflow is:
`hash → VT → malware name → ATT&CK software page → ATT&CK campaign page → ATT&CK group page`.
Every field (MITRE IDs, related campaigns, counts) lives on those pages verbatim.
