/**
 * Client-side credit report parser — closed loop, no API calls.
 * Reads uploaded files, extracts text, scans for dispute items.
 */

// ── Dispute pattern definitions (mirrors Flask backend) ─────────────────────

interface DisputePattern {
  label: string
  patterns: RegExp[]
  extract: RegExp
}

const DISPUTE_PATTERNS: Record<string, DisputePattern> = {
  collections: {
    label: 'Collection Account',
    patterns: [
      /collect(?:ion|ions)\s+(?:account|agency|balance)/i,
      /(?:placed|sent|sold)\s+(?:for|to)\s+collect/i,
      /charged?\s*off.*collect/i,
      /(?:portfolio|midland|lvnv|encore|cavalry|ic system)/i,
    ],
    extract: /((?:collection|collect\w+).{0,80}(?:\$[\d,.]+|\d{4,}))/gi,
  },
  late_payments: {
    label: 'Late Payment',
    patterns: [
      /(?:30|60|90|120)\s*days?\s*(?:late|past\s*due|delinq)/i,
      /late\s+payment/i,
      /past\s+due\s+(?:amount|balance)/i,
      /delinquen(?:t|cy)/i,
    ],
    extract: /((?:late|past due|delinq)\w*.{0,80}(?:\$[\d,.]+|\d{2}\/\d{2,4}))/gi,
  },
  wrong_addresses: {
    label: 'Incorrect Address',
    patterns: [
      /address(?:es)?\s+(?:reported|on file|listed)/i,
      /(?:previous|former|old|prior)\s+address/i,
      /(?:po box|p\.o\.\s*box)\s*\d+/i,
    ],
    extract: /((?:address|addr).{0,120})/gi,
  },
  unknown_accounts: {
    label: 'Unknown / Unrecognized Account',
    patterns: [
      /(?:authorized\s+user|au\s+account)/i,
      /inquir(?:y|ies)/i,
      /(?:hard|soft)\s+(?:pull|inquiry)/i,
      /account\s+(?:number|#|no)[\s.:]*\w{4,}/i,
    ],
    extract: /((?:account|acct)[\s#.:]*\w*.{0,80})/gi,
  },
  aged_debt: {
    label: 'Aged / Time-Barred Debt',
    patterns: [
      /(?:date\s+)?open(?:ed)?[\s:]+\d{1,2}\/\d{2,4}/i,
      /(?:original|first)\s+delinquency/i,
      /statute\s+of\s+limitation/i,
      /charge[\s-]*off\s+(?:date|since)/i,
    ],
    extract: /((?:charge.?off|delinquen|open(?:ed)?).{0,100}(?:\d{1,2}\/\d{2,4}|\$[\d,.]+))/gi,
  },
}

// ── Known creditors for structured extraction ───────────────────────────────

const KNOWN_CREDITORS = [
  'CAPITAL ONE', 'CHASE', 'JPMORGAN', 'BANK OF AMERICA', 'WELLS FARGO',
  'CITIBANK', 'CITI', 'DISCOVER', 'AMERICAN EXPRESS', 'AMEX', 'SYNCHRONY',
  'BARCLAYS', 'US BANK', 'PNC', 'TD BANK', 'ALLY', 'NAVIENT', 'SALLIE MAE',
  'PORTFOLIO RECOVERY', 'MIDLAND CREDIT', 'LVNV FUNDING', 'ENCORE CAPITAL',
  'CAVALRY', 'IC SYSTEM', 'CONVERGENT', 'TRANSWORLD', 'ERC', 'ENHANCED RECOVERY',
  'UNIFIN', 'AFNI', 'CREDIT ACCEPTANCE', 'WESTLAKE', 'SANTANDER',
  'REGIONAL ACCEPTANCE', 'SPRINGLEAF', 'ONEMAIN', 'LENDING CLUB', 'PROSPER',
  'UPSTART', 'SOFI', 'AVANT', 'BEST BUY', 'TARGET', 'WALMART', 'AMAZON',
  'PAYPAL', 'KLARNA', 'AFFIRM', 'AFTERPAY', 'CARE CREDIT',
]

const NEGATIVE_MARKS: Record<string, RegExp> = {
  collection: /collect(?:ion|ions|ed)/i,
  charge_off: /charge[\s-]*off/i,
  late_payment: /(?:30|60|90|120)\s*days?\s*(?:late|past\s*due)|late\s+payment|delinquen/i,
  repossession: /repos(?:s)?ess/i,
  foreclosure: /foreclos/i,
  bankruptcy: /bankrupt/i,
  judgment: /judg(?:e)?ment/i,
  settled: /settled?\s+(?:for\s+)?less/i,
}

const MARK_TO_DISPUTE_BOX: Record<string, string> = {
  collection: 'collections',
  charge_off: 'collections',
  late_payment: 'late_payments',
  repossession: 'collections',
  foreclosure: 'collections',
  bankruptcy: 'unknown_accounts',
  judgment: 'unknown_accounts',
  settled: 'aged_debt',
}

// ── State SOL database ──────────────────────────────────────────────────────

const STATE_SOL: Record<string, number> = {
  AL: 6, AK: 3, AZ: 6, AR: 5, CA: 4, CO: 6, CT: 6, DE: 3, FL: 5, GA: 6,
  HI: 6, ID: 5, IL: 5, IN: 6, IA: 5, KS: 5, KY: 5, LA: 3, ME: 6, MD: 3,
  MA: 6, MI: 6, MN: 6, MS: 3, MO: 5, MT: 5, NE: 5, NV: 6, NH: 3, NJ: 6,
  NM: 6, NY: 6, NC: 3, ND: 6, OH: 6, OK: 5, OR: 6, PA: 4, RI: 10, SC: 3,
  SD: 6, TN: 6, TX: 4, UT: 6, VT: 6, VA: 5, WA: 6, WV: 10, WI: 6, WY: 8, DC: 3,
}

// ── Text extraction from files ──────────────────────────────────────────────

async function extractTextFromFile(file: File): Promise<string> {
  // Read first bytes to sniff actual format — don't trust the extension
  const header = new Uint8Array(await file.slice(0, 8).arrayBuffer())
  const isPdf = header[0] === 0x25 && header[1] === 0x50 && header[2] === 0x44 && header[3] === 0x46 // %PDF
  const isZip = header[0] === 0x50 && header[1] === 0x4B // PK (docx/xlsx/odt are zip archives)
  const isImage = (header[0] === 0x89 && header[1] === 0x50) || // PNG
                  (header[0] === 0xFF && header[1] === 0xD8)     // JPEG

  // PDF — regardless of what extension the user saved it as
  if (isPdf) {
    return await extractTextFromPdf(file)
  }

  // Images — no OCR in browser
  if (isImage) {
    return '[IMAGE_UPLOADED_NO_OCR]'
  }

  // Everything else — read as text first, then figure out what it is
  let raw = ''
  try {
    raw = await file.text()
  } catch {
    return ''
  }

  // DOCX/ODT (zip archive) — extract text from the XML inside
  if (isZip) {
    return await extractTextFromZipDoc(file, raw)
  }

  // HTML — if the content has HTML tags, strip them to get text
  if (/<\s*(?:html|head|body|div|table|tr|td|span|p)\b/i.test(raw)) {
    return raw
      .replace(/<style[^>]*>[\s\S]*?<\/style>/gi, '')
      .replace(/<script[^>]*>[\s\S]*?<\/script>/gi, '')
      .replace(/<[^>]+>/g, ' ')
      .replace(/&nbsp;/gi, ' ')
      .replace(/&amp;/gi, '&')
      .replace(/&lt;/gi, '<')
      .replace(/&gt;/gi, '>')
      .replace(/&#?\w+;/gi, ' ')
      .replace(/\s+/g, ' ')
      .trim()
  }

  // Plain text / CSV / anything else — return as-is
  return raw
}

async function extractTextFromZipDoc(file: File, _raw: string): Promise<string> {
  // DOCX and ODT are ZIP archives with XML inside
  // Use a minimal approach — find readable text in the binary
  try {
    const buffer = await file.arrayBuffer()
    const bytes = new Uint8Array(buffer)
    const decoded = new TextDecoder('utf-8', { fatal: false }).decode(bytes)

    // Extract text from XML tags (works for both docx and odt)
    const textMatches = decoded.match(/<w:t[^>]*>([^<]+)<\/w:t>/g) // DOCX
      || decoded.match(/<text:p[^>]*>([^<]+)<\/text:p>/g) // ODT
      || []

    if (textMatches.length > 0) {
      return textMatches
        .map((m) => m.replace(/<[^>]+>/g, ''))
        .join(' ')
    }

    // Fallback — grab all readable strings from the binary
    const strings = decoded.match(/[\x20-\x7E]{12,}/g) || []
    return strings.join('\n')
  } catch {
    return ''
  }
}

async function extractTextFromPdf(file: File): Promise<string> {
  // Dynamic import pdf.js if available, otherwise read raw bytes as text
  try {
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    const pdfjsLib = await import(/* webpackIgnore: true */ 'pdfjs-dist' as string)
    pdfjsLib.GlobalWorkerOptions.workerSrc = ''
    const buffer = await file.arrayBuffer()
    const pdf = await pdfjsLib.getDocument({ data: buffer }).promise
    let text = ''
    const maxPages = Math.min(pdf.numPages, 30)
    for (let i = 1; i <= maxPages; i++) {
      const page = await pdf.getPage(i)
      const content = await page.getTextContent()
      text += content.items.map((item: Record<string, unknown>) => (item.str as string) || '').join(' ') + '\n'
    }
    return text
  } catch {
    // pdf.js not installed — try raw text extraction
    try {
      const buffer = await file.arrayBuffer()
      const bytes = new Uint8Array(buffer)
      const raw = new TextDecoder('utf-8', { fatal: false }).decode(bytes)
      // Extract readable strings from PDF binary
      const strings = raw.match(/[\x20-\x7E]{10,}/g) || []
      return strings.join('\n')
    } catch {
      return ''
    }
  }
}

// ── Dispute detection engine ────────────────────────────────────────────────

export interface DisputeItem {
  creditor: string
  account_number: string
  type: string
  amount: string
  date: string
  dispute: boolean
  dispute_box: string
  dispute_label: string
  sol_expired?: boolean
  account_age_years?: number
  text?: string
  label?: string
}

function parseTextForDisputes(text: string): Record<string, { label: string; items: string[] }> {
  const results: Record<string, { label: string; items: string[] }> = {}

  for (const [dtype, cfg] of Object.entries(DISPUTE_PATTERNS)) {
    const matched = cfg.patterns.some((p) => p.test(text))
    if (matched) {
      const hits: string[] = []
      let m: RegExpExecArray | null
      const re = new RegExp(cfg.extract.source, cfg.extract.flags)
      while ((m = re.exec(text)) !== null && hits.length < 5) {
        const cleaned = m[1].replace(/\s+/g, ' ').trim().slice(0, 120)
        if (cleaned.length > 15) hits.push(cleaned)
      }
      if (hits.length === 0) {
        hits.push(`${cfg.label} detected in report`)
      }
      results[dtype] = { label: cfg.label, items: hits }
    }
  }
  return results
}

function extractStructuredAccounts(text: string): DisputeItem[] {
  const accounts: DisputeItem[] = []
  const creditorPattern = new RegExp(`(${KNOWN_CREDITORS.map((c) => c.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|')})`, 'gi')
  const acctNumRe = /(?:account|acct|#|no)[\s#.:]*([A-Z0-9*x]{4,20})/i
  const amountRe = /\$[\d,]+(?:\.\d{2})?/
  const dateRe = /\b(\d{1,2}\/\d{2,4}|\d{1,2}-\d{1,2}-\d{2,4}|\d{4}-\d{2}-\d{2})\b/

  const lines = text.split('\n')
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i]
    const creditorMatch = creditorPattern.exec(line)
    if (!creditorMatch) continue
    creditorPattern.lastIndex = 0

    const context = lines.slice(Math.max(0, i - 1), Math.min(lines.length, i + 5)).join(' ')
    const creditor = creditorMatch[1].toUpperCase()
    const acctMatch = acctNumRe.exec(context)
    const amtMatch = amountRe.exec(context)
    const dateMatch = dateRe.exec(context)

    let markType = ''
    for (const [mark, re] of Object.entries(NEGATIVE_MARKS)) {
      if (re.test(context)) {
        markType = mark
        break
      }
    }

    if (markType || amtMatch) {
      accounts.push({
        creditor,
        account_number: acctMatch?.[1] || '',
        type: markType || 'unknown_accounts',
        amount: amtMatch?.[0] || '',
        date: dateMatch?.[1] || '',
        dispute: true,
        dispute_box: MARK_TO_DISPUTE_BOX[markType] || 'unknown_accounts',
        dispute_label: '',
        text: context.slice(0, 200),
      })
    }
  }

  // Deduplicate by creditor + account number
  const seen = new Set<string>()
  return accounts.filter((a) => {
    const key = `${a.creditor}|${a.account_number}`
    if (seen.has(key)) return false
    seen.add(key)
    return true
  })
}

function classifyDisputeItems(accounts: DisputeItem[], stateCode: string): DisputeItem[] {
  const solYears = STATE_SOL[stateCode] || null

  for (const acct of accounts) {
    const box = MARK_TO_DISPUTE_BOX[acct.type] || 'unknown_accounts'

    // Check statute of limitations
    if (solYears && acct.date) {
      const parsed = parseDate(acct.date)
      if (parsed) {
        const ageYears = (Date.now() - parsed.getTime()) / (365.25 * 24 * 60 * 60 * 1000)
        if (ageYears >= solYears) {
          acct.dispute_box = 'aged_debt'
          acct.sol_expired = true
          acct.account_age_years = Math.round(ageYears * 10) / 10
          acct.dispute_label = 'Aged / Time-Barred Debt'
          continue
        }
      }
    }

    acct.dispute_box = box
    acct.dispute_label = DISPUTE_PATTERNS[box]?.label || 'Unknown'
  }

  return accounts
}

function parseDate(str: string): Date | null {
  const formats = [
    /^(\d{1,2})\/(\d{2,4})$/, // MM/YY or MM/YYYY
    /^(\d{1,2})\/(\d{1,2})\/(\d{2,4})$/, // MM/DD/YY or MM/DD/YYYY
    /^(\d{4})-(\d{2})-(\d{2})$/, // YYYY-MM-DD
  ]
  for (const fmt of formats) {
    const m = fmt.exec(str)
    if (!m) continue
    if (m.length === 3) {
      const month = parseInt(m[1]) - 1
      let year = parseInt(m[2])
      if (year < 100) year += 2000
      return new Date(year, month, 1)
    }
    if (m.length === 4) {
      if (m[1].length === 4) return new Date(parseInt(m[1]), parseInt(m[2]) - 1, parseInt(m[3]))
      const month = parseInt(m[1]) - 1
      const day = parseInt(m[2])
      let year = parseInt(m[3])
      if (year < 100) year += 2000
      return new Date(year, month, day)
    }
  }
  return null
}

// ── Main export ─────────────────────────────────────────────────────────────

export interface ParseResult {
  items: DisputeItem[]
  rawText: string
  parsedCategories: Record<string, { label: string; items: string[] }>
  accountCount: number
}

export async function parseReport(file: File, stateCode: string): Promise<ParseResult> {
  console.log('[parseReport] Starting parse for:', file.name, 'size:', file.size, 'type:', file.type)
  const rawText = await extractTextFromFile(file)
  console.log('[parseReport] Extracted text length:', rawText.length)
  console.log('[parseReport] First 200 chars:', rawText.slice(0, 200))

  if (!rawText || rawText === '[IMAGE_UPLOADED_NO_OCR]') {
    return {
      items: [{
        creditor: '', account_number: '', type: 'unknown_accounts',
        amount: '', date: '', dispute: true,
        dispute_box: 'unknown_accounts',
        dispute_label: 'Manual Review Needed',
        text: rawText === '[IMAGE_UPLOADED_NO_OCR]'
          ? 'Image uploaded — OCR not available in browser. Upload PDF, HTML, or TXT for automatic parsing.'
          : 'Could not extract text from this file. Try a different format.',
      }],
      rawText: '',
      parsedCategories: {},
      accountCount: 0,
    }
  }

  // Run both parsers
  const parsedCategories = parseTextForDisputes(rawText)
  console.log('[parseReport] Categories found:', Object.keys(parsedCategories))
  const structuredAccounts = extractStructuredAccounts(rawText)
  console.log('[parseReport] Structured accounts:', structuredAccounts.length)
  const classified = classifyDisputeItems(structuredAccounts, stateCode)

  // If structured extraction found accounts, use those
  // Otherwise fall back to regex category matches
  let items: DisputeItem[]
  if (classified.length > 0) {
    items = classified
  } else {
    // Convert category matches to DisputeItem format
    items = []
    for (const [dtype, info] of Object.entries(parsedCategories)) {
      for (const text of info.items) {
        items.push({
          creditor: '', account_number: '', type: dtype,
          amount: '', date: '', dispute: true,
          dispute_box: dtype,
          dispute_label: info.label,
          text,
        })
      }
    }
  }

  console.log('[parseReport] Final items:', items.length)
  items.forEach((item, i) => console.log(`[parseReport] Item ${i}:`, item.dispute_label, item.creditor || item.text?.slice(0, 60)))

  return {
    items,
    rawText,
    parsedCategories,
    accountCount: structuredAccounts.length,
  }
}
