# v9 Context Intake Test — scope and limitations

The v8 field-fill-by-any-text flow was replaced with `intake_v9.js`, a **deterministic context intake prototype**. It keeps distinct facts for rent due date, rent amount, rent shortfall, and eviction notice; distinguishes household count, family relationships, and food-purchasing/preparation group; and distinguishes income, other income sources, and cash/savings. It asks follow-ups for missing facts and permits an explicit `unknown` response. The Situation Summary is editable and appears only after all minimum *prototype* fields have answers (including `unknown`).

**NOT DONE:** This is not live Agent 1/2 or Supervisor orchestration, not a verified sufficiency judgment for particular programs, and not personalized matching. Although `navigator/kb/kb_sacramento.json` is bundled, no validated ZIP-to-city/county or ZIP-to-service-area lookup is provided. ZIP is collected but NOT verified; do not infer Sacramento eligibility from a ZIP or user-provided city. A city and ZIP combination must be validated using an authoritative geography dataset, then cross-checked with verified KB program geography before recommendations. No personalized plan is generated; the Python bridge remains an unrelated synthetic diagnostic.

No answers are sent to the server or persisted by the intake test. Voice transcript review remains available. Do not enter sensitive personal data in this prototype.

Known pre-existing test failure in this archive: `tests/test_builders.py::TestWithKB::test_planning_package_availability_and_timing` expects Saint John's availability `temporarily_closed`, while current bundled KB produces `confirmed_open`. Do not silently change KB facts or the test without verifying the source.
