"""Builds navigator/kb/kb_sacramento.json (ProgramRecord + EvidenceRecord, contracts v1.1 section 3.5).
Owner: Silver. Run from repo root:  python navigator/kb/tools/build_kb.py
The Nov 2, 2026 update (Saint John's reopening + ev_calfresh_020 recheck) is published and built in permanently;
rows it replaced are written to navigator/kb/history/superseded_evidence.json.
Rules: official / operator sources only; missing facts stay empty; conflicting claims stay separate.
CalFresh evidence IDs 001-052 are kept exactly as in v0.1 (Slav reviewed them); new claims are appended."""
import json, os, re

NOV2_T = "2026-11-02T15:30:00-08:00"   # when the official pages were checked for the Nov 2 update
NOV2_STATUS = "verified"
SUPERSEDED = []  # rows replaced by the Nov 2 update, kept in navigator/kb/history for provenance (TD 9.2)

HERE = os.path.dirname(os.path.abspath(__file__))
KB_DIR = os.path.dirname(HERE)
ORDER = ["program_name", "organization", "geography", "eligibility_criteria", "required_documents",
         "application_method", "contact", "deadlines", "processing_time", "availability"]
ARRAYS = ["eligibility_criteria", "required_documents", "application_method", "contact", "deadlines"]


def ev_row(eid, pid, fp, val, src, eff, notes, status="verified"):
    url, title, scope, ck = src
    return {"evidence_id": eid, "program_id": pid, "field_path": fp, "claim_value": val, "source_url": url,
            "checked_at": ck, "verification_status": status, "source_title": title,
            "source_authority_scope": scope, "effective_date": eff, "notes": notes}


def assemble(meta, ev):
    """Build the ProgramRecord from its EvidenceRecords so claims and evidence can never drift apart."""
    def key(e):
        m = re.match(r"(\w+)(?:\[(\d+)\])?", e["field_path"])
        return (ORDER.index(m.group(1)), int(m.group(2) or 0))
    ev = sorted(ev, key=key)
    claim = lambda e: {"value": e["claim_value"], "evidence_refs": [e["evidence_id"]],
                       "verification_status": e["verification_status"], "checked_at": e["checked_at"]}
    p = {k: meta[k] for k in ("program_id", "program_name", "organization", "category", "subcategory", "geography")}
    for f in ARRAYS:
        p[f] = [claim(e) for e in ev if e["field_path"].startswith(f + "[")]
    pt = [e for e in ev if e["field_path"] == "processing_time"]
    p["processing_time"] = claim(pt[0]) if pt else None
    p["availability"] = meta["availability"]
    p["sources"] = [e["evidence_id"] for e in sorted(ev, key=lambda e: e["evidence_id"])]
    p["last_verified_at"] = max(e["checked_at"] for e in ev)
    p["verification_status"] = meta["verification_status"]
    return p, sorted(ev, key=lambda e: e["evidence_id"])


programs, evidence = [], []

# ---------------------------------------------------------------- 1. CalFresh (v0.1 + Slav's fix)
with open(os.path.join(HERE, "calfresh_v0.1.json"), encoding="utf-8") as f:
    old = json.load(f)
cf_ev = old["evidence_records"]
for e in cf_ev:  # Slav, Oct 24: recheck date for the ABAWD waiver list
    if e["evidence_id"] == "ev_calfresh_020":
        e["notes"] = ("Based on absence from both published lists. RECHECK BY 2026-11-02 (first business day after the "
                      "Nov 1, 2025 - Oct 31, 2026 list ends): confirm the Nov 1, 2026 - Oct 31, 2027 list on the CDSS page is "
                      "unchanged and Sacramento is still not listed. Next recheck after that: 2027-11-01.")
        # Nov 2 recheck (published)
        SUPERSEDED.append(dict(e))
        e["checked_at"], e["verification_status"] = NOV2_T, NOV2_STATUS
        e["source_url"] = "https://cdss.ca.gov/inforesources/cdss-programs/calfresh/able-bodied-adults-without-dependents"  # Slav, Nov 3: page with the 2026-2027 list
        e["notes"] = ("Rechecked " + NOV2_T[:10] + ": "
                      + "the Nov 1, 2026 - Oct 31, 2027 waiver list on the CDSS page does not include Sacramento County. "
                      "Next recheck: 2027-11-01.")
