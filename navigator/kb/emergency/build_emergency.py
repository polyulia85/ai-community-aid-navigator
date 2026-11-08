"""Builds navigator/kb/emergency/emergency_directory.json: verified emergency and crisis resources for the
safety path (Julia's Privacy & Crisis Protocol; Slav, Nov 5). Owner: Silver. Run: python navigator/kb/emergency/build_emergency.py
Same ProgramRecord / EvidenceRecord shape as the KB, kept in a SEPARATE file: crisis resources are not a KB
category (contracts v1.1 §3.4). Category "emergency_crisis" is PROPOSED for contracts v1.2.
Every number and line was checked on the organization's own page. Anything a page does not state is left out
or marked needs_review, never assumed (e.g. 24/7 is only recorded where the page says it)."""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
T = "2026-11-06T16:05:00-08:00"
CATEGORY = "emergency_crisis"  # PROPOSED (contracts v1.2)


def src(url, title, scope):
    return (url, title, scope)


def build(pid, meta, rows, prefix):
    ev = []
    for i, (fp, val, s, notes, *st) in enumerate(rows, 1):
        ev.append({"evidence_id": f"ev_{prefix}_{i:03d}", "program_id": pid, "field_path": fp, "claim_value": val,
                   "source_url": s[0], "checked_at": T, "verification_status": st[0] if st else "verified",
                   "source_title": s[1], "source_authority_scope": s[2], "effective_date": None, "notes": notes})
    claim = lambda e: {"value": e["claim_value"], "evidence_refs": [e["evidence_id"]],
                       "verification_status": e["verification_status"], "checked_at": e["checked_at"]}
    arr = lambda f: [claim(e) for e in ev if e["field_path"].startswith(f + "[")]
    rec = {"program_id": pid, "program_name": meta["name"], "organization": meta["org"], "category": CATEGORY,
           "subcategory": meta["sub"], "geography": meta["geo"], "eligibility_criteria": arr("eligibility_criteria"),
           "required_documents": [], "application_method": arr("application_method"), "contact": arr("contact"),
           "deadlines": [], "processing_time": None, "availability": meta["availability"],
           "sources": [e["evidence_id"] for e in ev], "last_verified_at": T, "verification_status": meta["status"]}
    return rec, ev


