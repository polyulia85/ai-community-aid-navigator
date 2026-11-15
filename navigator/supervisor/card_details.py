"""Supporting evidence for released cards, separate from Agent 8's plan schema."""

_SECTIONS = {
    "eligibility_criteria": "conditions",
    "required_documents": "documents",
    "application_method": "steps",
    "contact": "contacts",
    "availability": "availability",
    "deadlines": "deadlines",
}


def for_released_cards(cards, claims, programs, evidence, needs=()):
    """Project only checked, program-scoped claims with matching verified evidence."""
    mortgage_needs = {n["need_id"] for n in needs if n.get("subcategory") == "mortgage_assistance"}
    details = {}
    for card in cards:
        program_id = card.get("program_id")
        if not program_id or program_id not in programs:
            continue
        program = programs[program_id]
        mortgage = bool(mortgage_needs.intersection(card.get("related_need_ids", [])))
        sections = {name: [] for name in _SECTIONS.values()}
        sources = {}

        def add_source(ref):
            record = evidence.get(ref)
            if (record and record.get("program_id") == program_id
                    and record.get("verification_status") == "verified"):
                sources[ref] = record
                return record
            return None

        for ref in card.get("source_refs", []):
            add_source(ref)
        for claim in claims:
            if (claim["program_id"] != program_id
                    or claim["verification_status"] != "verified"
                    or claim["claim_value"] in (None, "")):
                continue
            path = claim["field_path"]
            section = _SECTIONS.get(path.split("[", 1)[0])
            if section is None or (mortgage and path.startswith(("eligibility_criteria", "required_documents"))):
                continue
            refs = []
            for ref in claim["evidence_refs"]:
                record = evidence.get(ref, {})
                if (record.get("field_path") == path
                        and record.get("claim_value") == claim["claim_value"]
                        and add_source(ref)):
                    refs.append(ref)
            if refs:
                sections[section].append({
                    "value": claim["claim_value"],
                    "field_path": path,
                    "checked_at": claim["checked_at"],
                    "evidence_refs": refs,
                    "note": claim.get("issue"),
                })
        details[card["card_id"]] = {
            "program_name": program.get("program_name"),
            "organization": program.get("organization"),
            "subcategory": "mortgage_assistance" if mortgage else program.get("subcategory"),
            "geography": program.get("geography", []),
            **sections,
            "sources": list(sources.values()),
        }
    return details
