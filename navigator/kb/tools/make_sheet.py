"""Builds the review spreadsheet from navigator/kb/kb_sacramento.json. Run: python navigator/kb/tools/make_sheet.py <out.xlsx>"""
import json, os, sys
from collections import OrderedDict
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.worksheet.datavalidation import DataValidation

KB = os.path.join(os.path.dirname(__file__), "..", "kb_sacramento.json")
OUT = sys.argv[1] if len(sys.argv) > 1 else "Silver_KB_Records_v1.0.xlsx"
d = json.load(open(KB, encoding="utf-8")); P = d["program_records"]; ev = d["evidence_records"]
F = "Arial"; H = Font(name=F, bold=True, color="FFFFFF"); HF = PatternFill("solid", fgColor="1F3A5F")
B = Font(name=F, size=10); thin = Side(style="thin", color="C8CDD3"); BOX = Border(top=thin, bottom=thin, left=thin, right=thin)
STAT = {"verified": "E3F1E6", "needs_review": "FFF2CC", "conflicting": "F8D7DA", "unverified": "EDEDED"}
AVC = {"confirmed_open": "E3F1E6", "temporarily_closed": "F8D7DA", "unknown": "EDEDED"}
wb = Workbook()


def table(ws, headers, rows, widths):
    ws.append(headers)
    for c in ws[1]: c.font, c.fill, c.alignment, c.border = H, HF, Alignment(wrap_text=True, vertical="center"), BOX
    for r in rows: ws.append(r)
    for row in ws.iter_rows(min_row=2):
        for c in row: c.font, c.alignment, c.border = B, Alignment(wrap_text=True, vertical="top"), BOX
    for i, w in enumerate(widths): ws.column_dimensions[chr(65 + i)].width = w
    ws.freeze_panes = "B2"; ws.row_dimensions[1].height = 30


n = {s: sum(e["verification_status"] == s for e in ev) for s in STAT}
r = wb.active; r.title = "README"
lines = [
    ("Sacramento Verified Knowledge Base: Records sheet v1.0", True),
    ("Owner: Silver Sanchez Cardenas (Agents 3-5). Contract: Shared JSON Contracts v1.0, sections 3.4 and 3.5. Canonical form: kb_sacramento.json (Slav, Oct 22).", False),
    (f"Status: 4 records covering all three P0 areas (food, housing, income) for the Oct 26 integration. {len(ev)} claims: {n['verified']} verified, {n['needs_review']} needs_review, {n['conflicting']} conflicting, {n['unverified']} unverified.", False),
    ("", False),
    ("Changes in v1.0 (Oct 24, aligned with Shared Contracts v1.0)", True),
    ("ev_calfresh_020 (ABAWD waiver list): recheck date added in notes: RECHECK BY 2026-11-02. No other data changes.", False),
    ("", False),
    ("Changes in v0.3 (Oct 23)", True),
    ("Coordinated Access: added PSAP eligibility and the documents needed for financial assistance (SSF Coordinated Access System page, modified Oct 6, 2026); replaced the vague prevention claim (ev_cas_005); availability unknown -> confirmed_open (access line operating; HHAP prevention funding noted). All 12 claims now verified. IDs ev_cas_001-010 unchanged; new ev_cas_011-012.", False),
    ("", False),
    ("Changes in v0.2 (Slav's review, Oct 22)", True),
    ("CalFresh: required_documents[0-11] confirmed linked to ev_calfresh_022-033 in the JSON (validator now also checks every evidence row is linked into its ProgramRecord). Evidence IDs 001-052 unchanged.", False),
    ("CalFresh: SAR 7 and renewal added as eligibility_criteria[17-19] ('To keep benefits...'), ev_calfresh_053-055. Two are needs_review (see Gaps_Questions).", False),
    ("New: EDD Unemployment Insurance (income), Saint John's Housing Assistance Program (rental, temporarily closed), Sacramento Coordinated Access via 2-1-1 press 8 (housing, open access route).", False),
    ("", False),
    ("How to read this sheet", True),
    ("ProgramRecords: one row per program. Claim fields list the evidence_ids that hold their values.", False),
    ("EvidenceRecords: one row per fact. field_path says which ProgramRecord field it fills, e.g. application_method[2].", False),
    ("Sources: the pages used and what each one is authoritative for. Gaps_Questions: what is missing or unclear. Allowed_Values: dropdowns.", False),
    ("", False),
    ("Rules followed", True),
    ("Official or operator sources only: state agencies (CDSS, EDD), state portal (BenefitsCal), county operator (DHA), the program operator's own page, the Continuum of Care lead (SSF) and 2-1-1 for access routes.", False),
    ("Missing facts are left empty, never guessed. Wording never promises eligibility or outcomes. Unclear facts are needs_review with a note saying how to confirm.", False),
    ("checked_at: CalFresh 001-052 on 2026-10-21 (22:36-23:24 PT); other rows on 2026-10-22 19:50 PT, except ev_cas_005, 011, 012 (Coordinated Access System page) on 2026-10-23 01:55 PT.", False),
]
for t, bold in lines:
    r.append([t]); c = r.cell(r.max_row, 1); c.font = Font(name=F, bold=bold, size=13 if bold and r.max_row == 1 else 10); c.alignment = Alignment(wrap_text=True)
r.column_dimensions["A"].width = 130


def refs(p, f): return ", ".join(x for c in p[f] for x in c["evidence_refs"]) or "(empty, see Gaps_Questions)"


pr = wb.create_sheet("ProgramRecords")
ph = ["program_id", "program_name", "organization", "category", "subcategory (PROPOSED)", "geography", "eligibility_criteria", "required_documents",
      "application_method", "contact", "deadlines", "processing_time", "availability", "sources", "last_verified_at", "verification_status"]
