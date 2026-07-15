# Staged Issues — BitmojiGuy 5-Min Credit Tool
## Identified during project owner end-to-end run-through
## Each issue gets its own focused session. Do not bundle.

---

### Issue 1: Cash App payment workflow stuck at "payment pending verification"

**Observed:** When client selects Cash App as payment method, status shows "payment pending verification" indefinitely with no clear path to release. Unclear whether admin manually releases after confirming payment, or whether there is an automated mechanism.

**Why it matters:** Payment confirmation is a workflow blocker. If admin must manually release every Cash App payment, this is a scaling bottleneck. If consumer Cash App is being used (vs. Cash App Pay via Square), there is no merchant API providing payment confirmation webhooks, which forces manual handling.

**Proposed direction:** Determine which Cash App integration is in use. If consumer Cash App, evaluate either (a) email-parsing fallback to detect payment notifications and auto-release, or (b) migration to Cash App Pay through Square for proper webhook integration. Decision needs to balance implementation cost against admin time saved.

**Dependencies:** Stripe webhook flow (already working) as reference pattern.

**Priority:** Medium-high (blocks throughput at scale)

---

### Issue 2: Postage cost and workflow for high-volume client cases

**Observed:** For client cases with many items, postage cost becomes significant ($200+ in extreme cases). Workflow ambiguity around whether system handles postage directly or whether client is forwarded to a third-party postage service. If forwarded, system has no clear mechanism to confirm postage was actually completed.

**Why it matters:** Cost is a barrier for the consumer base this tool serves. Workflow ambiguity around postage completion creates audit trail gaps that undermine the dispute process — the dispute clock depends on documented mailing dates.

**Proposed direction:** Evaluate integration with a programmatic mailing API (Lob, Click2Mail, or similar) that handles print-stuff-mail-track in one operation and returns webhook confirmation of send and delivery. Alternative: if external-redirect remains the model, require tracking number entry as a workflow gate before status advances. Tied to Issue 6 — selective disputing reduces letter count substantially, which reduces postage exposure.

**Dependencies:** Issue 6 (letter volume optimization), Issue 4 (letter consolidation).

**Priority:** High (affects every client case)

---

### Issue 3: Gate screen readability — opaque overlay obscures content

**Observed:** On the gate screen, an opaque box element makes content difficult to read. Same readability issue was previously identified on the koi pond screen and was fixed there.

**Why it matters:** UI readability directly affects whether consumers can complete intake accurately. Intake accuracy is foundational to the honest-position framework.

**Proposed direction:** Apply same overlay/contrast fix that was applied to koi pond screen. Likely a CSS opacity or background-color adjustment on the overlay element.

**Dependencies:** None.

**Priority:** Medium (affects user experience but does not break functionality)

---

### Issue 4: Letter generator produces multiple letters per item under different statutes

**Observed:** For a single disputed item, the tool generates separate letters citing different statutes (FCRA letter, FDCPA letter, Metro 2 letter, state law letter) all going to the same recipient. This is statute-stacking against a single fact at a single recipient.

**Why it matters:** Statute-stacking is the textbook frivolous-dispute pattern that bureaus are trained to dismiss. It also signals credit repair organization activity, which can taint the consumer's entire file. This directly contradicts the locked architectural rule against stacking multiple statutory framings of the same factual claim.

**Proposed direction:** Refactor the letter generator to consolidate grounds into one letter per recipient per item. Multiple independent factual violations in one item are cited together within a single letter. Statute citations support the factual grounds rather than being the basis for separate letters. Recipient routing (bureau vs. collector) determines which letters exist, not statute selection.

**Dependencies:** Issue 6 (letter volume), Issue 9 (letter structure).

**Priority:** Critical (architectural violation, must fix before any user release)

---

### Issue 5: No distinction between "I don't recognize this" and "I know this is fraud"

**Observed:** Intake does not differentiate between consumer's certainty of identity theft (which requires FTC report and triggers §605B procedures) and consumer's non-recognition of an account (which is uncertainty, not a fraud claim). Letters generated may assert fraud when the consumer has not actually claimed certainty of fraud.

**Why it matters:** Asserting fraud the consumer cannot personally substantiate is potentially a false statement on a federal filing. It also weakens the dispute by triggering fraud-procedure requirements (FTC report) that the consumer has not satisfied. Honest-position framework requires letters to reflect the consumer's actual epistemic state, not an inflated version of it.

**Proposed direction:** Add a routing question in intake: "Do you have specific reason to believe this is identity theft, or do you not recognize the account but cannot rule out that it could be old/forgotten/sold to a different company?" Route certainty-of-fraud responses to identity theft workflow with FTC report integration. Route non-recognition responses to the standard FCRA dispute + parallel FDCPA validation workflow with honestly-uncertain language in the letters.

**Dependencies:** Issue 4 (recipient routing), Issue 9 (letter explanation layer).

**Priority:** High (architectural — required for honest-position compliance)

---

### Issue 6: Tool generates excessive letter volume per case (35-letter pattern)

