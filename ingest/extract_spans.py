"""
extract_spans.py — pull VERBATIM clause spans from contract text.

Two-stage, matching your choice ("regex first pass, LLM fallback"):

  Stage 1 (deterministic): keyword/regex locates candidate clauses and returns
    the exact surrounding sentence/paragraph span, unmodified. Cheap, auditable,
    no network. This is the default and handles the common, well-worded cases.

  Stage 2 (LLM fallback): for any clause type Stage 1 did NOT find, optionally
    ask an LLM to locate it. The LLM is instructed to return an EXACT substring
    of the source text (a quote), never a paraphrase. We then verify the returned
    span is actually present verbatim in the source; if it isn't, we discard it.
    This guard is what keeps GABRIEL's input uncontaminated by model rewriting.

The LLM stage is OFF unless run_llm_fallback=True AND an API key is present, so
the module is fully usable and testable with zero network access.

Clause types map 1:1 to schema mechanism fields:
  interest_arbitration -> arbitration_clause_text
  comparability        -> comparability_text (+ comparability_referent)
  me_too               -> me_too_text
  no_strike            -> (flag only; no text field in schema)
"""

from __future__ import annotations
import os
import re
import json
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Stage 1: deterministic patterns
# ---------------------------------------------------------------------------
# Each clause type has trigger patterns. A match expands to the enclosing
# paragraph (verbatim) so GABRIEL sees full context, not a fragment.

TRIGGERS = {
    "interest_arbitration": [
        r"\binterest arbitration\b",
        r"\blast best offer\b",
        r"\bfinal[- ]offer arbitration\b",
        r"\bimpasse\b.{0,40}\barbitration\b",
    ],
    "comparability": [
        r"\bcomparab\w+\b",
        r"\bprevailing wage\b",
        r"\bcomparison communit\w+\b",
        r"\bsimilarly situated\b",
        r"\bexternal equity\b",
        r"\bparity\b",
    ],
    "me_too": [
        r"\bme[- ]too\b",
        r"\bmost favored nation\b",
        r"\bif any other (?:bargaining )?unit\b",
        r"\bshould any other (?:bargaining )?unit\b",
    ],
    "no_strike": [
        r"\bno[- ]strike\b",
        r"\bshall not strike\b",
        r"\bno (?:employee|member) shall (?:engage in|participate in) (?:a |any )?strike\b",
        r"\bwork stoppage\b",
    ],
}

# "binding arbitration" alone is deliberately NOT in TRIGGERS["interest_arbitration"]
# above: it is generic dispute-resolution language shared by grievance, discipline,
# benefits-dispute, and subcontracting/privatization-dispute arbitration, and
# matched non-wage-setting clauses as often as genuine interest arbitration (audited
# cases: NJ police legal-defense-coverage disputes, NJ police health-plan-definition
# disputes, an Ohio "final and binding arbitration" clause resolving a subcontracting/
# competitive-alternative dispute -- a mechanism this project's own codify codebook
# already tracks separately as subcontracting_outsourcing_or_volunteer_substitution,
# not interest arbitration). An earlier version of this fix tried a co-occurring-
# wage-vocabulary weak-trigger heuristic; it still produced the Ohio subcontracting
# false positive above (the clause literally discusses "the payment of a living
# wage"), so the weak trigger was retired rather than further special-cased. A row
# that only contains bare "binding arbitration" now stays unresolved (eligible for
# a future, more careful review or LLM-fallback pass) rather than being flagged
# outright -- under-flagging leaves a row for human/LLM review; over-flagging
# silently contaminates a primary-evidence field.

# A trigger phrase can appear inside language that EXCLUDES the unit from it rather
# than granting it (audited cases: a Scope clause reading "...but not employees who
# are eligible for interest arbitration...", a clause reading "...are not subject to
# interest arbitration...", an MFN clause merely referencing "...bargaining units
# entitled to interest arbitration..." as an exclusion category for a DIFFERENT
# group). Bare presence-matching cannot tell a grant from an exclusion; this guard
# checks the sentence containing the match for a negation/exclusion cue before the
# hit is accepted.
_NEGATION_CUES = re.compile(
    r"\b(not\s+(?:be\s+)?subject\s+to|excluded\s+from|does\s+not\s+apply\s+to|"
    r"shall\s+not\s+(?:be\s+(?:submitted|subject|referred)|apply|include|have jurisdiction)|"
    r"other\s+than|not\s+including|not\s+entitled\s+to|"
    r"not(?:\s+\w+){0,4}\s+eligible\s+for|"
    r"are\s+not\s+subject|is\s+not\s+subject)\b",
    re.IGNORECASE,
)

