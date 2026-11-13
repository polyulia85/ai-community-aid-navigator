# AI Community Aid Navigator
> *Helping families navigate financial crisis, one step at a time.*
### *Intelligent, Multi-Agent Crisis Intake, Verification & Actionable Relief Planning*

A team project developed through the **IBM SkillsBuild AI Experiential Learning Lab — Fall 2026**.

**Domain:** Government, Social Services & Community Welfare  
**Technology Stack:** IBM Granite, IBM watsonx (Orchestrate / Discovery), IBM Bob, Python, Open-Source RAG Frameworks  
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

## Development status

Under active development.

This repository is being prepared as the team's shared home for source code, technical documentation, agent contracts, resource data, and tests.

An integrated MVP, setup instructions, and demonstration materials will be added as they become available. Implemented features, mocks, and integration limitations will be documented explicitly.

## Quick Start & Demonstration

Clone the repository and run the master test and benchmark suite:

### Clone the repository
git clone: https://github.com/polyulia85/ai-community-aid-navigator.git

### Set up virtual environment
python -m venv venv

### Run the knowledge base builder
python3 navigator/kb/tools/build_kb.py
python3 navigator/kb/tools/validate_kb.py

### Run all tests
python3 -m unittest discover tests -v

## Team

- Iuliia Poliakova — Project Lead

- Sviatoslav Pechenevskyi — System Architecture & Integration

- Yogesh Kushwaha — Crisis Understanding & User Navigation

- Silver Sanchez Cardenas — Resource Retrieval, Matching & Verification

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

- M. Hisham Abbasi — Prioritization, Action Planning & Quality Validation

## Demo and documentation

Demo, documentation, and setup links will be added after the corresponding materials are uploaded and verified.

## Privacy

Do not upload credentials, API keys, or real user case data. Examples and demonstration cases must use synthetic data.
