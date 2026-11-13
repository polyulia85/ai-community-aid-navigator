"""New KB records, Nov 12, 2026 (owner: Silver). Food pantries, Salvation Army rent help, free tenant legal help.
Every claim was checked on the organization's own page on 2026-11-12 (Slav's Nov 10 drafts were re-checked, not copied blindly).
Called from build_kb.py:  from records_nov12 import build as build_nov12
Unknowns stay unknown: no invented phones, steps or funding status."""

T = "2026-11-12T10:30:00-08:00"

RC = ("https://rivercityfoodbank.org/emergency-food-distribution/", "Emergency Food Distribution | River City Food Bank (page modified Oct 29, 2026)", "local_provider_operating_intake", T)
RCPDF = ("https://rivercityfoodbank.org/wp-content/uploads/2025/09/RCFB_Both_Locations_Oct-Dec_2026_UPDATED.pdf", "River City Food Bank calendar, both locations, Oct-Dec 2026", "local_provider_operating_intake", T)
SA = ("https://www.salvationarmyusa.org/usa-western-territory/del-oro/sacramento-metro/food-pantry-social-services/", "Food Pantry & Social Services | The Salvation Army Sacramento Metro", "local_provider_operating_intake", T)
SF = ("https://www.sacramentofoodbank.org/find-food", "Find Food | Sacramento Food Bank & Family Services", "local_provider_operating_intake", T)
U = "2026-11-12T10:26:00-08:00"  # pages opened and copied by Silver
RCH = ("https://rivercityfoodbank.org/thanksgivingfood2026/", "Holiday Food Distribution & Closures | River City Food Bank", "local_provider_operating_intake", U)
SA2 = ("https://sacramento.salvationarmy.org/sacramento_metro/family-services/", "Family Services & Food Pantry | The Salvation Army Sacramento Metro", "local_provider_operating_intake", U)
EGH = ("https://elkgrovefoodbank.org/", "Elk Grove Food Bank Services (home page)", "local_provider_operating_intake", U)
EGF = ("https://elkgrovefoodbank.org/find-food/", "Find Food | Elk Grove Food Bank Services", "local_provider_operating_intake", U)
LO = ("https://lsnc.net/office/sacramento", "Sacramento office | Legal Services of Northern California", "local_provider_operating_intake", T)
LW = ("https://lsnc.net/what-we-do", "Our Services | Programs | Priorities | Legal Services of Northern California", "local_provider_operating_intake", T)
LC = ("https://lsnc.net/node/18", "How to Contact Us | Legal Services of Northern California", "local_provider_operating_intake", T)


