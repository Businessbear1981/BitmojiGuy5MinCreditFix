"""
Admin print packet — everything needed to put a case in the mail.

Built for the round-one reality where Sean prints and mails by hand. One
URL, one Ctrl-P, and out comes:

  1. A mailing checklist (what goes in which envelope, postage, tracking)
  2. Each letter on its own page, signature block and all
  3. Avery 5160 address labels — return + recipient, pre-paired
  4. #10 envelope layouts, for printing directly onto envelopes

Everything is a single self-contained HTML document with print CSS. No
dependencies, no build step, no PDF library — the browser's own print
dialog produces better output than a generated PDF for this job, and it
lets you reprint one page without regenerating anything.

Access is by short-lived signed token rather than the admin key, so the
print URL can be opened in a normal browser tab without putting the
long-lived key into browser history, server logs, or a bookmark.
"""
from __future__ import annotations

import hashlib
import hmac
import html
import time

import config

# Bureau addresses, formatted for a label. Kept here rather than imported so
# the print output stays correct even if the letter engine's copy changes.
BUREAU_MAIL = {
    "Experian": ["Experian", "P.O. Box 4500", "Allen, TX 75013"],
    "Equifax": ["Equifax Information Services LLC", "P.O. Box 740241",
                "Atlanta, GA 30374-0241"],
    "TransUnion": ["TransUnion Consumer Solutions", "P.O. Box 2000",
                   "Chester, PA 19016-2000"],
}

TOKEN_TTL_SECONDS = 600  # 10 minutes — long enough to print, short enough to leak safely


# ── Signed print tokens ─────────────────────────────────────────────────────

def issue_print_token(session_id: str) -> str:
    """Mint a short-lived token authorising a print view for one case."""
    expires = int(time.time()) + TOKEN_TTL_SECONDS
    payload = f"{session_id}:{expires}"
    sig = hmac.new(config.ADMIN_KEY.encode(), payload.encode(), hashlib.sha256).hexdigest()[:32]
    return f"{expires}.{sig}"


def verify_print_token(session_id: str, token: str) -> bool:
    """Constant-time check that a print token is valid and unexpired."""
    if not token or "." not in token or not config.ADMIN_KEY:
        return False
    expires_raw, _, sig = token.partition(".")
    try:
        expires = int(expires_raw)
    except ValueError:
        return False
    if expires < time.time():
        return False
    expected = hmac.new(
        config.ADMIN_KEY.encode(), f"{session_id}:{expires}".encode(), hashlib.sha256
    ).hexdigest()[:32]
    return hmac.compare_digest(expected, sig)


# ── Helpers ─────────────────────────────────────────────────────────────────

def _addr_lines(target: str) -> list[str]:
    return BUREAU_MAIL.get(target, [target, "(see letter for address)"])


def _split_client_address(address: str) -> list[str]:
    """'418 Marlowe Ave, Austin, TX 78702' -> ['418 Marlowe Ave', 'Austin, TX 78702']"""
    parts = [p.strip() for p in (address or "").split(",")]
    if len(parts) >= 3:
        return [parts[0], ", ".join(parts[1:])]
    return parts or [address or ""]


def _e(text: str) -> str:
    return html.escape(text or "")


# ── Document sections ───────────────────────────────────────────────────────

