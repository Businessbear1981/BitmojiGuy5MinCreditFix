"use client";

/**
 * Partner credit card recommendations.
 *
 * Replace placeholder `href` values with your actual affiliate links
 * from Impact, CJ Affiliate, FlexOffers, etc.
 *
 * FTC COMPLIANCE: the disclosure banner at the top is required.
 * Do NOT remove it or move it below the links.
 */

const PARTNERS = [
  {
    name: "Chime Credit Builder",
    issuer: "Chime",
    tag: "No credit check",
    desc: "Build credit with everyday purchases. No annual fee, no interest, no minimum deposit.",
    href: "https://www.chime.com/apply-credit-builder/",
    network: "Impact",
    category: "builder",
  },
  {
    name: "Self Credit Builder",
    issuer: "Self",
    tag: "Credit builder loan",
    desc: "Build credit and savings at the same time. Reports to all 3 bureaus.",
    href: "https://www.self.inc/",
    network: "Impact",
    category: "builder",
  },
  {
    name: "OpenSky Secured Visa",
    issuer: "OpenSky",
    tag: "No credit check",
    desc: "Secured card with no credit check required. $200 minimum deposit. Reports to all 3 bureaus.",
    href: "https://www.openskycc.com/",
    network: "FlexOffers",
    category: "secured",
  },
  {
    name: "Discover it Secured",
    issuer: "Discover",
    tag: "Cash back rewards",
    desc: "Secured card with 2% cash back at gas stations and restaurants (up to $1,000/quarter). No annual fee.",
    href: "https://www.discover.com/credit-cards/secured/",
    network: "CJ Affiliate",
    category: "secured",
  },
  {
    name: "Capital One Secured",
    issuer: "Capital One",
    tag: "Low deposit",
    desc: "Secured card with as low as $49 deposit for a $200 credit line. No annual fee.",
    href: "https://www.capitalone.com/credit-cards/secured-mastercard/",
    network: "CJ Affiliate",
    category: "secured",
  },
  {
    name: "Capital One Quicksilver",
    issuer: "Capital One",
    tag: "1.5% cash back",
    desc: "Unlimited 1.5% cash back on every purchase. No annual fee. For fair to excellent credit.",
    href: "https://www.capitalone.com/credit-cards/quicksilver/",
    network: "CJ Affiliate",
    category: "unsecured",
  },
  {
    name: "Cleo Credit Builder",
    issuer: "Cleo",
    tag: "AI-powered",
    desc: "Build credit while Cleo helps you budget. Reports to all 3 bureaus. Subscription-based.",
    href: "https://www.meetcleo.com/",
    network: "Impact",
    category: "builder",
  },
  {
    name: "MoneyLion Credit Builder Plus",
    issuer: "MoneyLion",
    tag: "Membership",
    desc: "Credit builder loan plus cash advances. Reports to all 3 bureaus.",
    href: "https://www.moneylion.com/",
    network: "Impact",
    category: "builder",
  },
];

const CATEGORY_LABELS = {
  builder: "Credit Builders",
  secured: "Secured Cards",
  unsecured: "Unsecured Cards",
};

const CATEGORY_ORDER = ["builder", "secured", "unsecured"];

export default function PartnerCards() {
  const grouped = {};
  for (const p of PARTNERS) {
    if (!grouped[p.category]) grouped[p.category] = [];
    grouped[p.category].push(p);
  }

  return (
    <div>
      {/* FTC Disclosure — REQUIRED, do not remove */}
      <div className="bg-mist/20 border border-gold-border rounded-lg p-3 mb-5 text-xs text-muted font-body">
        Advertising Disclosure: We may earn a commission when you apply
        through the links below. This does not affect your dispute letters or
        the cost of our service. Recommendations are optional and separate
        from credit repair services.
      </div>

      <h2 className="step-sub text-xl font-semibold mb-2">
        Rebuild Your Credit
      </h2>
      <p className="text-muted text-sm mb-6 font-body">
        After your disputes process, these products can help you build
        positive credit history. Your victory is earned, not given.
      </p>

      {CATEGORY_ORDER.map((cat) => {
        const items = grouped[cat];
        if (!items || items.length === 0) return null;
        return (
          <div key={cat} className="mb-6">
            <h3 className="text-xs font-semibold text-gold/60 uppercase tracking-wider mb-3 font-heading">
              {CATEGORY_LABELS[cat]}
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {items.map((p) => (
                <a
                  key={p.name}
                  href={p.href}
                  target="_blank"
                  rel="noopener noreferrer sponsored"
                  className="card hover:border-gold/40 transition-all group"
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium text-ivory text-sm group-hover:text-gold transition-colors font-heading">
                      {p.name}
                    </span>
                    <span className="text-xs px-2 py-0.5 rounded-full bg-gold/10 text-gold border border-gold-border font-body">
                      {p.tag}
                    </span>
                  </div>
                  <p className="text-xs text-muted font-body">{p.desc}</p>
                </a>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}