PID = "prog_food_calfresh_sac_001"
T = "2026-10-22T19:50:00-07:00"
DHA = ("https://ha.saccounty.gov/us/en/benefits/CalFresh.html", "CalFresh | Sacramento County Department of Human Assistance ('SAR 7 Information' section)", "county_operator_local_intake", T)
HB = ("https://www.cdss.ca.gov/calfreshoutreach/res/Toolkit/Handbook-GeneralMarket/GeneralMarketHandbook_CH6_MaintainBenefitsWhenEligible.pdf",
      "CalFresh Outreach Basics Handbook, General Market, Ch. 6: Maintain Benefits When Eligible (CDSS)", "state_governing_agency", T)
cf_ev += [
    ev_row("ev_calfresh_053", PID, "eligibility_criteria[17]",
           "To keep benefits: the SAR 7 (semi-annual report) is due by the 5th of the month. It can be completed online at BenefitsCal.com, or the form can be submitted by mail or in person.",
           DHA, None, "Help completing the SAR 7: 1-800-560-0976 (DHA). Added per Slav (Oct 22): ongoing reporting goes in eligibility_criteria, no new field."),
    ev_row("ev_calfresh_054", PID, "eligibility_criteria[18]",
           "To keep benefits: many households must complete a SAR 7 six (6) months after applying.",
           DHA, None, "NEEDS REVIEW: the DHA CalFresh page literally says 'six (6) months after applying for RCA' (RCA = Refugee Cash Assistance), which looks like a copy error on the county page. Confirm with DHA (1-800-560-0976) before showing users a date.",
           status="needs_review"),
    ev_row("ev_calfresh_055", PID, "eligibility_criteria[19]",
           "To keep benefits: in California, most households are on a 12-month certification period (renewal). Households where everyone is 60 or older or has a disability can be certified for 24 months.",
           HB, None, "NEEDS REVIEW: official CDSS outreach handbook, but the chapter is undated and cites 2012-2013 letters. Confirm the current renewal period with DHA or a current CDSS letter.",
           status="needs_review"),
]
p, e = assemble({"program_id": PID, "program_name": "CalFresh", "organization": "Sacramento County Department of Human Assistance (DHA)",
                 "category": "food_assistance", "subcategory": "calfresh_benefits", "geography": ["Sacramento County"],
                 "availability": "confirmed_open", "verification_status": "verified"}, cf_ev)
programs.append(p); evidence += e

