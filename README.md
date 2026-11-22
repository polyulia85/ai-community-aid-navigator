# AI Community Aid Navigator
> *Helping families navigate financial crisis, one step at a time.*
### *Intelligent, Multi-Agent Crisis Intake, Verification & Actionable Relief Planning*

A team project developed through the **IBM SkillsBuild AI Experiential Learning Lab — Fall 2026**.

**Domain:** Government, Social Services & Community Welfare  
**Technology Stack:** IBM Bob (development environment), IBM Granite on watsonx.ai (Agent 1 can read the user's story with Granite, with deterministic rules as a fallback), Python standard library, local Sacramento knowledge base.  
**Pilot Target:** Sacramento County, California 
**Contract Baseline:** Shared JSON Contracts v1.0 (Frozen Baseline)

## Project overview

Families facing an unexpected financial crisis often need to navigate multiple assistance programs with different eligibility requirements, application processes, and documentation.

AI Community Aid Navigator is being developed to help users describe their circumstances, identify potentially relevant community resources, and build a personalized action plan.

## Pilot scope

The initial pilot focuses on **Sacramento, California**, with priority given to housing/rent assistance and food support.

* Planned user experience

* Describe your situation in your own words.

* Answer clarifying questions and confirm the summary.

* Review relevant assistance programs, supporting sources, and eligibility uncertainties.

* Receive a prioritized action plan.

* Track progress and update the plan as circumstances change.

> **Operational Boundary:** Users apply to assistance programs independently. The navigator does **not** directly submit applications or guarantee eligibility or financial assistance.

## Status

Working local prototype. The web app (`app_layer/`) runs on the real Python Supervisor and agents:

* Conversation → Situation Summary → Action Plan → My Case, with progress saved in the browser tab (it survives a page reload).
* Agents 1–8 and 10 are integrated. Agent 9 (Personal Navigation) is deferred by design (Shared JSON Contracts, section 8).
* Agents work with deterministic rules. Agent 1 can also read the user's story with IBM Granite on watsonx.ai when credentials are set (see *Run the app*); without them it uses the rules.
* Programs come from the local Sacramento knowledge base (see *Knowledge base* below). If a user reports threats or violence, the app shows a safety notice with 9-1-1 and 988.
* Not in this build: account registration, server-side case storage, live re-checking of sources, and real email delivery (the email flow is simulated).
* IBM Bob task exports for each team member are in [`bob_sessions/`](bob_sessions/).

More detail: [STATUS.md](STATUS.md) and [INTEGRATION_REPORT.md](INTEGRATION_REPORT.md) (in Russian).

## Run the app

Requires Python 3.11 or newer. No extra packages are needed.

```sh
git clone https://github.com/polyulia85/ai-community-aid-navigator.git
cd ai-community-aid-navigator
python -m app_layer.server
```

Open http://127.0.0.1:8765/ in your browser. If port 8765 is busy, run `python -m app_layer.server --port 18765` and open http://127.0.0.1:18765/. (On macOS and Linux, use `python3` if `python` is not available.)

Use fictional data only. A test story for **Conversation**:

> I live in Sacramento ZIP code 95823 with my two children. I lost my job. I need food this week and help paying $1,450 rent.

Answers to the follow-up questions: monthly income `$900`; household size `3`; `Yes` to the lease question and `No` to the written-notice question; shortfall `400`; rent due `2026-12-01`; `Yes` to "will food run out today or tomorrow"; money available now `20`. Then review the **Situation Summary**, click **Confirm Information**, and open the **Action Plan** and **My Case**.

Optional — IBM Granite for Agent 1: set the environment variables `WATSONX_APIKEY` and `WATSONX_PROJECT_ID` before starting the server (details in [`navigator/agents/agent_1_2/`](navigator/agents/agent_1_2/)). Without them, Agent 1 uses its rules.

A Russian-language version of these instructions is in [START_HERE.md](START_HERE.md).

## Run the tests

From the repository root:

```sh
python -I -m unittest discover -s tests -t .
```

Expected result: `Ran 659 tests ... OK`.

Rebuild and validate the knowledge base:

```sh
python navigator/kb/tools/build_kb.py
python navigator/kb/tools/validate_kb.py
```

## Demo video

Watch the 3-minute demo on YouTube: [AI Community Aid Navigator | IBM SkillsBuild Project Demo](https://www.youtube.com/watch?v=ClAavXxaMys)

## Team and roles

- Iuliia Poliakova — Project Lead (concept, architecture, web app and its integration with the agents)

- Sviatoslav Pechenevskyi — System Architecture & Integration (Python Supervisor, Shared JSON Contracts)

- Yogesh Kushwaha — Crisis Understanding & User Navigation (Agents 1 and 2)

- Silver Sanchez Cardenas — Resource Retrieval, Matching & Verification (Agents 3–5, Sacramento knowledge base)

- M. Hisham Abbasi — Prioritization, Action Planning & Quality Validation (Agents 6, 7, 8 and 10)

## Knowledge base

`navigator/kb/kb_sacramento.json` is the local knowledge base for Sacramento County. As of Nov 12, 2026 it covers **11 programs** and **200 evidence records** across food assistance, housing assistance, and income assistance:

| Program | Category | Availability |
|---|---|---|
| CalFresh | food_assistance / calfresh_benefits | confirmed_open |
| Unemployment Insurance (EDD) | income_assistance / unemployment_insurance | confirmed_open |
| Saint John's Housing Assistance Program | housing_assistance / rental_assistance | confirmed_open |
| Sacramento Coordinated Access System (2-1-1, press 8) | housing_assistance / eviction_prevention | confirmed_open |
| Emergency Food Distribution — Midtown (River City Food Bank) | food_assistance / food_pantry | confirmed_open |
| Emergency Food Distribution — Arden-Arcade (River City Food Bank) | food_assistance / food_pantry | confirmed_open |
| Client Choice Food Pantry (Salvation Army Sacramento Metro) | food_assistance / food_pantry | confirmed_open |
| Rent & Utility Assistance — rental assistance (Salvation Army Sacramento Metro) | housing_assistance / rental_assistance | unknown (funding depends on availability) |
| Food Finder — partner food distribution sites (Sacramento Food Bank & Family Services) | food_assistance / food_pantry | confirmed_open |
| Elk Grove Food Bank Services (food distribution) | food_assistance / food_pantry | confirmed_open |
| Free legal help for tenants (Legal Services of Northern California, Sacramento office) | housing_assistance / housing_legal_aid | confirmed_open |

Sources and terms of use: `navigator/kb/SOURCES.md` (32 source links, 15 sites, 13 owners as of Nov 12, 2026).

KB is rebuilt by running `python3 navigator/kb/tools/build_kb.py` from the repo root. Validation: `python3 navigator/kb/tools/validate_kb.py`.

## Privacy

Do not upload credentials, API keys, or real user case data. Examples and demonstration cases must use synthetic data.