def build(ev_row, assemble):
    programs, evidence = [], []

    def add(meta, prefix, rows):
        ev = [ev_row(f"{prefix}_{i:03d}", meta["program_id"], *r) for i, r in enumerate(rows, 1)]
        p, e = assemble(meta, ev)
        programs.append(p); evidence.extend(e)

    # ---- River City Food Bank: one record per site (same page, same rules) ----
    def river_city(site, pid, prefix, address, hours, extra):
        rows = [
            ("program_name", "River City Food Bank's Emergency Food Distribution has 2 locations: Midtown and Arden-Arcade. RCFB utilizes a Choice Food Model where each guest can select the items that best meet their needs.", RC, None, f"This record is the {site} site."),
            ("organization", "River City Food Bank (RCFB)", RC, None, None),
            ("geography[0]", "Sacramento County", RC, None, "Page: open 'to anyone experiencing food insecurity in Sacramento County'."),
            ("eligibility_criteria[0]", "All are welcome.", RC, None, "Page also: 'anyone experiencing food insecurity in Sacramento County'. Intake questions are optional."),
            ("eligibility_criteria[1]", "Each household may receive a full grocery offering once per week.", RC, None, None),
            ("eligibility_criteria[2]", "If returning a second time the same week, you will only be able to access USDA items (e.g., canned and dry goods).", RC, None, None),
            ("required_documents[0]", "ID is helpful, but not required.", RC, None, None),
            ("application_method[0]", "Walk in during distribution hours. Bring your own cart or bags to carry groceries.", RC, None, "No appointment or application is described on the page."),
            ("contact[0]", address, RC, None, None),
            ("contact[1]", hours, RC, None, None),
            ("contact[2]", "Phone: 916-446-2627", RCH, None, "Listed in the site footer next to both distribution sites' hours and addresses."),
            ("availability", "These sites are open four days a week to provide healthy, nutritious food to anyone experiencing food insecurity in Sacramento County.", RC, None, "Basis for availability = confirmed_open (published schedule). Closure dates are separate dated rows."),
            ("availability", "November 11 - Veterans Day (closed)", RC, "2026-11-11", "Year confirmed by the Oct-Dec 2026 calendar PDF (Nov 11 marked CLOSED)."),
            ("availability", "November 20 - Closed", RC, "2026-11-20", "CONFLICT: the distribution page and the holiday banner say Nov 20 is closed, but the holiday page's closure list reads 'Friday, Nov. 20 - Distribution' and the Oct-Dec 2026 calendar PDF does not mark Nov 20 closed. Call 916-446-2627 before going.", "conflicting"),
            ("availability", "November 25-27 - Thanksgiving Holiday (closed)", RC, "2026-11-25", "Year confirmed by the calendar PDF (Nov 25-27 marked CLOSED)."),
            ("availability", "Thursday, December 24 through Friday, January 1, 2027 (holiday closure)", RCH, "2026-12-24", "Holiday page states the years; the calendar PDF also marks Dec 24-31 CLOSED."),
            extra,
        ]
        add({"program_id": pid, "program_name": f"Emergency Food Distribution ({site})", "organization": "River City Food Bank",
             "category": "food_assistance", "subcategory": "food_pantry", "geography": ["Sacramento County"],
             "availability": "confirmed_open", "verification_status": "verified"}, prefix, rows)

    river_city("Midtown", "prog_food_rivercity_midtown_sac_001", "ev_rcfbmt",
               "1800 28th St. Sacramento, CA 95816", "Tuesday & Thursday: 10:30am - 1:30pm",
               ("availability", "Holiday distribution: Tuesday, November 24, 2026, 10:30am - 1:30pm, Midtown Distribution, 1800 28th Street", RCH, "2026-11-24", None))
    river_city("Arden-Arcade", "prog_food_rivercity_arden_sac_001", "ev_rcfbar",
               "(The Center at St. Matthew's) 2300 Edison Ave. Sacramento, CA 95821", "Wednesday & Friday: 10:30am - 1:30pm",
               ("availability", "Holiday distribution: Saturday, November 21, 2026, 10:30am - 1:30pm, Arden Distribution (The Center at St. Matthew's)", RCH, "2026-11-21", None))

    # ---- Salvation Army Sacramento Metro: Client Choice Food Pantry ----
    who = "Seniors, individuals with disabilities, low-income or no-income households, and homeless households in Sacramento County."
    add({"program_id": "prog_food_salvationarmy_pantry_sac_001", "program_name": "Client Choice Food Pantry",
         "organization": "The Salvation Army Sacramento Metro", "category": "food_assistance", "subcategory": "food_pantry",
         "geography": ["Sacramento County"], "availability": "confirmed_open", "verification_status": "verified"}, "ev_sapantry", [
        ("program_name", "Through our Client Choice Food Pantry, families can shop with dignity and select the items they need most.", SA, None, None),
        ("organization", "The Salvation Army Sacramento Metro", SA, None, None),
        ("geography[0]", "Sacramento County", SA, None, "From the 'Who Qualifies' section."),
        ("eligibility_criteria[0]", who, SA, None, "The page's 'Who Qualifies' section applies to both pantry and family services."),
        ("eligibility_criteria[1]", "Income guidelines are based on The Emergency Food Assistance Program.", SA, None, "No dollar limits on the page; unknown income is not a mismatch."),
        ("contact[0]", "Location: 3213 Orange Grove Ave., North Highlands, CA 95660", SA, None, None),
        ("contact[1]", "Food Pantry Schedule: Tuesday, Wednesday, Thursday 9AM - 1PM", SA, None, "A staff member's email is on the page; left out on purpose (personal address)."),
        ("contact[2]", "North Highlands Family Services: (916) 678-4010", SA2, None, "Family services page. Same page: 'Food Boxes & Fresh Produce: Tuesday, Wednesday, Thursday from 9AM - 1PM'."),
        ("contact[3]", "Food for Seniors: 60 years old +, 4th Monday & Thursday, 9AM - 1PM", SA2, None, None),
        ("availability", "Food Pantry Schedule: Tuesday, Wednesday, Thursday 9AM - 1PM", SA, None, "Basis for availability = confirmed_open (published schedule)."),
    ])

    # ---- Salvation Army Sacramento Metro: Rent & Utility Assistance (rent part) ----
    add({"program_id": "prog_housing_salvationarmy_rent_sac_001", "program_name": "Rent & Utility Assistance (rental assistance)",
         "organization": "The Salvation Army Sacramento Metro", "category": "housing_assistance", "subcategory": "rental_assistance",
         "geography": ["Sacramento County"], "availability": "unknown", "verification_status": "needs_review"}, "ev_sarent", [
        ("program_name", "Helping families stay housed means covering essential rental and utility costs keeping a roof over their heads.", SA, None, "Scope here: rental assistance only (utility, move-in and motel help on the same page are out of scope for now)."),
        ("organization", "The Salvation Army Sacramento Metro", SA, None, None),
        ("geography[0]", "Sacramento County", SA, None, None),
        ("eligibility_criteria[0]", who, SA, None, None),
        ("eligibility_criteria[1]", "Rental Assistance - Requires a 3-day pay or quit notice.", SA, None, "Criterion for Agent 4: if has_written_eviction_notice is unknown, keep potential_match, never a mismatch."),
        ("eligibility_criteria[2]", "Income guidelines are based on The Emergency Food Assistance Program.", SA, None, "No dollar limits on the page."),
        ("required_documents[0]", "A 3-day pay or quit notice.", SA, None, None),
        ("contact[0]", "North Highlands Family Services: 3213 Orange Grove Ave., North Highlands, CA 95660", SA2, None, "The food pantry & social services page writes the rent-help address as '3213 Orange Grove Ave, Sacramento' (no ZIP); same street address."),
        ("contact[1]", "Rent & Utility Assistance Schedule: Monday, Tuesday, Wednesday, Thursday 9AM - 4PM", SA, None, "No application steps are published."),
        ("contact[2]", "North Highlands Family Services: (916) 678-4010", SA2, None, None),
        ("eligibility_criteria[3]", "Assistance programs are based on residence, income qualifications and availability of funding.", SA2, None, None),
        ("availability", "Rent & Utility Assistance Schedule: Monday, Tuesday, Wednesday, Thursday 9AM - 4PM", SA, None, "Basis for availability = unknown: office hours are published, but the family services page says help depends on 'availability of funding' and no current status is given.", "needs_review"),
    ])

    # ---- Sacramento Food Bank & Family Services: Food Finder (county-wide partner network) ----
    add({"program_id": "prog_food_sfbfs_foodfinder_sac_001", "program_name": "Food Finder (partner food distribution sites)",
         "organization": "Sacramento Food Bank & Family Services", "category": "food_assistance", "subcategory": "food_pantry",
         "geography": ["Sacramento County"], "availability": "confirmed_open", "verification_status": "verified"}, "ev_sfbfs", [
        ("program_name", "Use the Food Finder tool below to locate a food distribution site near you. Our network of 112 partners are here to help.", SF, None, "Access route to many sites across the county, not one site."),
        ("organization", "Sacramento Food Bank & Family Services", SF, None, None),
        ("geography[0]", "Sacramento County", SF, None, "The page's holiday list covers 'holiday food distributions in Sacramento County'."),
        ("eligibility_criteria[0]", "It's always recommended that you contact the location before visiting to confirm hours, eligibility requirements.", SF, None, "Eligibility is set by each distribution site."),
        ("application_method[0]", "Use the Food Finder on https://www.sacramentofoodbank.org/find-food to locate a distribution site near you.", SF, None, None),
        ("contact[0]", "Main line: (916) 456-1980", SF, None, None),
        ("contact[1]", "CalFresh Outreach: (916) 779-0052", SF, None, "Help applying for CalFresh."),
        ("contact[2]", "Office: 1951 Bell Avenue, Sacramento, CA 95838", SF, None, "Organization office, not a distribution site."),
        ("availability", "Due to rising demand, please plan for longer lines and wait times at all food distribution sites at this time.", SF, None, "Basis for availability = confirmed_open: the finder and partner network are operating; each site's hours vary."),
    ])

    # ---- Elk Grove Food Bank Services (south county) ----
    eg_hours = ("Monday through Friday: 9:00 am to 2:00 pm; 1st Thursday of the month: open 12:30 pm to 2 pm; "
                "4th Wednesday of the month: open 12:30 pm to 2 pm. Closed on most major holidays and Saturdays / Sundays.")
    add({"program_id": "prog_food_elkgrove_foodbank_sac_001", "program_name": "Elk Grove Food Bank Services (food distribution)",
         "organization": "Elk Grove Food Bank Services", "category": "food_assistance", "subcategory": "food_pantry",
         "geography": ["Sacramento County"], "availability": "confirmed_open", "verification_status": "verified"}, "ev_egfbs", [
        ("program_name", "Elk Grove Food Bank Services serves food insecure individuals in the Elk Grove Region and south county. All services are provided at no cost.", EGH, None, None),
        ("organization", "Elk Grove Food Bank Services (EGFBS)", EGH, None, None),
        ("geography[0]", "Sacramento County", EGH, None, "Home page: 'the Elk Grove Region and south county'. Only the home-delivery Wellness Bag program lists ZIPs (95624, 95757, 95758, 95828, 95829)."),
        ("eligibility_criteria[0]", "Our programs serve low-income families, children, seniors, chronically ill, migrant families, disabled, working poor, unemployed and the homeless.", EGH, None, None),
        ("eligibility_criteria[1]", "All services are provided at no cost.", EGH, None, None),
        ("contact[0]", "Physical address: 9888 Kent Street, Elk Grove, CA 95624", EGH, None, None),
        ("contact[1]", "Phone: 916-685-8453", EGH, None, None),
        ("contact[2]", "We serve our clients: " + eg_hours, EGH, None, None),
        ("contact[3]", "CalFresh Coordinator: (916) 685-8453 x 205", EGF, None, "Help applying for CalFresh."),
        ("availability", "We serve our clients: " + eg_hours, EGH, None, "Basis for availability = confirmed_open (published hours). During extreme heat (forecast of 100 degrees) the warehouse and food distribution close at noon."),
    ])

    # ---- Legal Services of Northern California, Sacramento office: free tenant legal help ----
    add({"program_id": "prog_housing_lsnc_sac_001", "program_name": "Free legal help for tenants (Sacramento office)",
         "organization": "Legal Services of Northern California (LSNC)", "category": "housing_assistance", "subcategory": "housing_legal_aid",
         "geography": ["Sacramento County"], "availability": "confirmed_open", "verification_status": "verified"}, "ev_lsnc", [
        ("program_name", "LSNC provides free civil representation to low-income clients.", LC, None, None),
        ("organization", "Legal Services of Northern California, Sacramento office", LO, None, None),
        ("geography[0]", "Sacramento County", LO, None, "Office page: 'Serving low-income clients in Sacramento county.'"),
        ("eligibility_criteria[0]", "Serving low-income clients in Sacramento county.", LO, None, "No dollar limits on the page; unknown income is not a mismatch."),
        ("eligibility_criteria[1]", "Service priorities include tenants rights, evictions and lock outs.", LW, None, None),
        ("eligibility_criteria[2]", "LSNC does not provide rental assistance or other monetary payments.", LW, None, "Legal help only; pair with a rent-help program."),
        ("application_method[0]", "Call during intake hours: Monday, Tuesday, Thursday and Friday, 8:30 a.m. to 12 p.m., 1 p.m. to 5 p.m. or until full. The list can fill quickly; call when the office opens.", LO, None, None),
        ("contact[0]", "Phone: (916) 551-2150", LO, None, None),
        ("contact[1]", "After-hours intake (leave a message): (866) 815-5990", LO, None, None),
        ("contact[2]", "First contact by email for people who are deaf, hard of hearing or have trouble using the phone: sacramento-office@lsnc.net", LO, None, "Office address, not a personal one."),
        ("contact[3]", "Address: 515 - 12th Street, Sacramento, CA 95814", LO, None, "NEEDS REVIEW: the site footer and 'How to Contact Us' list the Executive Office at 517 - 12th Street; the Sacramento office page says 515. Call (916) 551-2150 to confirm the walk-in address.", "needs_review"),
        ("availability", "Intake: Monday, Tuesday, Thursday and Friday, 8:30 a.m. to 12 p.m., 1 p.m. to 5 p.m. or until full.", LO, None, "Basis for availability = confirmed_open (published intake hours); help is not guaranteed."),
    ])
    return programs, evidence