# ---------------------------------------------------------------- 2. EDD Unemployment Insurance (income)
PID = "prog_income_edd_ui_ca_001"
T = "2026-10-22T19:50:00-07:00"
EL = ("https://edd.ca.gov/en/unemployment/eligibility/", "Eligibility for Unemployment Benefits | EDD", "state_governing_agency", T)
FC = ("https://edd.ca.gov/en/unemployment/filing-a-claim/", "Filing a Claim | EDD", "state_governing_agency", T)
CU = ("https://edd.ca.gov/en/Unemployment/Contact_UI", "Contact Unemployment Insurance | EDD", "state_governing_agency", T)
CA = ("https://edd.ca.gov/en/unemployment/create-account", "Register and Create an Account | EDD", "state_governing_agency", T)
DE = ("https://edd.ca.gov/pdf_pub_ctr/de2320.pdf", "For Your Benefit: California's Programs for the Unemployed, DE 2320 Rev. 67 (1-24) | EDD", "state_governing_agency", T)
DEN = "Source: EDD pamphlet DE 2320 Rev. 67 (1-24), the current publication on edd.ca.gov."
rows = [
    ("program_name", "Unemployment Insurance (UI): weekly benefit payments for people who are fully or partially unemployed. For eligible claimants, the weekly benefit amount is between $40 and $450.", EL, None, "Exact amount depends on wages earned in the base period; Agent 4 must not estimate it."),
    ("organization", "Unemployment Insurance is administered statewide by the California Employment Development Department (EDD).", FC, None, None),
    ("geography[0]", "California", FC, None, "Statewide program: covers every California county, including Sacramento County."),
    ("eligibility_criteria[0]", "Have a Social Security number, or have authorization to work in the United States (if not a US citizen).", EL, None, None),
    ("eligibility_criteria[1]", "Have earned enough wages during the base period.", EL, None, "Wage thresholds are not stated on this page; unknown wages are not a mismatch."),
    ("eligibility_criteria[2]", "Be fully or partially unemployed.", EL, None, None),
    ("eligibility_criteria[3]", "Be unemployed through no fault of your own.", EL, None, "Shared test case: laid off (user statement). Final decision is EDD's."),
    ("eligibility_criteria[4]", "Be physically able and available to work.", EL, None, None),
    ("eligibility_criteria[5]", "Be looking for work each week.", EL, None, None),
    ("eligibility_criteria[6]", "Be ready and willing to accept work right away.", EL, None, None),
    ("eligibility_criteria[7]", "All claims have a one-week, unpaid, waiting period.", DE, None, DEN),
    ("eligibility_criteria[8]", "To keep receiving benefits, you must certify for benefits every two weeks.", DE, None, DEN),
    ("required_documents[0]", "Name (including all names used while working) and Social Security number.", DE, None, DEN + " Listed under 'To apply, we need your:'."),
    ("required_documents[1]", "Mailing and residence address (if different) and phone number.", DE, None, DEN),
    ("required_documents[2]", "Last employer's complete name, address (mailing and physical location), and phone number.", DE, None, DEN),
    ("required_documents[3]", "Last day worked and the reason you're no longer working (laid off, quit, fired, or left work because of a trade dispute).", DE, None, DEN),
    ("required_documents[4]", "Work history during the 18 months prior to applying, including out-of-state employment: all employers' names, dates employed, and wages earned.", DE, None, DEN),
    ("required_documents[5]", "State-issued driver license number or identification card number.", DE, None, DEN),
    ("required_documents[6]", "Citizenship status and whether you have the legal right to work in the United States; if authorized to work through USCIS, the title of the employment authorization document and information from it (such as Alien Registration Number, card number, expiration date).", DE, None, DEN),
    ("application_method[0]", "Apply online through myEDD (UI Online), which EDD describes as the fastest and most convenient way to apply for unemployment and manage a claim.", CA, None, "A myEDD account is needed first; the confirmation email link expires within 48 hours."),
    ("application_method[1]", "You must be at least 18 years old to apply online; applicants under 18 can apply by phone, fax, or mail.", CA, None, None),
    ("application_method[2]", "You may apply for benefits as soon as you are unemployed or your hours are reduced.", DE, None, DEN),
    ("contact[0]", "UI phone line (English and Spanish): 1-800-300-5616, 8 a.m. to 5 p.m. Pacific time, Monday through Friday, except California state holidays.", CU, None, "Also listed as the number for all other languages not listed separately."),
    ("contact[1]", "UI self-service line (English): 1-866-333-4606, 24 hours a day, 7 days a week.", CU, None, None),
    ("contact[2]", "UI TTY (deaf and hard of hearing): 1-800-815-9387.", CU, None, None),
    ("contact[3]", "UI lines in other languages: Armenian 1-855-528-1518; Cantonese 1-800-547-3506; Korean 1-844-660-0877; Mandarin 1-866-303-0706; Tagalog 1-866-395-1513; Vietnamese 1-800-547-2058.", CU, None, "Free interpreter services."),
    ("contact[4]", "myEDD / UI Online help: 1-833-978-2511 (option 1), or live chat in myEDD.", CA, None, None),
    ("processing_time", "It takes about three weeks to process a benefit application and make the first payment.", FC, None, "Published estimate, not a guarantee."),
    ("availability", "EDD currently accepts applications online through myEDD ('Apply Now').", FC, None, "Basis for availability = confirmed_open (published status only)."),
]
ui_ev = [ev_row(f"ev_eddui_{i:03d}", PID, *r) for i, r in enumerate(rows, 1)]
p, e = assemble({"program_id": PID, "program_name": "Unemployment Insurance (UI)", "organization": "California Employment Development Department (EDD)",
                 "category": "income_assistance", "subcategory": "unemployment_insurance", "geography": ["California"],
                 "availability": "confirmed_open", "verification_status": "verified"}, ui_ev)
programs.append(p); evidence += e