def _checklist(name: str, letters: list[dict], code: str, tier_label: str) -> str:
    rows = []
    for i, ltr in enumerate(letters, 1):
        target = ltr.get("target", "Bureau")
        addr = " · ".join(_addr_lines(target)[1:])
        rows.append(f"""
        <tr>
          <td class="chk"><span class="box"></span></td>
          <td><strong>{_e(target)}</strong><br><span class="muted">{_e(addr)}</span></td>
          <td class="muted">Letter {i} of {len(letters)}</td>
          <td class="muted">Certified + return receipt</td>
          <td class="track"></td>
        </tr>""")

    return f"""
    <section class="sheet">
      <h1>Mailing checklist</h1>
      <p class="sub">{_e(name)} &middot; {_e(code)} &middot; {_e(tier_label)}</p>

      <table class="checklist">
        <thead>
          <tr><th></th><th>Send to</th><th></th><th>Postage</th><th>Tracking #</th></tr>
        </thead>
        <tbody>{''.join(rows)}</tbody>
      </table>

      <h2>Before sealing each envelope</h2>
      <ol class="steps">
        <li><span class="box"></span> Letter signed in <strong>blue ink</strong></li>
        <li><span class="box"></span> Copy of photo ID &mdash; <strong>both sides</strong> on one sheet</li>
        <li><span class="box"></span> Copy of proof of address (utility bill, bank statement, lease)</li>
        <li><span class="box"></span> Nothing original — copies only</li>
      </ol>

      <h2>At the counter</h2>
      <ol class="steps">
        <li><span class="box"></span> USPS Certified Mail, Return Receipt Requested (PS Form 3811)</li>
        <li><span class="box"></span> Write each tracking number in the table above</li>
        <li><span class="box"></span> Keep the green card when it comes back — that is your proof of delivery</li>
        <li><span class="box"></span> Enter tracking numbers in /admin so the 30-day clock starts</li>
      </ol>

      <p class="note">The bureaus have 30 days from <em>receipt</em>, not from postmark.
      The return receipt is what establishes that date.</p>
    </section>"""


def _letter_pages(letters: list[dict]) -> str:
    pages = []
    for ltr in letters:
        body = ltr.get("text", "")
        pages.append(f"""
    <section class="sheet letter">
      <pre class="body">{_e(body)}</pre>
    </section>""")
    return "".join(pages)


def _labels(name: str, client_address: str, letters: list[dict]) -> str:
    """Avery 5160 — 3 across, 10 down, 2.625in x 1in."""
    from_lines = [name] + _split_client_address(client_address)
    cells = []

    for ltr in letters:
        to_lines = _addr_lines(ltr.get("target", "Bureau"))
        cells.append(f"""
      <div class="label">
        <div class="lbl-from">{'<br>'.join(_e(l) for l in from_lines)}</div>
        <div class="lbl-to">{'<br>'.join(_e(l) for l in to_lines)}</div>
      </div>""")

    # Pad to a full row of 3 so the sheet feeds straight.
    while len(cells) % 3:
        cells.append('<div class="label empty"></div>')

    return f"""
    <section class="sheet labels-sheet">
      <h1 class="screen-only">Address labels &mdash; Avery 5160</h1>
      <p class="sub screen-only">Load a 5160 sheet. Return address top-left, recipient below.</p>
      <div class="labels">{''.join(cells)}</div>
    </section>"""


def _envelopes(name: str, client_address: str, letters: list[dict]) -> str:
    """#10 envelope, 9.5in x 4.125in, printed one per page."""
    from_lines = [name] + _split_client_address(client_address)
    envs = []
    for ltr in letters:
        to_lines = _addr_lines(ltr.get("target", "Bureau"))
        envs.append(f"""
    <section class="sheet envelope">
      <div class="env-from">{'<br>'.join(_e(l) for l in from_lines)}</div>
      <div class="env-to">{'<br>'.join(_e(l) for l in to_lines)}</div>
      <div class="env-mark">CERTIFIED MAIL &mdash; RETURN RECEIPT REQUESTED</div>
    </section>""")
    return "".join(envs)


def _window_covers(name: str, client_address: str, letters: list[dict]) -> str:
    """
    Cover sheet per letter, addressed for a #10 SINGLE-WINDOW envelope.

    Tri-fold this sheet (bottom third up, then top third down) and the
    recipient block lands in the window. No label, no handwriting — the
    only sticker you need is your return address.

    Window position varies slightly by envelope brand, so the block sits
    inside a marked safe zone rather than at one exact coordinate. Print
    one and check it against your envelopes before running a batch.
    """
    from_lines = [name] + _split_client_address(client_address)
    covers = []
    for i, ltr in enumerate(letters, 1):
        to_lines = _addr_lines(ltr.get("target", "Bureau"))
        covers.append(f"""
    <section class="sheet window-cover">
      <div class="fold-mark fold-1"><span>fold up</span></div>
      <div class="fold-mark fold-2"><span>fold down</span></div>

      <div class="wc-from">{'<br>'.join(_e(l) for l in from_lines)}</div>

      <div class="window-zone">
        <div class="wz-label screen-only">#10 window safe zone</div>
        <div class="wc-to">{'<br>'.join(_e(l) for l in to_lines)}</div>
      </div>

      <div class="wc-mark">CERTIFIED MAIL &mdash; RETURN RECEIPT REQUESTED</div>
      <div class="wc-foot screen-only">
        Cover {i} of {len(letters)} &middot; tri-fold &middot; place behind this sheet:
        signed letter, ID copy, proof of address
      </div>
    </section>""")
    return "".join(covers)