**Observed:** For client cases with multiple negative items, tool produces letters for all of them, generating dispute volumes in the 30+ range. This produces the dispute-everything pattern that bureaus pattern-match to credit repair operations and dismiss via automated frivolous flagging.

**Why it matters:** Selective disputing on items with affirmed grounds is core architecture. Volume-based output indicates the tool is generating letters for items the consumer has not affirmed specific grounds on, or that the intake is allowing affirmation without sufficient specificity. Either path produces the wrong outcome — bulk dismissal by bureaus and CRO classification of the consumer's file.

**Proposed direction:** Audit the intake-to-letter pipeline to confirm that letters are only generated for items with consumer-affirmed specific grounds. If grounds affirmation in intake is too permissive (e.g., allowing checkbox-everything), tighten the affirmation requirement so each ground requires specific basis. Add UI feedback showing "Round 1 plan: X items, Y letters" with an explanation of why other items are not included.

**Dependencies:** Issue 4 (letter consolidation), Issue 5 (fraud vs. non-recognition).

**Priority:** Critical (the architectural spine of the product)

---

### Issue 7: No primary/secondary item ranking in letters

**Observed:** When a letter disputes multiple items on the same report, all items are presented as if equal weight. Bureau analysts can resolve the dispute by addressing the lowest-impact item (e.g., removing an inquiry) and marking the case complete, leaving the high-impact item (e.g., a $10K collection driving utilization to 100%) untouched.

**Why it matters:** This is a documented bureau behavior pattern that allows partial-resolution to close out disputes without addressing the items that actually affect the consumer's score. Without explicit ranking, the tool's letters give bureaus the escape hatch.

**Proposed direction:** Parsing engine computes per-item score impact based on balance, status, utilization contribution, recency, and account type. Letter generator includes an explicit ranking section near the top of each letter naming the primary item in dispute and stating that resolution of secondary items does not constitute resolution of the primary dispute. Round 2 MOV requests target whichever items the bureau corner-cut on in their round 1 verification.

**Dependencies:** Issue 6 (selective disputing), Issue 9 (letter structure).

**Priority:** High (significant strategic impact on outcome quality)

---

### Issue 8: No goal-driven optimization for time-pressured cases

**Observed:** Tool does not differentiate strategy based on consumer's actual goal and timeline (mortgage closing in 60 days, auto loan in 90 days, apartment application in 30 days, no deadline). All cases are treated with the same default strategy.

**Why it matters:** Time-pressured cases especially around mortgage closing have specific risks (active disputes can prevent closing on FHA/VA loans), and specific opportunities (some interventions like utilization reduction move scores faster than disputes). A consumer closing on a house in 60 days needs a fundamentally different campaign than a consumer with no deadline.

**Proposed direction:** Add goal-driven intake at the start of the user flow asking primary goal, timeline, budget, and any specific blocking issue. Optimizer composes round 1 plan based on these inputs. For mortgage cases specifically, surface the active-dispute warning and recommend lender consultation before disputing. Surface non-dispute interventions (utilization paydown, authorized user additions) where they would help more than disputes for the consumer's specific situation.

**Dependencies:** Issue 6 (selective disputing), Issue 7 (item ranking).

**Priority:** Medium (significant value-add but not blocking initial release)

---

### Issue 9: No explanation layer in delivered letters

**Observed:** Generated letters cite grounds without explaining the reasoning behind each ground. This produces letters that read as templated checklists rather than coherent factual positions, which makes them dismissable as frivolous and poorly-grounded.

**Why it matters:** Letters that explain the reasoning behind each ground demonstrate the consumer's informed engagement with the facts, which forces bureau analysts out of automated-dismissal mode and into substantive investigation. The explanation layer also serves as evidence of consumer education for any future regulatory or legal scrutiny.

**Proposed direction:** Letter generator produces seven-section structure: account audit (specific data points), discrepancies and inconsistencies, verification framework, consumer factual position, specific requests, explicit disclaimers, statutory grounding. Each section is auto-populated from intake and parsing engine output.

**Dependencies:** Issue 4 (letter consolidation), Issue 5 (honest position routing).

**Priority:** High (foundational to the math-first letter rule)

---

### Issue 10: Internal tool branding leaking into delivered documents

**Observed:** AE customer numbers and AE Labs references potentially appearing in dispute letters delivered to credit bureaus. Even if the tool is operating cleanly, internal branding on delivered documents creates attack surface.

**Why it matters:** Delivered documents going to bureaus, furnishers, and collectors should not contain internal tool identifiers, customer numbers, generator strings, or branding metadata. These create unnecessary attack surface for any future regulatory scrutiny or litigation, and signal credit repair organization activity to recipient analysts.

**Proposed direction:** Sanitization pass on every delivered document before output. Strip metadata (Producer, Creator, Author, Company fields in PDF/DOCX). Remove visible AE references, customer numbers, generator strings, and watermarks. Normalize filenames to non-identifying patterns. Regex scan output for internal token patterns before release. This applies to all delivered formats (PDF, DOCX, printed mail).

**Dependencies:** None (can be implemented independently).

**Priority:** Critical (delivered to real recipients, creates legal exposure if not addressed)