# ---------------------------------------------------------------- 3. Saint John's Housing Assistance Program (rental, direct intake)
PID = "prog_housing_saintjohns_sac_001"
T = "2026-10-22T19:50:00-07:00"
SJ = ("https://saintjohnsprogram.org/get-help/housing-assistance-program/", "Housing Assistance Program | Saint John's Program for Real Change (page text as published, rechecked Oct 25, 2026)", "local_provider_operating_intake", "2026-10-25T23:42:00-07:00")
rows = [
    ("program_name", "Housing Assistance Program: one-time assistance of up to $1,500 each for past-due rent, security deposits, and mortgage payments. Referrals to other programs (employment, childcare and others) are also offered.", SJ, None, "Operator's own page is the authority for its intake rules (TD 9.2: local provider for local operating/intake facts)."),
    ("organization", "Saint John's Program for Real Change (Sacramento nonprofit).", SJ, None, None),
    ("geography[0]", "Sacramento County", SJ, None, "Based on the residency rule in eligibility_criteria[0]."),
    ("eligibility_criteria[0]", "Have been a Sacramento County resident for at least six months.", SJ, None, None),
    ("eligibility_criteria[1]", "Fall under HUD low-income guidelines (not applicable for mortgage assistance).", SJ, None, "Dollar limits are not published on the page; unknown income is not a mismatch. Proof of income: required_documents[0]."),
    ("eligibility_criteria[2]", "Be able to pay a portion of the security deposit.", SJ, None, None),
    ("eligibility_criteria[3]", "Have a realistic plan to remain in current housing.", SJ, None, None),
    ("eligibility_criteria[4]", "Submit a valid rental or lease agreement.", SJ, None, None),
    ("eligibility_criteria[5]", "Ensure the property owner agrees to return all security deposits upon lease termination and completes a W-9 Federal Tax form.", SJ, None, None),
    ("eligibility_criteria[6]", "Not have used our Housing Assistance funds before or within the last two years.", SJ, None, None),
    ("required_documents[0]", "Provide proof of total household income.", SJ, None, None),
    ("required_documents[1]", "Submit a valid rental or lease agreement.", SJ, None, None),
    ("required_documents[2]", "W-9 Federal Tax form completed by the property owner.", SJ, None, "The page also says 'Provide all required documents' but does not list any others."),
    ("application_method[0]", "If you would like to apply for rental assistance in November please return back to this page on Monday, November 2nd.", SJ, "2026-11-02", "Shared test case: rent is due Nov 1, one day BEFORE applications reopen. Agent 6 must not present this as help for the Nov 1 payment."),
    ("application_method[1]", "Applications re-open for assistance to be delivered by the middle to end of November.", SJ, None, "Resolved Oct 25: the page says November. The 'February' wording captured on Oct 22 is no longer on the page."),
    ("contact[0]", "Phone: (916) 453-1482.", SJ, None, None),
    ("contact[1]", "Mailing address: 2443 Fair Oaks Blvd, #369, Sacramento, CA 95825.", SJ, None, "No online application form or email is published on the page."),
    ("processing_time", "If you applied for October funding, you will hear back from Saint John's Housing program within two weeks of your application date.", SJ, None, "Stated for the October cycle; recheck the wording for November on Nov 2."),
    ("availability", "We regret to announce that all of the funds for October 2026 have been exhausted.", SJ, None, "Basis for availability = temporarily_closed until applications re-open Nov 2 (published status only). Per Julia's rule, do not present as currently available."),
]
sj_ev = [ev_row(f"ev_sjhap_{i:03d}", PID, *r) for i, r in enumerate(rows, 1)]
# Slav, Oct 25: the reopening date must travel with the closure, so it gets its own availability row with effective_date.
sj_ev.append(ev_row("ev_sjhap_022", PID, "availability",
                    "If you would like to apply for rental assistance in November please return back to this page on Monday, November 2nd, when applications re-open for assistance to be delivered by the middle to end of November.", SJ, "2026-11-02",
                    "Reopening date for the closure in ev_sjhap_019 (same page). Shared test case: rent due Nov 1 is BEFORE this date, "
                    "so the plan must say 'reopens Nov 2, after your Nov 1 date'. Exact page wording (rechecked Oct 25)."))
