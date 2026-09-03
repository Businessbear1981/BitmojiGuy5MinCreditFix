# BitmojiGuy 5-Min Credit Fix — State

> **Status:** LIVE in test/demo mode on `bitmojiguycredittool.tech` (themed journey + full e2e); real charges blocked on Sean's live keys + PR #3 merge
> **Last updated:** 2026-08-31 (dispute engine + relief pathways, PR #5) · **Last verified:** 2026-08-31 (ruff clean, pytest 20/20, GitHub Actions `backend` + `frontend` both green on PR #5 @ `6be9923`)
> **One-liner:** $24.99 credit-dispute letters — detect from the customer's own report, one letter per bureau, mailed on an escalating postage ladder, encrypted at rest and hard-deleted within 24h.
> **Links:** `AGENTS.md` (charter/SOP) · `docs/decisions/` (ADRs) · `docs/compliance/croa-positioning.md` · GitHub Issues (work tracking)

This is the shared, repo-level context document — what is actually built, wired, and live.
It is updated **via PR, in the same PR as the change that moved the state**. Read it at
session start; never re-explain history that's already recorded here.

Facts carry confidence tags: `verified` (checked against ground truth on the stated date) ·
`asserted` (stated, not re-checked) · `assumed` (best guess).

---

## Live topology

| Service | URL | Status | Last verified |
|---|---|---|---|
| Frontend (Next.js, Vercel) | `bitmoji-guy5-min-credit-fix.vercel.app` | LIVE but serving the **old** build; redeploy from PR #3 pending | 2026-07-14 `asserted` |
| Backend (FastAPI, Railway) | to be (re)deployed from PR #3 — old Flask deploy is obsolete | pending | — |
| Database | Postgres (Railway or Supabase), **encrypted-ephemeral** per ADR-0002; SQLite in dev | pending provisioning | — |
| Mail (Lob) | integration built with postage ladder; needs `LOB_API_KEY` | `verified` code, `asserted` no key | 2026-07-18 |
| Stripe | Checkout + webhook built; live keys + webhook secret pending from Sean | `asserted` | — |

## Branch reality (read this before touching code)

- **`main`** = Sean's Jul-10 snapshot + merged agent-infra PR #2. Still carries the legacy Flask app and three competing frontends. `verified` 2026-07-18.
- **`ko/fastapi-takeover`** (pushed to `Kayo-11` fork, **PR #3 open**) = the canonical release candidate:
  - One FastAPI backend (`backend/`, evolved from Sean's BITMOJIGUY_CREDIT_ALL work) + one Next.js frontend (`frontend/`, from creditfix-next). Everything else deleted.
  - Field-level AES-256-GCM PII encryption at rest + 24h hard delete (ADR-0002 supersedes ADR-0001 hold-nothing).
  - Stateless HMAC terms tokens, in-memory PDF parse/generation, DB-derived fishbowl queues → multi-worker safe (`railway.toml` runs 2 uvicorn workers).
  - Frontend: typed API client, 5-step wizard wired end-to-end, consent gate, localStorage session resume, Stripe redirect polling, /terms /privacy /admin pages. $24.99 everywhere.
  - `ruff` clean · 14/14 pytest · eslint clean · `next build` clean · API e2e + browser walk green. `verified` 2026-07-18.

## What is real vs. mock

| Module | State |
|---|---|
| Report upload → parse (PyMuPDF) → dispute detection (Claude w/ keyword fallback) | **Real** |
| Letter generation (per-bureau + per-creditor, FCRA/FDCPA citations, in-memory PDF) | **Real** (Sean's perfected letter texts still pending — drop-in swap in `ae_creditfix/templates.py`) |
| Postage ladder (Lob: First Class r1 → Certified r2 → Certified+RR r3) | **Built**, needs `LOB_API_KEY` |
| Stripe Checkout ($24.99) + webhook + demo mode | **Built**, test/demo only until live keys |
| Manual pay (Cash App `$5mincreditfix` / Chime `$AELabsPay`): confirmation code → customer pays Sean directly → admin verifies + releases from /admin (unlock, mail r1, email PDF) | **Real** (2026-07-19), covered by tests; stairway polls and auto-advances on release |
| PII encryption at rest + 24h purge loop | **Real**, covered by tests |
| Terms/consent gate (FE + server-side token) | **Real** |
| Admin dashboard (/admin, key-gated stats) | **Real** |
| CI (GitHub Actions: ruff+pytest, eslint+build) | **Written**, not pushed — token lacks `workflow` scope |
| Relief pathways backend (`relief_pathways.py`, `student_loans.py`, `medical_relief.py`) — emits `student_loans` + `medical` sections, all-`.gov` links, anti-scam "no such thing as a debt-relief grant" block | **Built**, routes exist at `main.py:1073` (`GET /api/case/{id}/relief`) and `:1110` (`/relief/summary`) `verified` 2026-08-31. Logic not test-verified. |
| Relief frontend (`components/relief/ReliefPanel.tsx`) | **Built but NOT WIRED** — zero imports, zero render sites in `frontend/`. Invisible to customers today. `verified` 2026-08-31 |
| Signature capture (`components/sign/SignaturePad.tsx` + `main.py:500` `/sign`, `:536` `/signature-status`) | Backend **built**; frontend component **NOT WIRED** — zero imports. `verified` 2026-08-31 |
| `dispute_engine/` package (categories, tiers, legal_library, analyst, compose, letter_generator, adapter) | **Real and wired** — `main.py:30-31`, `/api/admin/templates` (`:1148`), `/api/admin/buckets` (`:1137`), `/api/case/{id}/letters` (`:571,601`); compose reached via `ae_creditfix/letters.py:18`. `verified` 2026-08-31 |
| Watcher backend (`watcher.py`, `watcher_loop.py`) | **Real and wired** — routes `main.py:928`–`:1023`, loop registered in lifespan `main.py:75`. `verified` 2026-08-31 |
| Scoring ledger (`outcomes.py`) | **Inert.** Write fns `record_dispute`/`record_result`/`record_score` have **zero callers**; `init_outcomes()` never called; `outcomes.db` is 0 bytes. See gap 10. `verified` 2026-08-31 |
| Calibration (`calibration.py`) | **Dead code** — nothing imports it. `install_into_scoring()` (`:141`) never runs, so the Beta posterior never replaces `scoring.PRIORS`. `verified` 2026-08-31 |

## Known gaps that will bite

1. **Launch inputs from Sean:** live Stripe keys + webhook secret, Lob API key, his perfected letter texts, and the merge of PR #3 (Kevin has no write access to this repo).
2. **Deploy logins:** Railway + Vercel CLI sessions on Kevin's machine are expired; re-login needed before infra work.
3. **Production Postgres not provisioned** — dev runs SQLite; `DATABASE_URL` must be set on Railway.
4. **CROA/state-CSO legal review pending** — see `docs/compliance/croa-positioning.md` action list; needed before scaling paid volume.
5. Old Vercel deployment still serves the pre-takeover frontend — must be repointed to `frontend/` on the new branch/main.
6. **Relief feature is dead code on the frontend.** Backend endpoints are live, but nothing renders `ReliefPanel`. Wiring it into `/koi-pond` (step 3, item review) needs: a `sessionId` in scope on that page (it currently reads items from a localStorage cache via `getDisputes()`, not the server — use `getApiSessionId()`), an `apiBase`, and typed helpers in `lib/api.ts`. `verified` 2026-08-31
7. **Relief types are duplicated, not shared.** `ReliefPanel` declares its own seven shapes locally and bypasses `lib/api.ts` with raw `fetch`. `lib/types.ts` has `medical_debt` in `BUCKET_LABELS` but **no `student_loan` bucket**, and `CaseStatus` has no `signed`/`signed_at` field. `verified` 2026-08-31
8. **No ADR for the relief/forgiveness module.** ADRs stop at 0002. A relief path that guides customers toward federal programs has CROA/state-CSO surface area and needs its own decision record alongside `docs/compliance/croa-positioning.md`.
9. ~~PR #5 is unverified.~~ **Resolved 2026-08-31 (`6be9923`).** ruff clean (was 270 errors), pytest 20/20, GitHub Actions `backend` and `frontend` both green. Still unexercised: no browser walk of the new relief UI, because it is not mounted (gap 6).
10. **The scoring ledger records disputes but never outcomes — every number is still `HAND_SET`.** Two thirds fixed:
    - `6be9923` — `scoring.py` no longer swallows the failure with a bare `except Exception: pass`; it catches `sqlite3.Error` and reports once per process that the ledger is unreadable, so the condition is visible instead of silent.
    - `7f027cf` — `init_outcomes()` now runs at startup beside `provenance.init_audit()`, and `_record_dispatched_disputes()` logs each item of a mailed round from both dispatch sites. Only real dispatches are recorded (demo mode fabricates its tracking numbers; those letters were never sent and must not enter the denominator). Covered by `test_outcome_ledger_records_a_dispatched_round`.
    - **Still open:** `record_result` and `record_score` have no callers **because no surface exists for anyone to report what happened to a dispute.** Every row sits at `outcome=NULL`, `removal_rate` returns nothing confident, and scoring correctly keeps using `PRIORS`. The denominator is now being built; the numerator does not exist. **This is a product decision, not a code fix** — most naturally the Watcher's 30/60/90 follow-up would ask the consumer, but nobody has decided that. Until then, every probability the engine shows is `HAND_SET` and must not be described as measured. `verified` 2026-08-31
11. **Student-loan findings never reach a dispute letter.** `student_loans.attach_findings` (`student_loans.py:901`) — the function that merges findings into `item['categories']` for the letter generator — has zero callers. Findings render only in the `/relief` JSON panel, which is itself unmounted (gap 6). Net effect: the student-loan work is invisible in both surfaces. `verified` 2026-08-31
12. **Forgiveness program directory is stale against 2026 rules.** `FORGIVENESS_PROGRAMS` (`student_loans.py:93-205`) has 7 entries and covers IDR only as a generic `idr_forgiveness`. The strings **RAP, SAVE, IBR, PAYE, ICR appear nowhere in the codebase.** SAVE ended by court order and RAP became the primary income-driven plan on 2026-07-01 — a customer-facing panel that names neither is out of date. Pell/federal grants: no coverage at all. `verified` 2026-08-31
13. **No application-packet or pre-fill export exists.** Relief content lives only as JSON on two GET endpoints; it never reaches a PDF, the print packet, or any downloadable artifact (`print_packet.py`, `letter_preview.py`, `pdf_gen.py` contain zero relief/student-loan/medical references). There is also **no Method, Plaid, or any external liability-discovery integration** anywhere in the repo — the only outbound HTTP client is Lob in `mail_service.py`. Prior session notes claiming a Method client shipped are wrong. `verified` 2026-08-31
14. **Two broken `__main__` demo blocks.** `dispute_engine/analyst.py:681` and `letter_generator.py:580` both `from .parsing_engine import parse_report` — **`parsing_engine.py` does not exist** — and both hardcode a dead path from a different machine (`C:\Users\sgill\Downloads\...`). Harmless at import, but running either module directly fails immediately. Delete or repair.
15. **Toolchain drift:** `.python-version` pins **3.11.0**, CI's `setup-python` uses **3.12**, and the working venv is **3.12.10**. Pick one. (Also: `ruff` is unpinned in `requirements-dev.txt`, so a ruff release can turn CI red without a code change. It was 0.16.5 on 2026-08-31.)
16. **The letter engine was mailing a letter with no statutory basis.** Found and fixed 2026-08-31 (`6be9923`), recorded because it was live in `b03e7d8` and is the kind of defect that must never recur. When no violation theory matched, `compose._shell_letter` produced an address block plus SECTION 4B and nothing else — 1,344 chars for the bureau letter, 1,293 for the creditor letter, `theory_count=0`, no statutory basis, no demand. That is what would have gone in the envelope. `test_full_lifecycle` had been failing on exactly this since the code landed, and the failure was real, not a stale assertion. Letters now carry SECTION 2 built from the recipient's baseline obligations plus each item's category citations. `verified` 2026-08-31
17. **Timestamp convention (read before adding a datetime).** Every timestamp in the backend is timezone-aware UTC as of `6be9923`. Do not use `datetime.utcnow()` or a bare `datetime.now()` — ruff's DTZ rules now fail CI on both. Database columns use the `UtcDateTime` decorator in `database.py`, which stores naive UTC on disk (unchanged format, no migration) and hands Python aware values on both SQLite and Postgres. Dates parsed out of a credit report carry no zone and are stamped UTC at the parse site.

## Active work

PR #3 (`Kayo-11:ko/fastapi-takeover` → `main`) is the release candidate. Next session: deploy runbook in `deploy/RUNBOOK.md` — provision Postgres, set env, deploy Railway + Vercel, then live-keys dry run when Sean surfaces.

**PR #5 (`sean/letters-engine` → `main`), opened 2026-08-31** — dispute engine + relief pathways + supporting backend modules. 38 files, +10,621/−374, commit `b03e7d8`.

- Adds `dispute_engine/` package; `student_loans.py`, `relief_pathways.py`, `medical_relief.py`; `equifax_parser.py`, `letter_preview.py`, `print_packet.py`, `signature.py`, `calibration.py`, `disclosures.py`, `outcomes.py`, `provenance.py`, `scoring.py`, `watcher.py`, `watcher_loop.py`; frontend `ReliefPanel.tsx` + `SignaturePad.tsx`.
- **Verification status:** local dev environment built from scratch this session (no `node_modules`, no venv existed; `python` is not on PATH on Sean's box — only the `py` launcher). Backend venv on Python 3.12.10, 45 packages, `pip install` exit 0. `npm install` exit 0. Both servers start: uvicorn `Application startup complete` on `127.0.0.1:8000`, Next.js 16.2.3 `Ready in 16.3s` on `:3000`. `verified` 2026-08-31.
- **Now verified (`6be9923`, 2026-08-31):** ruff clean, pytest 20/20, CI `backend` + `frontend` green. Two real defects were found and fixed on the way: the letter engine was producing letters with no statutory basis (gap 16), and the whole codebase used naive datetimes against a purge loop that compares them (gap 17). Still not exercised: no HTTP request against a running route, no browser walk.
- **Vercel:** the `bitmoji-guy5-min-credit-fix` preview deploys green; a second project, `bitmoji-guy5-min-credit-fix-et7l`, fails on every push and was already failing before this work. Nobody has looked at why.
- Backend boots with **no `.env`**, falling back to `config.py` defaults — Stripe/Lob/Anthropic paths are inert until keys are supplied.
- **Static audit run 2026-08-31** (read-only, two agents): import-graph reachability from `main.py`, stub/placeholder sweep, secret scan, `ast.parse` syntax check of all 22 new files. Results folded into the tables and gaps above. Headline: the code quality is high — **0 TODOs, 0 `NotImplementedError`, 0 `...` bodies, 0 bare `except:`, 0 syntax failures, 0 hardcoded secrets** across ~10,600 new lines — but four things are built and never called (gaps 6, 10, 11, and `calibration.py`).
- Next, in order (Iron Sharpens Iron: one fault, fixed, re-run from the top — not a backlog to work through): ~~(1) outcome ledger~~ done as far as code allows in `7f027cf`, remainder is Sean's call (gap 10); **(2) call `attach_findings` so student-loan findings reach letters — gap 11**; (3) wire `ReliefPanel` into `/koi-pond` + add the `student_loan` bucket to `lib/types.ts`; (4) refresh the forgiveness directory for RAP/post-SAVE — gap 12; (5) write the relief ADR; (6) browser walk before asking Kevin to merge.
- **Decision waiting on Sean:** where a dispute outcome gets captured. Without it the ledger accumulates disputes that never resolve, and no amount of volume will turn a prior into a measurement.
- **Worth a look while doing (2):** `guess_category` classifies "Not my account — no contract with collector" as `creditor_direct` rather than `collection` or `identity_error`, and only 14 of the categories map to a violation theory (`PARSER_CATEGORY_THEORIES` 9 + `CONDITIONAL_CATEGORY_THEORY` 5). Items outside that set reach no theory and fall to the fallback section. The fallback is now a valid letter (gap 16), but a valid letter is not the same as an argued one.

## Parsing real bureau reports — 2026-09-01

Measured against three real reports pulled by Sean for the same person in the same week. This section exists because the parser was previously validated only against a synthetic fixture, and the synthetic fixture flattered it.

**What the keyword scanner did on a real 91-page Experian export** (`verified` 2026-09-01): 20 items, furnisher present 0/20, date opened 0/20, account number 0/20. Its "creditors" were `Individual`, `Signer`, `Authorized User`, `Po Box 305,`, `Hays Mt` and `Account Number` — Responsibility *values*, address fragments and field *labels*. It found none of the 6 charge-offs, none of the 6 collections and none of the 30 hard inquiries, while reporting 4 `obsolete` and 4 `re_aging` items the file contains no date support for. On a real TransUnion file it identified `Fraud Victim Rights`, `Remedying The Effects Of Identity Theft` (a heading inside the FCRA legal notice) and the consumer's own name as creditors, producing 9 phantom `identity_theft` items.

**`experian_parser.py` (`dd89584`, wired `290b1fb`)** — written against the real export. 36 tradelines (matching the report header), 20 negative, 29 hard inquiries, 8 duplicates, 51 dispute items. Furnisher 22/22, account 22/22, opened 22/22. Six collections carry the original creditor. `verified` 2026-09-01.

**`canonical.py` (`fe48f1e`)** — one contract between every parser and the letter engine. Resolves field aliases once (`furnisher`/`target`/`account_name`, `reported`/`date_reported`), guarantees every field always present, converts money to `Decimal`, and sorts deterministically by severity. `field_coverage()` is the diagnostic: it shows in one table whether a parse is real, which is how the TransUnion gap was proven rather than guessed.

**Bureau disclosure differs materially — the data is NOT uniform.** Same consumer, same week: Equifax 33 accounts, Experian 36, TransUnion 38.

| Field | Equifax | TransUnion | Experian |
|---|---|---|---|
| **Date of first delinquency** | **33** | 10 | **absent** |
| Date closed / amount past due / actual payment | yes | yes | **absent** |
| Date of last activity, date major delinquency, months reviewed | **only EQ** | — | — |
| **Fall-off / removal date** | **absent** | 17 | 30 |
| **Furnisher address + phone** | **absent** | 212 | 36 |
| Balance history | absent | 13 | 18 |

18. **Equifax is the best single source, and no bureau is complete.** Equifax discloses the DOFD — the date § 1681c(a)(4) runs from, and the field the obsolescence and re-aging theories depend on. Experian discloses none of it; `implied_dofd` exists only to work around that absence. Conversely Equifax omits the fall-off date, which Experian and TransUnion publish. **They are complementary halves of one arithmetic: DOFD + 7 years should equal the stated fall-off date, and where it does not the bureau has contradicted its own maths on the face of its own disclosure.** That is a § 1681e(b) dispute requiring no assertion from the consumer. Ask for Equifax primary, Experian secondary (it is the only one that yielded the hard inquiries). `verified` 2026-09-01
19. **No TransUnion parser exists.** TU falls through to the keyword scanner and produces the garbage above. Its format is the richest of the three — `Pay Status` as a code rather than prose, original creditor on 10 accounts, a `Maximum Delinquency` note, and uniquely the **furnisher's mailing address and phone on every tradeline**, which is precisely what § 1681i(a)(7) entitles a consumer to demand. Roughly a day of work.
20. **`equifax_parser.py` had never been run against a real Equifax file until 2026-09-01.** It works: furnisher 20/20, account 20/20, opened 20/20, balance 20/20, DOFD 10/20. Unconfirmed whether that 10/20 reflects the 9 paid-and-closed student loans having no delinquency, or the `_field()` truncation bug from the static audit. Check before relying on it.

## End-to-end runs and the letter audit — 2026-09-03

**138 full journeys** against the local stack with Sean's own documents (ID front/back, a bank statement, all three bureau exports): 118 through a loop harness in three completed 20-run sequences, plus 20 individual runs during the fix cycle. `verified` 2026-09-03

**What that proved, and what it did not.** Every sequence produced a byte-identical letter once the case reference, timestamp and fingerprint were stripped, so the pipeline is deterministic and leaks no state between cases. It says nothing about whether the letters were *correct*: the harness checked structure — sections in order, no literal `Unknown`, signed, cites the FCRA — and structure was never the problem. **Reporting "20/20 clean" against a structural harness was the wrong measurement, and it held for 95 runs while the defects below were live.**

**Adversarial letter audit**, 5 dimensions, every finding re-verified against the letter file by an independent pass: **74 raised, 53 confirmed, 21 refuted, 0 invented quotes.** 10 critical, 23 high. `verified` 2026-09-03

Fixed:

21. **`date_of_first_delinquency` was backfilled from `date_opened`.** `adapter.py` read `item.get("dofd") or item.get("opened")`, and the Experian export contains the word "delinquency" zero times — it publishes `On Record Until` instead (30 occurrences). So **all 14 items in an Experian letter printed the open date under the DOFD label**: a fabricated date in the one field that sets the § 1681c clock, while the Equifax letter for the same accounts mailed the same day stated different dates. The pair contradicted each other in writing. No fallback now — an absent DOFD stays absent, and the matchers decline a theory they have no date for. `verified` 2026-09-03
22. **Uploads carried no document type**, so a bank statement sent to prove an address was parsed as a credit report and returned three dispute items built from its opening balance, closing balance and service fee — one asserting the account was not the customer's. `doc_type` is now required, only a report is parsed, and `docs_complete` needs all three kinds instead of flipping on the first upload.
23. **`to_affirmations` set the consumer's affirmations from the item's category.** Selecting a collection auto-set `no_validation_received`, so the letter read "Consumer affirms no validation was ever received from current collector" once per collector — for a consumer who had said no such thing. A collector's mailing log disproves it and the letter becomes the exhibit. Personal-knowledge affirmations now come only from explicit consumer input.
24. **The `collection` reason template opened by denying the account** — "I do not recognise this collection account and have no contractual relationship with…" — fired from a parser classification. It now disputes accuracy, completeness and verifiability: grounds the report supports, and grounds that survive the furnisher producing its log. Same for `personal_info`, which called a former address "not mine".
25. **The keyword scanner emitted unattributable items** whose furnisher was a section heading (`Monthly Payment`, `Addresses`) and whose account was `Unknown`. On the TransUnion export it produced 20 of them, which then *overwrote* Experian's good parse because the client cache was last-write-wins. Items now require an account identifier, each bureau keeps its own parse, and an unreadable report is refused with instructions rather than accepted empty.
26. **The per-round cap applied on one parser path only.** `MAX_ITEMS_PER_ROUND = 20` exists so a letter does not read as a mail-merge and invite a § 1681i(a)(3) frivolousness finding; the Experian path put 52 items in one envelope. Every path now returns through `_finalise`.
27. **The provenance watermark landed inside statutory citations.** Anchoring on every "period-space" put zero-width characters after `U.S.C.`, so `15 U.S.C. § 1681c` no longer matched a bureau's own text search for that section. Anchors now skip abbreviations and citation spans; the fingerprint still round-trips.
28. **Rate limits on any route carrying `{session_id}` were per-session, not per-IP** — slowapi keys on the concrete path by default. Measured: 20 watcher subscribes across 20 sessions never tripped a declared 10/hour, while 13 on one session tripped at the 11th. `key_style="endpoint"` fixed it, confirmed by the limit now binding at exactly 10 of 20 runs.
29. **Money was `float` end to end.** `money.py` holds one representation: Decimal in Python, exact decimal string on the wire and in storage. Float casts removed from `canonical.py` (which held Decimal then discarded the precision on output), `outcomes.py`, both parsers and `_fmt_money`.
30. **Case law is dark by construction, and now gated.** `get_verified_cases` reads the verified store, where 0 cases are active; the `federal_case_law` entries in `legal_library` carry a self-asserted `verified: True` that nothing checked, two of which reached real letters. `assert_citable` enforces appellate-or-higher from the citation string for anything added later. **The letters make no judicial claim at all**, which is the strongest position available — a statute cannot be distinguished or venue-shopped.

**Still open, and blocking a live launch:**

31. **The FDCPA is cited to a credit bureau.** `letter_generator` prints every statute a matched theory arms with no filter on recipient, so `validation_failure` puts § 1692g(b), § 1692e and § 1692f in a letter addressed to Experian — not a debt collector under § 1692a(6). One line also extends § 1692g(b) to say a debt "may not be collected **or reported**", which is not in the text. Correct law, wrong envelope: the engine already generates collector letters, and statutes need scoping by recipient.
32. **The re-aging theory is inverted.** It treats a DOFD *earlier* than the collection tradeline's open date as evidence of re-aging, and labels the ground `(strong)`. § 1681s-2(a)(5)(A) requires the original creditor's earlier delinquency date on a sold debt, so the letter asserts a violation on facts that show compliance — and a bureau can dismiss the section by pointing at the letter's own date table. The stated rule "the dates must be consistent across the transfer" exists in no statute.
33. **The consumer's return address is truncated to the street line** — no city, state or ZIP, though every source export carries them. The bureau cannot reply to the letter.
34. **Internal confidence scores print as letter text** — `(strong)`, `(moderate)`, `(weak)` — telling the bureau which items the consumer considers weak. Consumer-facing strategy copy addressed as "you" is also left in the mailed text.
35. **No consumer can say they do not recognise an account.** The review screen never asks for per-item affirmations, so `not_recognized`, `no_validation_received` and the fraud affirmations have no UI at all. Before fix 23 the software asserted them unasked; after it, nobody can assert them. **Not recognising a collection is a legitimate dispute and there is no box for it** — koi-pond needs to ask, per item.

**Synthetic profile suite** (`backend/tests/synthetic.py`) — 20 consumers, 5 per beta state, each a pure function of its seed so a failure reproduces from `make_profile(seed, state)` alone. Eight account archetypes, each recording the ground it exists to trigger, including a clean account that must produce no dispute. Two all-clean profiles both correctly produced 0 items and 0 letters — the negative case a load test cannot supply. Two suite assertions fired and traced to the harness rather than the product: `$100` is the correct quote of § 1681n statutory damages, and the zero-width characters sit at offset 25 of a 24-character citation, i.e. after it ends. `verified` 2026-09-03

**Deploy prerequisites, read off `config.py`, `database.py`, `provenance.py`, `outcomes.py`:**

- **Boot-critical on Railway** — `ENVIRONMENT=production` (exact lowercase), `PII_ENCRYPTION_KEY`, `TERMS_TOKEN_SECRET`, `CYPHER_SERVER_SECRET`, `ADMIN_KEY`. `config.py` raises on import without them and the deploy dies after 3 retries, reading like a broken image rather than a missing variable.
- **Fails silently, which is worse** — `DATABASE_URL` defaults to `sqlite:///./creditfix.db` on an ephemeral container, so the health check stays green while every redeploy wipes cases people paid for. `FRONTEND_URL` defaults to `localhost:3000`, which is where Stripe returns the customer after taking $24.99. `ALLOWED_ORIGINS` defaults to `localhost:3000`, so the browser is CORS-blocked on every call.
- **Supabase needs no manual SQL.** `init_db()` runs `create_all`, and `_ensure_columns()` ALTERs in the 18 later columns idempotently. Use the Supavisor pooler host with `sslmode=require`; the direct `db.<ref>.supabase.co` host is IPv6-only. `database.py` has no `pool_pre_ping`/`pool_recycle`, so the first request after an idle spell gets a dead connection and 500s.
- **Two stores bypass Postgres entirely.** `provenance.py` (`audit_chain.db`) and `outcomes.py` (`outcomes.db`) use raw `sqlite3` against local files, so on Railway both are wiped every deploy — losing the hash-chained audit log that is the evidence trail for every letter, and the outcome ledger that feeds `scoring`. They need a volume or a port to Postgres.
- `RATE_LIMIT_STORAGE_URI` is `memory://`: limits reset each deploy and are not shared across workers.
- **Vercel** — `NEXT_PUBLIC_API_URL` is inlined at build time; unset means the shipped bundle calls `localhost:8000` for every customer.