# For comparability, try to capture what the clause pegs to (the referent) —
# still verbatim: we return the matched phrase, we do NOT interpret it.
# DOTALL so matches survive pdftotext's mid-sentence line wraps.
REFERENT_PATTERNS = [
    r"comparable to\s+(.{0,160}?(?:communities|cities|towns|municipalities|jurisdictions|officers|departments)[^.;]{0,80})",
    r"((?:police|fire|law enforcement|firefighter)\w*\s+(?:officers?\s+)?(?:in|of|among)\s+.{0,140}?(?:communities|cities|towns|municipalities|jurisdictions))",
    r"(?:to|with|than|among)\s+((?:other\s+)?(?:surrounding|neighboring|comparable|similar)\s+(?:communities|cities|towns|municipalities|jurisdictions).{0,140}?)(?:[.;]|$)",
    r"(the\s+(?:average|mean|median)\s+of\s+.{0,140}?)(?:[.;]|$)",
]

# A referent match (peer-jurisdiction language) is necessary but not sufficient:
# "comparable [to] other cities" can describe non-wage things too (audited false
# positive: a recruiting-vendor evaluation clause comparing candidate pools "in
# other major or comparable metropolitan cities"). The schema's comparability
# concept is peer WAGE comparability specifically (redefined and applied
# project-wide 2026-07-05), so the matched span must also contain wage vocabulary.
_WAGE_VOCAB = re.compile(r"\b(wages?|salary|salaries|pay|compensation)\b", re.IGNORECASE)


def _paragraphs(text: str) -> list[str]:
    # Split on blank lines; fall back to single newlines for dense OCR output.
    parts = re.split(r"\n\s*\n", text)
    if len(parts) < 3:
        parts = re.split(r"\n", text)
    return [p.strip() for p in parts if p.strip()]


# A "heading" is a short, often all-caps line (e.g. "ARTICLE 24 — INTEREST
# ARBITRATION") that names a clause but contains none of its operative language.
# When a trigger matches only a heading, the real clause text is in the
# following paragraph(s), so we must absorb them or GABRIEL scores titles.
_HEADING_RE = re.compile(r"^\s*(article|section|sec\.?|art\.?)\b", re.IGNORECASE)


def _looks_like_heading(p: str) -> bool:
    if len(p) <= 80 and _HEADING_RE.match(p):
        return True
    # all-caps short line with no sentence punctuation
    letters = [c for c in p if c.isalpha()]
    if p and len(p) <= 80 and letters and all(c.isupper() for c in letters) \
            and not re.search(r"[.;]", p):
        return True
    return False


def _span_with_body(paras: list[str], idx: int) -> str:
    """Return the matched paragraph, but if it's just a heading, append the
    following non-heading body paragraph(s) so the operative language is kept
    verbatim and in context."""
    chosen = [paras[idx]]
    if _looks_like_heading(paras[idx]):
        j = idx + 1
        added = 0
        while j < len(paras) and added < 2:
            if _looks_like_heading(paras[j]):
                break
            chosen.append(paras[j])
            added += 1
            # one substantive body paragraph is usually enough
            if len(paras[j]) > 120:
                break
            j += 1
    return "\n".join(chosen).strip()


def _sentence_containing(text: str, pos: int) -> str:
    """Roughly isolate the sentence enclosing position pos, for negation-cue scoping.
    A negation cue elsewhere in a long paragraph shouldn't suppress an unrelated
    trigger match, so the check is scoped to a sentence, not the whole paragraph.
    Bare newlines are NOT treated as sentence boundaries: PDF text wraps mid-phrase
    (e.g. "not\\n    including"), and a naive newline split would sever a negation
    cue from the trigger it modifies."""
    start = max(text.rfind(".", 0, pos), text.rfind(";", 0, pos))
    ends = [e for e in (text.find(".", pos), text.find(";", pos)) if e != -1]
    end = min(ends) if ends else len(text)
    return text[start + 1:end + 1]


def _is_negated(paragraph: str, match_start: int) -> bool:
    return bool(_NEGATION_CUES.search(_sentence_containing(paragraph, match_start)))


@dataclass
class SpanHit:
    clause_type: str
    text: str            # verbatim span
    method: str          # "regex" | "llm"
    referent: str = ""   # comparability only


@dataclass
class ExtractionResult:
    hits: dict = field(default_factory=dict)   # clause_type -> SpanHit
    flags: dict = field(default_factory=dict)  # clause_type -> 0/1
    unresolved: list = field(default_factory=list)  # types regex missed

    def flag(self, t):
        return 1 if self.flags.get(t) else 0