sj_availability = "temporarily_closed"
# Nov 2 reopening (published): new IDs replace the October claims; old rows go to navigator/kb/history
# Page text checked Nov 2, 2026 15:30 PT: the October 'funds exhausted' / 'return on November 2nd' paragraph is gone,
# the delivery and 'hear back within two weeks' sentences are gone, and an 'APPLY HERE' link to an online form appeared.
SJ2 = (SJ[0], "Housing Assistance Program | Saint John's Program for Real Change (page text as published, checked Nov 2, 2026)", SJ[2], NOV2_T)
pending = ""
replace = {"ev_sjhap_014": ev_row("ev_sjhap_020", PID, "application_method[0]",
                                  "APPLY HERE (https://wkf.ms/4tjLVzi)", SJ2, "2026-11-02",
                                  "Verbatim link text from the page; the link opens the online application form. Replaces ev_sjhap_014 ('return back to this page on Monday, November 2nd'). The online form link appeared on the page on Nov 2. Rent in the Nov 1 test case was due before this date.", NOV2_STATUS),
           "ev_sjhap_019": ev_row("ev_sjhap_021", PID, "availability",
                                  "APPLY HERE", SJ2, "2026-11-02",
                                  "Verbatim link text, shown on the page on Nov 2, 2026. INFERENCE: availability = confirmed_open is inferred from what changed on the page: "
                                  "the October notice ('We regret to announce that all of the funds for October 2026 have been exhausted...') is no longer shown, "
                                  "and an 'APPLY HERE' link to the online application form is. The page has no sentence stating that applications are open. "
                                  "Published status only, not a funding guarantee. Replaces ev_sjhap_019 and ev_sjhap_022.", NOV2_STATUS),
           "ev_sjhap_022": None,  # reopening-date row: superseded by ev_sjhap_021 (same date)
           "ev_sjhap_015": None,  # 'delivered by the middle to end of November': sentence no longer on the page
           "ev_sjhap_018": None}  # 'hear back within two weeks' (October applicants): sentence no longer on the page
for e in sj_ev:  # contact[1] note said no online form was published; that changed on Nov 2
    if e["evidence_id"] == "ev_sjhap_017":
        e["notes"] = "Online application form: see application_method[0] (added to the page on Nov 2, 2026). No email is published."
SUPERSEDED += [e for e in sj_ev if e["evidence_id"] in replace]
sj_ev = [replace.get(e["evidence_id"], e) for e in sj_ev if replace.get(e["evidence_id"], e) is not None]
sj_availability = "confirmed_open"
p, e = assemble({"program_id": PID, "program_name": "Housing Assistance Program", "organization": "Saint John's Program for Real Change",
                 "category": "housing_assistance", "subcategory": "rental_assistance", "geography": ["Sacramento County"],
                 "availability": sj_availability, "verification_status": "verified"}, sj_ev)
programs.append(p); evidence += e