R = []
# 1. 911
S911 = src("https://www.saccounty.gov/Pages/Calling911.aspx", "Calling 911 | County of Sacramento (no page date shown)", "county_government")
R.append(build("res_emergency_911_sac_001",
               {"name": "9-1-1 Emergency", "org": "Emergency services (County of Sacramento guidance)", "sub": "emergency_services",
                "geo": ["Sacramento County"], "availability": "unknown", "status": "needs_review"}, [
    ("application_method[0]", "Call 9-1-1 to report: a fire; a serious injury or medical condition; a crime in progress or a serious crime has just occurred; anything that poses or indicates an immediate threat to people or property.", S911, "List items from the page, joined in one claim."),
    ("application_method[1]", "Calmly and clearly answer the dispatcher's questions. Stay on the line until the 9-1-1 dispatcher says it is okay to hang up.", S911, None),
    ("contact[0]", "9-1-1", S911, None),
    ("availability", "The county page does not state hours.", S911, "availability = unknown because the page does not state hours. TEAM DECISION: the safety path should always show 911 regardless of this field.", "needs_review"),
], "e911"))
# 2. 988
S988 = src("https://988lifeline.org/get-help/", "Get Help | 988 Suicide & Crisis Lifeline", "national_service_operator")
R.append(build("res_crisis_988_us_001",
               {"name": "988 Suicide & Crisis Lifeline", "org": "988 Suicide & Crisis Lifeline", "sub": "mental_health_crisis",
                "geo": ["United States"], "availability": "unknown", "status": "needs_review"}, [
    ("application_method[0]", "Call or text 988, or chat at chat.988lifeline.org.", S988, None),
    ("application_method[1]", "Using the 988 Lifeline is free; conversations are confidential.", S988, "Paraphrase of two statements on the page."),
    ("contact[0]", "Call or text 988.", S988, None),
    ("contact[1]", "Spanish: call 988 and press 2, or text AYUDA to 988.", S988, None),
    ("contact[2]", "Veterans, service members and their loved ones: call 988 and press 1 (Veterans Crisis Line).", S988, None),
    ("contact[3]", "Deaf and Hard of Hearing people have 24/7/365 access to 988 Videophone.", S988, None),
    ("availability", "The Get Help page does not state the hours of the main 988 line.", S988, "24/7 is stated only for the Veterans Crisis Line and the videophone on the pages checked (988lifeline.org/get-help, /what-to-expect; samhsa.gov/mental-health/988 and /faqs). Re-check before showing hours. The safety path should always show 988.", "needs_review"),
], "c988"))
# 3. WEAVE
SW = src("https://weaveinc.org/get-help", "Get Help | WEAVE (Sacramento)", "local_provider_operating_intake")
R.append(build("res_dv_weave_sac_001",
               {"name": "WEAVE 24-Hour Support & Information Line", "org": "WEAVE (Sacramento)", "sub": "domestic_violence_sexual_assault",
                "geo": ["Sacramento County"], "availability": "confirmed_open", "status": "verified"}, [
    ("eligibility_criteria[0]", "WEAVE serves adult and child survivors of domestic violence, sexual assault, and sex trafficking.", SW, None),
    ("contact[0]", "24-Hour Support & Information Line: (916) 920-2952", SW, "Matches the number in Julia's protocol."),
    ("availability", "24-Hour Support & Information Line (also described on the page as the 24/7 Support Line).", SW, "Basis for availability = confirmed_open (published hours)."),
], "weave"))
# 4. National DV Hotline
SH = src("https://www.thehotline.org/about/", "About The Hotline | National Domestic Violence Hotline", "national_service_operator")
R.append(build("res_dv_hotline_us_001",
               {"name": "National Domestic Violence Hotline", "org": "National Domestic Violence Hotline (The Hotline)", "sub": "domestic_violence_sexual_assault",
                "geo": ["United States"], "availability": "confirmed_open", "status": "verified"}, [
    ("application_method[0]", "Free, confidential, and compassionate support, in over 200 languages.", SH, None),
    ("contact[0]", "Call 800.799.SAFE (7233).", SH, "Matches the number in Julia's protocol (1-800-799-7233)."),
    ("contact[1]", "Text START to 88788. Msg & data rates may apply.", SH, None),
    ("contact[2]", "Chat with a Live Advocate at thehotline.org.", SH, "Chat hours are not stated separately."),
    ("availability", "24 hours a day, seven days a week, 365 days a year.", SH, "Basis for availability = confirmed_open (published hours)."),
], "ndvh"))
# 5. Sacramento Regional Family Justice Center
SF = src("https://sacda.org/victim-services/family-justice-center/", "The Sacramento Regional Family Justice Center | Sacramento County District Attorney (last modified Feb 2, 2026)", "county_government")
R.append(build("res_dv_fjc_sac_001",
               {"name": "Sacramento Regional Family Justice Center", "org": "Sacramento Regional Family Justice Center (Sacramento County District Attorney)", "sub": "domestic_violence_sexual_assault",
                "geo": ["Sacramento County"], "availability": "unknown", "status": "needs_review"}, [
    ("application_method[0]", "Services listed: individual and group counseling, a mobile civil legal team, safety planning, temporary restraining order applications, and Camp HOPE.", SF, "List from the page, joined in one claim."),
    ("contact[0]", "916.875.HOPE (4673)", SF, "Matches the number in Julia's protocol."),
    ("contact[1]", "3701 Power Inn, Suite 3100 (Third Floor), Sacramento, CA 95826", SF, None),
    ("availability", "Hours are not listed on the page.", SF, "availability = unknown; walk-in policy not stated. Call to confirm.", "needs_review"),
], "fjc"))

out = {"schema_version": "1.0", "note": "Emergency and crisis resources for the safety path. Separate from the KB; category emergency_crisis PROPOSED for contracts v1.2.",
       "program_records": [r for r, _ in R], "evidence_records": [e for _, ev in R for e in ev]}
with open(os.path.join(HERE, "emergency_directory.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, indent=2, ensure_ascii=False)
print(f"{len(R)} resources, {len(out['evidence_records'])} evidence records -> navigator/kb/emergency/emergency_directory.json")
