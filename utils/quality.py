"""
Quality helpers: grammar checking, simple readability / AI-likeness heuristics,
and a naturalness-focused rewrite pass (not detector evasion).
"""

from __future__ import annotations

import re
from typing import Dict, List, Tuple

import textstat

try:
    import language_tool_python
    _tool = None

    def get_language_tool():
        global _tool
        if _tool is None:
            _tool = language_tool_python.LanguageTool("en-US")
        return _tool
except Exception:
    get_language_tool = None


# Common formulaic phrases that often appear in unedited LLM output
COMMON_AI_TELLS = [
    r"\bin conclusion\b",
    r"\bin summary\b",
    r"\bit is important to note\b",
    r"\bit is worth noting\b",
    r"\bin today's (?:fast-paced|digital|modern) world\b",
    r"\ba (?:myriad|plethora) of\b",
    r"\bunderscore[s]? the (?:importance|significance)\b",
    r"\bdelve(?:s|d)? into\b",
    r"\bnavigat(?:e|ing) the (?:complexities|landscape)\b",
    r"\bin the realm of\b",
    r"\bplay(?:s|ed) a crucial role\b",
    r"\bmoreover\b",
    r"\bfurthermore\b",
    r"\badditionally\b",
    r"\bto summarize\b",
    r"\blet's dive in\b",
    r"\bwithout further ado\b",
]


def check_grammar(text: str) -> Tuple[str, List[Dict]]:
    """
    Return corrected text (best-effort) and list of issues.
    Falls back gracefully if LanguageTool is unavailable.
    """
    if not get_language_tool:
        return text, [{"message": "LanguageTool not available – skipped grammar check"}]

    try:
        tool = get_language_tool()
        matches = tool.check(text)
        issues = []
        for m in matches:
            issues.append(
                {
                    "message": m.message,
                    "replacements": [r.value for r in m.replacements[:3]],
                    "offset": m.offset,
                    "errorLength": m.errorLength,
                    "context": m.context,
                }
            )
        # Apply automatic corrections where confident
        corrected = language_tool_python.utils.correct(text, matches)
        return corrected, issues
    except Exception as e:
        return text, [{"message": f"Grammar check failed: {e}"}]


def compute_metrics(text: str) -> Dict:
    """Simple readability and variation metrics."""
    if not text.strip():
        return {}

    sentences = re.split(r"[.!?]+", text)
    sentences = [s.strip() for s in sentences if s.strip()]
    words = re.findall(r"\b\w+\b", text.lower())
    unique_words = set(words)

    sent_lengths = [len(s.split()) for s in sentences] if sentences else [0]
    avg_sent_len = sum(sent_lengths) / len(sent_lengths) if sent_lengths else 0
    variance = (
        sum((l - avg_sent_len) ** 2 for l in sent_lengths) / len(sent_lengths)
        if len(sent_lengths) > 1
        else 0
    )
    std_dev = variance ** 0.5

    # Count common AI-ish phrases
    ai_tell_count = 0
    for pattern in COMMON_AI_TELLS:
        ai_tell_count += len(re.findall(pattern, text, flags=re.IGNORECASE))

    try:
        flesch = textstat.flesch_reading_ease(text)
        grade = textstat.flesch_kincaid_grade(text)
    except Exception:
        flesch = None
        grade = None

    return {
        "word_count": len(words),
        "sentence_count": len(sentences),
        "avg_sentence_length": round(avg_sent_len, 1),
        "sentence_length_std": round(std_dev, 1),  # higher = more burstiness
        "unique_word_ratio": round(len(unique_words) / max(len(words), 1), 3),
        "ai_tell_phrase_count": ai_tell_count,
        "flesch_reading_ease": flesch,
        "flesch_kincaid_grade": grade,
    }


def build_humanize_prompt(original: str, style_notes: str = "") -> str:
    """
    Prompt focused on naturalness, rhythm, and voice — NOT on detector scores.
    """
    return f"""You are an expert developmental editor. Rewrite the following text so it reads more naturally and human.

Goals (in priority order):
1. Preserve every factual claim, name, number, and the original meaning exactly.
2. Vary sentence length and structure (mix short punchy sentences with longer ones).
3. Reduce repetitive phrasing and overly uniform rhythm.
4. Prefer concrete, specific language over vague abstractions where possible.
5. Keep the requested style: {style_notes or "clear, professional, and engaging"}.
6. Do not add new facts, opinions, or filler. Do not remove important content.
7. Do not use clichéd transitions such as "Moreover", "Furthermore", "In conclusion", "It is important to note", etc. unless they truly fit the voice.

Return ONLY the rewritten text. No commentary.

TEXT TO REWRITE:
{original}
"""


def build_draft_system_prompt(
    category: str,
    structure_name: str,
    outline: List[str],
    style: str,
    reference_sample: str = "",
    extra_instructions: str = "",
) -> str:
    """System prompt that enforces structure, style, and anti-hallucination rules."""

    outline_str = "\n".join(f"- {item}" for item in outline)

    base = f"""You are a professional {category.lower()} writer and editor.

STRICT RULES:
- Follow the chosen structure exactly. Do not invent extra major sections unless necessary for coherence.
- Stick strictly to the facts, details, and constraints provided by the user. If information is missing, note it clearly with [NEEDS RESEARCH] or [ASSUMPTION] rather than inventing.
- Never fabricate quotes, statistics, studies, or specific events.
- Match the requested writing style closely.
- Produce clean, well-formatted output ready for further editing.
- For screenplays: use industry-standard formatting (scene headings in ALL CAPS, character names in ALL CAPS before dialogue, present-tense action lines, sparse parentheticals).

STRUCTURE TO FOLLOW ({structure_name}):
{outline_str}

STYLE GUIDANCE:
{style}
"""

    if reference_sample.strip():
        base += f"""

REFERENCE STYLE SAMPLE (imitate the voice, cadence, and vocabulary level — do not copy content):
\"\"\"
{reference_sample[:1500]}
\"\"\"
"""

    if category == "Screenplay":
        base += """

SCREENPLAY FORMATTING REQUIREMENTS:
- Scene headings: INT./EXT. LOCATION - TIME
- Action in present tense, concise and visual
- CHARACTER NAMES in ALL CAPS immediately before dialogue
- Dialogue natural and character-specific
- Parentheticals only when essential
- Aim for roughly one page per minute of screen time
"""

    if extra_instructions.strip():
        base += f"\n\nADDITIONAL USER INSTRUCTIONS:\n{extra_instructions}"

    return base