def _return_stickers(name: str, client_address: str) -> str:
    """A full Avery 5160 sheet of return-address stickers — 30 identical."""
    from_lines = [name] + _split_client_address(client_address)
    one = "<br>".join(_e(l) for l in from_lines)
    cells = "".join(
        f'<div class="label"><div class="sticker">{one}</div></div>' for _ in range(30)
    )
    return f"""
    <section class="sheet labels-sheet">
      <h1 class="screen-only">Return-address stickers &mdash; Avery 5160</h1>
      <p class="sub screen-only">30 per sheet. One on each envelope, top-left.</p>
      <div class="labels">{cells}</div>
    </section>"""


# ── Main builder ────────────────────────────────────────────────────────────

def build_print_packet(
    name: str,
    client_address: str,
    letters: list[dict],
    confirmation: str = "",
    tier: int = 1,
    tier_name: str = "",
) -> str:
    """Return a complete, self-contained printable HTML document."""
    tier_label = f"Round {tier}" + (f" — {tier_name}" if tier_name else "")
    code = confirmation or "—"

    return f"""<!doctype html>
<html><head>
<meta charset="utf-8">
<title>Print packet — {_e(name)}</title>
<style>
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; background: #55575c;
    font-family: -apple-system, "Segoe UI", system-ui, sans-serif;
    color: #14140f;
  }}
  .toolbar {{
    position: sticky; top: 0; z-index: 10;
    background: #14140f; color: #f0ebe0;
    padding: 12px 20px; display: flex; gap: 16px; align-items: center;
    font-size: 13px;
  }}
  .toolbar button {{
    font: inherit; font-weight: 600;
    background: #c9a84c; color: #14140f; border: 0;
    padding: 8px 18px; border-radius: 4px; cursor: pointer;
  }}
  .toolbar .hint {{ opacity: .7 }}

  .sheet {{
    background: #fff; width: 8.5in; min-height: 11in;
    margin: 20px auto; padding: 0.75in 0.9in;
    box-shadow: 0 4px 20px rgba(0,0,0,.35);
    page-break-after: always;
  }}
  h1 {{ font-size: 20pt; margin: 0 0 4px; letter-spacing: -.01em }}
  h2 {{ font-size: 12pt; margin: 26px 0 8px; text-transform: uppercase; letter-spacing: .08em }}
  .sub {{ margin: 0 0 24px; color: #6a675f; font-size: 10.5pt }}
  .muted {{ color: #6a675f }}
  .note {{ margin-top: 26px; padding: 12px 14px; background: #f3f1ea;
           border-left: 3px solid #c9a84c; font-size: 10pt; line-height: 1.5 }}

  table.checklist {{ width: 100%; border-collapse: collapse; font-size: 10.5pt }}
  table.checklist th {{
    text-align: left; font-size: 8pt; text-transform: uppercase; letter-spacing: .08em;
    color: #6a675f; border-bottom: 1.5px solid #14140f; padding: 6px 8px;
  }}
  table.checklist td {{ padding: 12px 8px; border-bottom: 1px solid #ddd; vertical-align: top }}
  td.chk {{ width: 28px }}
  td.track {{ width: 150px; border-bottom: 1px solid #ddd }}

  .box {{
    display: inline-block; width: 13px; height: 13px;
    border: 1.5px solid #14140f; border-radius: 2px; vertical-align: -2px;
  }}
  ol.steps {{ list-style: none; padding: 0; margin: 0; font-size: 10.5pt }}
  ol.steps li {{ padding: 7px 0; border-bottom: 1px solid #eee }}
  ol.steps .box {{ margin-right: 10px }}

  .letter .body {{
    font-family: "Courier New", Courier, monospace;
    font-size: 10.5pt; line-height: 1.55;
    white-space: pre-wrap; word-wrap: break-word; margin: 0;
  }}

  /* Avery 5160 */
  .labels {{ display: grid; grid-template-columns: repeat(3, 2.625in); gap: 0 }}
  .label {{
    width: 2.625in; height: 1in; padding: .12in .16in;
    font-size: 7.5pt; line-height: 1.25; overflow: hidden;
  }}
  .label.empty {{ visibility: hidden }}
  .lbl-from {{ font-size: 6pt; color: #555; margin-bottom: .1in }}
  .lbl-to {{ font-weight: 600 }}
  .labels-sheet {{ padding: .5in .19in }}

  /* #10 envelope */
  .envelope {{
    width: 9.5in; height: 4.125in; min-height: 0;
    position: relative; padding: 0;
  }}
  .env-from {{ position: absolute; top: .4in; left: .4in; font-size: 9pt; line-height: 1.3 }}
  .env-to   {{ position: absolute; top: 2in; left: 4.2in; font-size: 12pt; line-height: 1.4; font-weight: 600 }}
  .env-mark {{
    position: absolute; top: 1.15in; left: .4in;
    font-size: 8pt; font-weight: 700; letter-spacing: .05em;
    border: 1.5px solid #14140f; padding: 4px 8px;
  }}


  /* Window-envelope cover sheet */
  .window-cover {{ position: relative; padding: 0 }}
  .wc-from {{ position: absolute; top: .55in; left: .75in; font-size: 9.5pt; line-height: 1.35 }}
  .wc-mark {{
    position: absolute; top: 1.35in; left: .75in;
    font-size: 8pt; font-weight: 700; letter-spacing: .05em;
    border: 1.5px solid #14140f; padding: 4px 8px;
  }}
  /* Safe zone for a standard #10 single window */
  .window-zone {{
    position: absolute; top: 2.0in; left: .875in;
    width: 4in; height: 1.05in; padding: .1in .12in;
  }}
  .wz-label {{
    position: absolute; top: -14px; left: 0;
    font-size: 7pt; letter-spacing: .06em; text-transform: uppercase; color: #b08a2a;
  }}
  .wc-to {{ font-size: 12pt; line-height: 1.35; font-weight: 600 }}
  .fold-mark {{
    position: absolute; left: 0; right: 0; border-top: 1px dashed #c9c5bb;
  }}
  .fold-mark span {{
    position: absolute; right: .35in; top: -8px; background: #fff;
    padding: 0 6px; font-size: 7pt; color: #b3aea3; letter-spacing: .06em;
  }}
  .fold-1 {{ top: 3.667in }}
  .fold-2 {{ top: 7.333in }}
  .wc-foot {{ position: absolute; bottom: .5in; left: .75in; font-size: 8.5pt; color: #6a675f }}
  .sticker {{ font-size: 8pt; line-height: 1.3; padding-top: .05in }}

  @media print {{
    .window-zone {{ border: 0 }}
    .fold-mark {{ border-top-color: #e8e6e0 }}
  }}

  @media print {{
    body {{ background: #fff }}
    .toolbar, .screen-only {{ display: none !important }}
    .sheet {{ margin: 0; box-shadow: none; width: auto; min-height: 0 }}
    .envelope {{ width: 9.5in; height: 4.125in }}
    @page {{ margin: 0.4in }}
  }}
</style>
</head><body>

<div class="toolbar">
  <button onclick="window.print()">Print packet</button>
  <span><strong>{_e(name)}</strong> &middot; {len(letters)} letter{'' if len(letters)==1 else 's'} &middot; {_e(code)}</span>
  <span class="hint">Checklist &rarr; window covers &rarr; letters &rarr; return stickers &rarr; labels &rarr; envelopes. Print all, or use a page range.</span>
</div>

{_checklist(name, letters, code, tier_label)}
{_window_covers(name, client_address, letters)}
{_letter_pages(letters)}
{_return_stickers(name, client_address)}
{_labels(name, client_address, letters)}
{_envelopes(name, client_address, letters)}

</body></html>"""
