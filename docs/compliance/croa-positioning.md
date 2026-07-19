# CROA Positioning Memo — AE 5-Min Credit Fix

**Status:** Working memo, not legal advice. Reviewed by: (pending — engage a consumer-finance attorney before scaling paid volume.)
**Last updated:** 2026-07-18

## The question

The Credit Repair Organizations Act (15 U.S.C. §1679) regulates any person who
sells services "for the express or implied purpose of improving any consumer's
credit record, credit history, or credit rating." CROA imposes, among other
things: a written contract, a 3-day cancellation right, mandatory disclosures,
and — critically — **a ban on charging before services are fully performed**
(§1679b(b)). Many states (including Texas and California, two of our beta
states) layer on registration/bonding requirements for "credit services
organizations."

Does 5-Min Credit Fix fall inside that definition?

## Our positioning: self-help document preparation software

The product is deliberately built as a **software tool the consumer operates
themselves**, not a service performed on the consumer's behalf:

1. **The consumer does the work.** They upload their own report, select which
   items to dispute, review each generated letter, and authorize the mailing.
   We never contact bureaus or furnishers to advocate, negotiate, or follow up.
2. **No outcome claims.** The UI, marketing copy, and Terms explicitly state we
   do not promise any change to a credit report or score, and that consumers
   can do all of this themselves for free. (CROA's core targets are deceptive
   outcome promises and advance fees for undelivered results.)
3. **Charge only at delivery.** The $24.99 charge occurs at the moment the
   letter packet is generated and delivered (download + email + round-1 mail
   submission). There is no ongoing retainer, subscription, or promise of
   future work — the thing paid for is fully performed at purchase.
4. **Good-faith disputes only.** The consent gate requires the user to affirm
   the items they dispute are inaccurate to their knowledge. Letters assert
   FCRA §611 rights (reinvestigation of disputed information), not
   jamming/frivolous-dispute tactics.
5. **No data retention.** All PII is encrypted at rest and hard-deleted within
   24 hours (ADR-0002), which both reduces breach exposure and reinforces that
   we are not an ongoing "organization" managing the consumer's credit file.

This places us alongside tax-prep software, will-drafting software, and
letter-template products rather than credit repair firms.

## Honest risk assessment

- **The definition is broad and courts have read it broadly.** Some courts
  have applied CROA to software and advice products. "We're just software" is
  a strong argument, not a guaranteed safe harbor.
- **State CSO statutes vary.** TX (Fin. Code ch. 393) and CA (CCRAA,
  Civ. Code §1789.10+) have their own definitions and registration/bonding
  regimes; some exempt pure software/publishers, some are murkier. Beta-state
  selection should be revisited with counsel.
- **Marketing is the biggest lever.** The product name ("Credit Fix") and any
  copy implying score improvement pull toward CROA coverage. Copy must stay on
  "prepare and mail your dispute letters," never "fix/boost/repair your
  credit." Flag: the brand name itself should be discussed with counsel.

## Required before scale (action list)

- [ ] Engage consumer-finance counsel for a written opinion (CROA + TX/CA/WA CSO statutes)
- [ ] Counsel review of Terms, Privacy, consent-gate language, and all marketing copy
- [ ] Revisit brand name implication ("Credit Fix") with counsel
- [ ] Add 3-day post-purchase refund policy regardless of CROA applicability (cheap goodwill + risk buffer)
- [ ] Document the "charge at delivery" flow (Stripe event → letters already generated) as evidence

## Operating rules for everyone touching this product

1. Never promise, imply, or testimonial-ize score improvements.
2. Never charge before the letter packet is generated and delivered.
3. Never contact a bureau/furnisher on a consumer's behalf.
4. Keep the "you can do this yourself for free" disclosure prominent.
5. Any new marketing copy gets checked against this memo before shipping.
