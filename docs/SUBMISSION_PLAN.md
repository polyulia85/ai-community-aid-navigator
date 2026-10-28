# Submission Plan: Weeks 7–10 (Oct 27 – Nov 22, 2026)

**Status:** PROPOSED by Slav, Oct 27, 2026, for team review. Julia confirms owners and scope. Times are Pacific (PT) unless noted; ET = PT + 3 h.

## 1. Official IBM milestones (Week 7 checklist from our coach)

| By | IBM asks for | Our status today |
|---|---|---|
| Oct 27 | Mid-Program Milestone Checkpoint (unlocks the Career Fair) | Submitted by Julia for Oct 23. IBM sends no confirmation email, so worth confirming with the coach |
| Oct 29 | Implement technical features | Full 12-step cycle runs on all three components; open fixes listed in STATUS.md |
| Oct 30 | Improve reliability and robustness | Supervisor already handles timeouts, retries, rejected results and partial plans; to be demonstrated (§3) |
| **Oct 31** | **Test with real users** | **Not in our plan yet** (§4) |
| Nov 6 | Refine based on feedback | — |
| **Nov 8** | **Complete technical implementation and user validation** | — |
| Weeks 9–10 | Pitch Craft, Storytelling and Demo Flow session; documentation; finalize and submit | — |
| **Nov 22, 11:59 PM ET** | **Submissions close** | — |

**Week 7 calendar (posted Oct 27):** Oct 27 start building with IBM Bob (mandatory); Oct 28 continue in Bob, integrate key features; Oct 29 test, fix bugs, improve reliability; Oct 30 review progress, validate features, document updates and next steps. All teams must actively use IBM Bob. **Mandatory Learning Plan courses: by Wed, Oct 28.**

Nov 8 is the readiness milestone; Nov 22 is the hard deadline for submitting the materials.

## 2. What the final submission must contain

From the "Complete the learning lab" page and the Lab rules:
1. **Demo video, max 3 minutes, public link.** At least 90 seconds of the solution working on screen, with voice-over. **IBM Bob must be shown in use.**
2. **Problem and solution statement, max 500 words:** the problem, what the solution does, target users, how they use it, what is new.
3. **Technology statement:** exactly how and where we used IBM Bob, and watsonx.ai / watsonx Orchestrate if used.
4. **Public link to a working prototype.**
5. **Data rules:** a list of every public data source with its terms checked; no personal data, client data or social-media data.
6. **Bob sessions:** each of us exports our Bob task sessions (usage screenshot + markdown) to `bob_sessions/` in this public repository.
7. **Learning Plan:** each of us has every mandatory course and session (or recording) marked Completed — **mandatory courses by Wed, Oct 28** (Week 7 calendar). Needed for the credential.

Judging: four criteria, 5 points each — completeness and feasibility (including clear use of IBM technology), creativity and innovation, design and usability, effectiveness and efficiency.

## 3. Reliability demonstration (by Oct 30) — proposed owner: Slav

One run set, recorded in the run report and summarized in the channel:
- a hung agent (timeout, process stopped, plan still released);
- a malformed result (rejected, never treated as success);
- a result leaking an SSN-like number (rejected for privacy);
- a failed agent (dependents stop, unrelated steps continue);
- an Agent 10 FLAG (only the flagged card withheld after repair rounds).

These already work in tests; the demo turns them into evidence for the pitch.

## 4. Real-user test (Oct 31) — proposed owner of the protocol: Slav; testers: one per team member

The Lab rules forbid personal data, so "real users" means real people working through **synthetic story cards**, not telling their own story.

- **Testers:** 3–5 people outside the team; ideally one with social-work or 211 experience.
- **Session (15–20 min):** the tester enters a story card in their own words, answers the questions, reads the plan. We observe silently, then ask five questions.
- **What we measure:** can they name the first step; can they tell an official deadline from their own date; can they correct a misunderstood need; can they find where to reach a human; what was unclear. Plus time to the first step.
- **Consent:** short verbal or written consent; no names recorded; only answers go into the report.
- **If there is no UI by Oct 31:** test on the printed plan from a Supervisor run and call it a paper-prototype test.
- **Output:** a findings table → fixes by Nov 6 → one slide "What we changed after user testing".

## 5. Decisions we need this week (Julia)

1. Real-user test: format, testers, who leads.
2. Owners for the UI, application layer, database and the public prototype link (Master Development Plan: assigned Oct 26).
3. IBM integration: what moves to watsonx Orchestrate by Nov 8, and who does it. A local prototype alone does not count as completed IBM integration.
4. Where each of us uses IBM Bob, so the video and the technology statement can show it.
5. Progress statuses: six (Baseline) or five (Blueprint v1.1) — contracts decision 11.
6. Demo story: rent due Dec 1 (agreed); confirm the demo scenario list (5–7 synthetic cases).
7. Evidence freshness window for Agent 7 (rule Q7): after how many days a source check counts as too old — contracts decision 12.

## 6. Proposed timeline

| When | What | Proposed owner |
|---|---|---|
| Oct 27 | Contracts v1.1 published; repository structure uploaded; this plan | Slav |
| Oct 27–28 | Fixes from the Oct 26–27 reviews, done in IBM Bob, sessions exported to `bob_sessions/<name>/`; each part uploaded to the repository by pull request; re-run | Yogesh, Silver, Hisham, Slav |
| Oct 29 | Technical features: open v1.1 items in components; card titles with program names | Each owner |
| Oct 30 | Reliability demonstration (§3); presentation outline (Master Plan) | Slav; Julia |
| Oct 31 | Real-user test (§4) | All |
| Nov 2 | Saint John's page check and KB publish; re-run on the published KB | Silver; Slav |
| Nov 3 | Main integration done, remaining gaps documented; draft slides and demo scenario | All; Julia |
| Nov 4–6 | Fixes from user testing; stabilization; final presentation materials | All; Julia |
| Nov 7–8 | Acceptance tests T01–T12; rehearsal; **readiness milestone** | Julia (QA), all |
| Nov 9–20 | Pitch session; video recording; 500-word statement; technology statement; data-source list; Bob session exports | Team; owners to assign |
| Nov 20 | Internal submission deadline (two days of buffer) | Julia |
| **Nov 22** | **IBM deadline, 11:59 PM ET** | — |

## 7. Main risks

- **No public prototype yet** (required item 4). Needs an owner and hosting this week.
- **IBM integration** is not started; it affects the "clear use of IBM technology" score.
- **IBM Bob usage** must be real and exported by each of us; coins cannot be transferred between members (coach, Oct 26).
- **The demo date passes:** keep the demo story on Dec 1 and re-run after every change.
- **Workload:** most of us work on weekdays or have jobs; deadlines are agreed with the person doing the work, and post-freeze changes go through change requests.