def regex_pass(text: str) -> ExtractionResult:
    paras = _paragraphs(text)
    res = ExtractionResult()
    for ctype, pats in TRIGGERS.items():
        res.flags[ctype] = 0
        compiled = [re.compile(p, re.IGNORECASE) for p in pats]
        for idx, para in enumerate(paras):
            hit = None
            for c in compiled:
                m = c.search(para)
                if m:
                    hit = m
                    break
            if hit is None:
                continue

            # A matched trigger inside exclusion/negation language ("not eligible
            # for interest arbitration", "not including bargaining units entitled
            # to interest arbitration") is evidence the unit LACKS the mechanism,
            # not that it has it -- do not accept this occurrence as a positive hit,
            # but keep scanning later paragraphs for a genuine (non-negated) one.
            if ctype == "interest_arbitration" and _is_negated(para, hit.start()):
                continue

            span = _span_with_body(paras, idx)   # absorb body if heading-only
            referent = ""
            if ctype == "comparability":
                norm_span = re.sub(r"\s+", " ", span)
                for rp in REFERENT_PATTERNS:
                    m = re.search(rp, norm_span, re.IGNORECASE | re.DOTALL)
                    if m:
                        referent = m.group(1).strip()
                        break
                # A bare "comparable"/"comparability" hit with no peer-jurisdiction/
                # peer-wage referent is not the schema's peer-wage-comparability
                # concept (audited false positives: internal rank comparisons,
                # benefits-plan comparisons, sick-leave-usage comparisons) -- do not
                # flag it; keep scanning for a genuine referent-bearing occurrence.
                # A referent alone is still not sufficient: "comparable to other
                # cities" can describe non-wage things (audited false positive: a
                # recruiting-vendor evaluation clause) -- also require wage
                # vocabulary in the matched span.
                if not referent or not _WAGE_VOCAB.search(span):
                    continue

            res.flags[ctype] = 1
            res.hits[ctype] = SpanHit(
                clause_type=ctype, text=span,
                method="regex", referent=referent,
            )
            break
    # no_strike is flag-only in the schema; drop its text span but keep the flag
    res.hits.pop("no_strike", None)
    res.unresolved = [
        t for t in ("interest_arbitration", "comparability", "me_too")
        if not res.flags.get(t)
    ]
    return res


# ---------------------------------------------------------------------------
# Stage 2: LLM fallback (optional, verbatim-verified)
# ---------------------------------------------------------------------------

def _verify_verbatim(span: str, source: str) -> bool:
    """The LLM must return an exact quote. Normalize whitespace, then require
    the span to be a literal substring of the source. If not, we reject it —
    this is the anti-paraphrase guard."""
    if not span or len(span) < 15:
        return False
    norm = lambda s: re.sub(r"\s+", " ", s).strip().lower()
    return norm(span) in norm(source)


def llm_pass(text: str, missing: list[str], model: str = "gpt-5.4-nano") -> dict:
    """Ask the LLM to locate ONLY the missing clause types, returning exact
    quotes. Returns {clause_type: SpanHit}. Requires HARVARD_SUBSCRIPTION_KEY;
    returns {} if unavailable so the pipeline degrades gracefully."""
    if not missing:
        return {}
    api_key = os.environ.get("HARVARD_SUBSCRIPTION_KEY")
    if not api_key:
        return {}
    try:
        from openai import OpenAI
    except Exception:
        return {}

    client = OpenAI(
        api_key=api_key,
        base_url="https://go.apis.huit.harvard.edu/ais-openai-direct/v2",
        default_headers={"Ocp-Apim-Subscription-Key": api_key},
    )
    type_desc = {
        "interest_arbitration": "interest/binding arbitration of contract terms",
        "comparability": "comparability / prevailing-wage / parity to other jurisdictions",
        "me_too": "me-too / most-favored-nation clause tied to other bargaining units",
    }
    asks = "\n".join(f"- {t}: {type_desc[t]}" for t in missing if t in type_desc)
    prompt = (
        "You are extracting clauses from a municipal collective bargaining "
        "agreement for a research corpus. For each clause type below that is "
        "present in the TEXT, return the EXACT verbatim passage (a literal "
        "quote copied character-for-character from the text). Do NOT paraphrase, "
        "summarize, or alter wording in any way. If a clause type is absent, "
        "omit it.\n\n"
        "Return ONLY a JSON object: {\"clause_type\": {\"text\": \"<exact quote>\", "
        "\"referent\": \"<for comparability only: the exact phrase naming what "
        "wages are pegged to, else empty>\"}}. No prose, no markdown.\n\n"
        f"Clause types to find:\n{asks}\n\n"
        f"TEXT:\n{text[:50000]}"
    )
    try:
        resp = client.chat.completions.create(
            model=model, max_completion_tokens=1500,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = resp.choices[0].message.content or ""
        raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        data = json.loads(raw)
    except Exception:
        return {}

    out = {}
    for ctype, payload in data.items():
        if ctype not in missing:
            continue
        span = (payload or {}).get("text", "")
        if _verify_verbatim(span, text):   # anti-paraphrase guard
            out[ctype] = SpanHit(
                clause_type=ctype, text=span, method="llm",
                referent=(payload.get("referent", "") if ctype == "comparability" else ""),
            )
    return out


def extract_spans(text: str, run_llm_fallback: bool = False) -> ExtractionResult:
    res = regex_pass(text)
    if run_llm_fallback and res.unresolved:
        llm_hits = llm_pass(text, res.unresolved)
        for ctype, hit in llm_hits.items():
            res.hits[ctype] = hit
            res.flags[ctype] = 1
        res.unresolved = [t for t in res.unresolved if t not in llm_hits]
    return res
