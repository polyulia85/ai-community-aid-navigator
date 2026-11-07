# Emergency directory (owner: Silver), draft for the safety path

`emergency_directory.json` lists 5 emergency and crisis resources from Julia's Privacy & Crisis Protocol. Each number was checked on the organization's own page on 2026-11-06. Same record shape as the KB, kept in a separate file because crisis resources are not a KB category. The category `emergency_crisis` is PROPOSED for contracts v1.2. This merges together with the Supervisor safety path.

| Resource | Number (as published) | Hours on the page | Status |
|---|---|---|---|
| 911 (County of Sacramento guidance) | 9-1-1 | not stated | needs_review (hours) |
| 988 Suicide & Crisis Lifeline | call/text 988; chat; Spanish press 2 / text AYUDA; Veterans press 1 | main line hours not stated on the pages checked | needs_review (hours) |
| WEAVE Sacramento | (916) 920-2952 | 24-Hour Support & Information Line | verified |
| National Domestic Violence Hotline | 800.799.SAFE (7233); text START to 88788; chat | 24/7/365 | verified |
| Sacramento Regional Family Justice Center | 916.875.HOPE (4673); 3701 Power Inn, Suite 3100 | not listed | needs_review (hours) |

All 5 numbers match Julia's protocol.

**For the team:** 911 and 988 show availability `unknown` because the pages checked don't state their hours. The safety path should always show them, whatever this field says.

Rebuild with `python navigator/kb/emergency/build_emergency.py`. Tests are in `tests/kb_emergency/`.