table(pr, ph, [[p["program_id"], p["program_name"], p["organization"], p["category"], p["subcategory"], "; ".join(p["geography"]),
                refs(p, "eligibility_criteria"), refs(p, "required_documents"), refs(p, "application_method"), refs(p, "contact"), refs(p, "deadlines"),
                ", ".join(p["processing_time"]["evidence_refs"]) if p["processing_time"] else "(empty)", p["availability"], ", ".join(p["sources"]),
                p["last_verified_at"], p["verification_status"]] for p in P],
      [28, 22, 30, 18, 22, 18, 34, 30, 30, 30, 22, 18, 18, 40, 24, 18])
for row in pr.iter_rows(min_row=2):
    row[12].fill = PatternFill("solid", fgColor=AVC[row[12].value]); row[15].fill = PatternFill("solid", fgColor=STAT[row[15].value])
er = wb.create_sheet("EvidenceRecords")
eh = ["evidence_id", "program_id", "field_path", "claim_value", "source_url", "checked_at", "verification_status", "source_title", "source_authority_scope", "effective_date", "notes"]
table(er, eh, [[e[k] for k in eh] for e in ev], [17, 28, 22, 60, 34, 24, 16, 30, 22, 13, 55])
for row in er.iter_rows(min_row=2):
    row[6].fill = PatternFill("solid", fgColor=STAT[row[6].value])
src = OrderedDict()
for e in ev: src.setdefault(e["source_url"] + "|" + e["source_title"], []).append(e)
so = wb.create_sheet("Sources")
table(so, ["source_url", "source_title", "authority_scope", "checked_at", "claims used"],
      [[v[0]["source_url"], v[0]["source_title"], v[0]["source_authority_scope"], v[0]["checked_at"], ", ".join(x["evidence_id"] for x in v)] for v in src.values()],
      [50, 50, 26, 24, 60])
g = wb.create_sheet("Gaps_Questions")
table(g, ["#", "program", "type", "item", "next step"], [
    [1, "CalFresh", "needs_review", "Gross income dollar limits (ev_calfresh_012): CDSS page last updated Sept 2025; limits may have changed Oct 1, 2026", "Find the CDSS notice with limits effective Oct 1, 2026"],
    [2, "CalFresh", "needs_review", "SAR 7 timing (ev_calfresh_054): DHA page says 'six (6) months after applying for RCA', likely a copy error", "Confirm with DHA 1-800-560-0976"],
    [3, "CalFresh", "needs_review", "12-month renewal (ev_calfresh_055): undated CDSS outreach handbook", "Confirm with DHA or a current CDSS letter"],
    [4, "CalFresh", "gap", "Net income dollar limits not published on a dated statewide source", "Unknown is not a mismatch"],
    [5, "EDD UI", "gap", "Base-period wage thresholds and benefit formula not on the eligibility page", "Agent 4 must not estimate; EDD decides"],
    [6, "Saint John's", "resolved Oct 25", "Page now says assistance is 'delivered by the middle to end of November' (ev_sjhap_015). All Saint John's claims rechecked against the page text on Oct 25", "None"],
    [7, "Saint John's", "test-case impact", "Rent is due Nov 1; applications reopen Nov 2. The program cannot cover the Nov 1 payment on time", "Agent 6 / Hisham: show as 'reopens Nov 2', not as current help"],
    [8, "Saint John's", "gap", "No online form or email; 'all required documents' not itemized", "Ask the program by phone"],
    [9, "Coordinated Access", "resolved in v0.3", "Eligibility and financial-assistance documents now published (SSF CAS page); access line operating; $2M/yr HHAP prevention funding. Income limits still not published", "2-1-1 specialist decides each case; help not guaranteed"],
    [10, "All", "question", "Statewide programs use geography 'California' (covers all CA counties). OK with the Supervisor?", "Slav"],
    [11, "All", "question", "Need subcategory used as a preference (ordering), not a hard filter. OK?", "Slav / Julia"],
    [12, "Housing", "future record", "CalWORKs Homeless Assistance (can help with rent arrearages for CalWORKs families; DHA CalWORKs Fact Sheet, July 2026)", "Next housing/income record if time allows"],
], [5, 18, 18, 70, 46])
a = wb.create_sheet("Allowed_Values")
cols = {"category": ["food_assistance", "housing_assistance", "income_assistance", "utility_assistance", "medical_health_coverage", "debt_hardship", "material_in_kind", "crowdfunding_guidance"],
        "subcategory (P0)": ["calfresh_benefits", "food_pantry", "emergency_shelter", "motel_voucher", "rental_assistance", "eviction_prevention", "housing_legal_aid", "unemployment_insurance", "cash_aid", "disability_family_leave", "employment_services"],
        "availability": ["confirmed_open", "temporarily_closed", "unknown"], "verification_status": ["verified", "needs_review", "conflicting", "unverified"]}
for j, (k, v) in enumerate(cols.items(), 1):
    c = a.cell(1, j, k); c.font, c.fill = H, HF; a.column_dimensions[chr(64 + j)].width = 26
    for i, x in enumerate(v, 2): a.cell(i, j, x).font = B


def dv(ws, letter, nrows, rng):
    v = DataValidation(type="list", formula1=f"=Allowed_Values!${letter}$2:${letter}${nrows + 1}", allow_blank=False); ws.add_data_validation(v); v.add(rng)


dv(pr, "A", 8, "D2:D200"); dv(pr, "B", 11, "E2:E200"); dv(pr, "C", 3, "M2:M200"); dv(pr, "D", 4, "P2:P200"); dv(er, "D", 4, "G2:G2000")
wb.save(OUT); print("saved", OUT)
