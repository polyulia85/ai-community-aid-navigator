# Nov 2 update: Saint John's reopening + ev_calfresh_020 recheck (owner: Silver)

Staged draft (not published): `navigator/kb/staged/kb_sacramento_nov2_DRAFT.json`. The live KB is unchanged until step 4.

**What changes on publish**
| Record | Before (Oct) | After (Nov 2) |
|---|---|---|
| Saint John's `availability` | `temporarily_closed` | `confirmed_open` |
| ev_sjhap_019 "All of the funds for October 2026 have been exhausted." + ev_sjhap_022 "...reopen on Monday, November 2nd." (effective_date 2026-11-02) | in record | both replaced by **ev_sjhap_021** "Applications for November assistance are open as of Monday, November 2, 2026." (effective_date 2026-11-02) |
| ev_sjhap_014 "Applications for November assistance reopen Monday, November 2." | in record | replaced by **ev_sjhap_020** "...reopened on Monday, November 2, 2026." |
| ev_calfresh_020 (ABAWD waiver list) | checked 2026-10-21 | rechecked on Nov 2; next recheck 2027-11-01 |

Replaced rows are kept in `navigator/kb/history/superseded_evidence.json` (provenance).

**On Monday, Nov 2**
1. Open https://saintjohnsprogram.org/get-help/housing-assistance-program/ and confirm applications are open for November.
   - If the page already says November funds are exhausted, **do not publish**. Keep `temporarily_closed` and tell Slav.
   - If the wording differs from ev_sjhap_020 / ev_sjhap_021, edit those two claims in `navigator/kb/tools/build_kb.py` to match the page.
   - Also check the delivery wording (ev_sjhap_015, "middle to end of November") and the processing time sentence (ev_sjhap_018, written for October applicants).
2. Open https://cdss.ca.gov/inforesources/CalFresh/ABAWD and confirm Sacramento County is not on the Nov 1, 2026 - Oct 31, 2027 waiver list.
3. Note the time you checked (Pacific time is -08:00 after Nov 1).
4. Publish and check:
   ```
   python navigator/kb/tools/build_kb.py --nov2 publish --checked-at 2026-11-02T09:30:00-08:00
   python navigator/kb/tools/validate_kb.py
   python -m unittest discover tests -v
   python navigator/samples/agent_3_4_5/make_samples.py
   ```
5. Send Slav the new `navigator/kb/kb_sacramento.json` (he re-runs the Supervisor on Nov 2).