# ---------------------------------------------------------------- 4. Coordinated Access via 2-1-1 (housing, open route)
PID = "prog_housing_coordaccess_sac_001"
T = "2026-10-22T19:50:00-07:00"
AS = ("https://www.sacramentostepsforward.org/access-support/", "Access Support: Get Help with Homelessness | Sacramento Steps Forward (page last modified Oct 12, 2026)", "continuum_of_care_lead_agency", T)
HP = ("https://www.sacramentostepsforward.org/provider-hub/homelessness-prevention/", "Homelessness Prevention in Sacramento | Sacramento Steps Forward (page last modified Sept 10, 2026)", "continuum_of_care_lead_agency", T)
TS = ("https://www.211sacramento.org/211/housing-resources/", "Housing Resources | 2-1-1 Sacramento", "211_directory_discovery", T)
T3 = "2026-10-23T01:55:00-07:00"
CP = ("https://www.sacramentostepsforward.org/provider-hub/the-coordinated-access-system/", "The Coordinated Access System | Sacramento Steps Forward (page last modified Oct 6, 2026)", "continuum_of_care_lead_agency", T3)
HH = "https://www.sacramentostepsforward.org/provider-hub/homeless-housing-assistance-and-prevention-hhap-grants/"
rows = [
    ("program_name", "Sacramento Coordinated Access System: call 2-1-1 and press 8 for shelter, housing and other homelessness services, including homelessness prevention. A specialist works to determine availability and eligibility.", AS, None, "Access route, not a single fund. TD 20.3: describe the 211 referral process; never claim to reserve a slot."),
    ("organization", "Sacramento Steps Forward (Continuum of Care lead agency) with 2-1-1 Sacramento; 2-1-1 schedules appointments with approved Problem Solving Access Point (PSAP) agencies.", HP, None, "SSF states it is not a direct provider of housing resources or shelters."),
    ("geography[0]", "Sacramento County", AS, None, None),
    ("eligibility_criteria[0]", "There are not enough resources for everyone; the Coordinated Access System focuses on making sure those most at risk are served first.", AS, None, "No program-specific eligibility rules are published."),
    ("eligibility_criteria[1]", "Financial assistance through problem-solving services is limited and must directly lead to securing housing.", CP, None, "v0.3: replaces the v0.2 wording from the general prevention page, which was too vague to verify."),
    ("application_method[0]", "Call 2-1-1 and press 8. 2-1-1 assesses the needs and circumstances of callers and schedules appointments with approved PSAP agencies.", HP, None, None),
    ("contact[0]", "Toll-free: 1-844-546-1464. If 2-1-1 is hard to reach: 916-498-1000, still pressing 8.", AS, None, None),
    ("contact[1]", "Coordinated Access hours: Monday through Saturday, 7:00 a.m. to 7:00 p.m.", AS, None, "2-1-1 Sacramento's general referral line is listed as 24/7; the press-8 Coordinated Access line has the hours shown here. Another SSF page says CAS hours were updated starting October 1; this page (modified Oct 12, 2026) is the newer source."),
    ("contact[2]", "2-1-1 Sacramento: text your ZIP code to 898-211, or use the online chat.", TS, None, "General 2-1-1 referral channel (discovery source)."),
    ("availability", "The Coordinated Access line is published as operating: call 2-1-1 and press 8 (or 1-844-546-1464), Monday through Saturday, 7 a.m. to 7 p.m.", AS, None,
     "Basis for availability = confirmed_open: the access route is accepting calls (TD 9.2: published status only, not proof of funding or capacity). "
     "Funding context: the Sacramento CoC's state HHAP allocations include $2 million annually dedicated to keeping households housed through prevention efforts "
     "(SSF HHAP page, expenditures current through July 31, 2026: " + HH + "). Help for any one household is not guaranteed."),
    # v0.3 additions (appended so v0.2 IDs ev_cas_001-010 stay the same)
    ("eligibility_criteria[2]", "Anyone at risk of or experiencing homelessness, or who is fleeing or attempting to flee domestic violence, sexual assault, or human trafficking, and meets income requirements, is eligible for problem-solving services.", CP, None, "Answer to 'What makes someone eligible for a problem-solving access point (PSAP) referral?'. Income limits are not published; unknown income is not a mismatch."),
    ("required_documents[0]", "Additional verification documents (proof of income, eviction filings, etc.) are required for financial assistance.", CP, None, "Not needed just to call 2-1-1; needed if financial assistance is offered."),
]
ca_ev = [ev_row(f"ev_cas_{i:03d}", PID, *r) for i, r in enumerate(rows, 1)]
p, e = assemble({"program_id": PID, "program_name": "Sacramento Coordinated Access System (2-1-1, press 8)",
                 "organization": "Sacramento Steps Forward with 2-1-1 Sacramento",
                 "category": "housing_assistance", "subcategory": "eviction_prevention", "geography": ["Sacramento County"],
                 "availability": "confirmed_open", "verification_status": "verified"}, ca_ev)
programs.append(p); evidence += e

out = {"schema_version": "1.0", "note": "Contracts v1.1. Nov 2, 2026 update published. Built by navigator/kb/tools/build_kb.py.",
       "program_records": programs, "evidence_records": evidence}
target = os.path.join(KB_DIR, "kb_sacramento.json")
with open(target, "w", encoding="utf-8") as f:
    json.dump(out, f, indent=2, ensure_ascii=False)
# History is rebuilt from scratch every run (no appending), so rebuilding never duplicates rows.
hist = os.path.join(KB_DIR, "history", "superseded_evidence.json")
os.makedirs(os.path.dirname(hist), exist_ok=True)
with open(hist, "w", encoding="utf-8") as f:
    json.dump([dict(r, superseded_at=NOV2_T) for r in SUPERSEDED], f, indent=2, ensure_ascii=False)
print(f"{len(programs)} programs, {len(evidence)} evidence records -> navigator/kb/kb_sacramento.json")
