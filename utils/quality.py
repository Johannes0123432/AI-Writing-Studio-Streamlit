"""
Quality helpers: grammar checking, adaptive naturalness scoring,
and an adaptive multi-pass humanizer focused on consistent, human-like prose integrity.

This is designed for writing quality and integrity — not for evading commercial AI detectors.
"""

from __future__ import annotations

import re
from typing import Dict, List, Tuple, Optional, Callable

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


# Expanded list of common formulaic / AI-typical phrases
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
    r"\bat the end of the day\b",
    r"\bwhen it comes to\b",
    r"\bin order to\b",
    r"\ba wide range of\b",
    r"\bit goes without saying\b",
    r"\bneedless to say\b",
    r"\bin this day and age\b",
    r"\bthe fact of the matter is\b",
    r"\bone of the most (?:important|significant)\b",
    r"\bhas become increasingly\b",
    r"\bserves as a (?:testament|reminder)\b",
    r"\bpaves the way for\b",
    r"\bleaves much to be desired\b",
]


def check_grammar(text: str) -> Tuple[str, List[Dict]]:
    """Return corrected text (best-effort) and list of issues."""
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
        corrected = language_tool_python.utils.correct(text, matches)
        return corrected, issues
    except Exception as e:
        return text, [{"message": f"Grammar check failed: {e}"}]


def compute_metrics(text: str) -> Dict:
    """Readability, variation, and local naturalness metrics."""
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

    ai_tell_count = 0
    for pattern in COMMON_AI_TELLS:
        ai_tell_count += len(re.findall(pattern, text, flags=re.IGNORECASE))

    try:
        flesch = textstat.flesch_reading_ease(text)
        grade = textstat.flesch_kincaid_grade(text)
    except Exception:
        flesch = None
        grade = None

    # Adaptive local naturalness score (0–100, higher = more human-like)
    # This is a heuristic for writing quality/integrity, NOT a commercial AI detector.
    naturalness = _compute_naturalness_score(
        avg_sent_len=avg_sent_len,
        std_dev=std_dev,
        unique_ratio=len(unique_words) / max(len(words), 1),
        ai_tell_count=ai_tell_count,
        word_count=len(words),
        flesch=flesch,
    )

    return {
        "word_count": len(words),
        "sentence_count": len(sentences),
        "avg_sentence_length": round(avg_sent_len, 1),
        "sentence_length_std": round(std_dev, 1),
        "unique_word_ratio": round(len(unique_words) / max(len(words), 1), 3),
        "ai_tell_phrase_count": ai_tell_count,
        "flesch_reading_ease": flesch,
        "flesch_kincaid_grade": grade,
        "naturalness_score": naturalness,          # 0–100, higher = more natural
        "ai_likeness_estimate": 100 - naturalness, # inverse for convenience
    }


def _compute_naturalness_score(
    avg_sent_len: float,
    std_dev: float,
    unique_ratio: float,
    ai_tell_count: int,
    word_count: int,
    flesch: Optional[float],
) -> int:
    """
    Local heuristic that rewards:
    - Sentence-length variation (burstiness)
    - Reasonable average sentence length
    - Lexical diversity
    - Few formulaic AI-tell phrases
    - Readable but not overly simplistic prose
    """
    score = 55.0  # baseline

    # Burstiness / sentence length variation (very important for natural rhythm)
    if std_dev >= 8:
        score += 18
    elif std_dev >= 5:
        score += 12
    elif std_dev >= 3:
        score += 6
    else:
        score -= 8

    # Average sentence length (human writing usually 12–22 words)
    if 12 <= avg_sent_len <= 22:
        score += 10
    elif 8 <= avg_sent_len <= 28:
        score += 4
    else:
        score -= 6

    # Lexical diversity
    if unique_ratio >= 0.55:
        score += 10
    elif unique_ratio >= 0.42:
        score += 5
    else:
        score -= 5

    # Penalize formulaic phrases (scaled by length)
    if word_count > 0:
        density = ai_tell_count / (word_count / 100)
        if density == 0:
            score += 8
        elif density < 0.5:
            score += 3
        elif density > 2:
            score -= 15
        else:
            score -= 7

    # Mild readability preference
    if flesch is not None:
        if 50 <= flesch <= 70:
            score += 5
        elif flesch < 30 or flesch > 90:
            score -= 4

    return max(0, min(100, int(round(score))))


def build_humanize_prompt(
    original: str,
    style_notes: str = "",
    previous_score: Optional[int] = None,
    target_score: int = 75,
) -> str:
    """
    Adaptive prompt focused on naturalness, rhythm, voice consistency,
    and writing integrity. Not optimized against commercial detectors.
    """
    feedback = ""
    if previous_score is not None:
        if previous_score < target_score:
            feedback = (
                f"\nThe previous version scored only {previous_score}/100 on local naturalness metrics. "
                "Increase sentence-length variation, reduce repetitive and formulaic phrasing, "
                "and make the rhythm feel more human and less uniform.\n"
            )
        else:
            feedback = (
                f"\nPrevious naturalness score was {previous_score}/100. "
                "Preserve the improvements while keeping meaning identical.\n"
            )

    return f"""You are an expert developmental editor focused on consistent, natural human prose and writing integrity.

Goals (in strict priority order):
1. Preserve every factual claim, name, number, quote, and the original meaning exactly. Do not invent or remove substance.
2. Produce writing that feels consistently human: varied sentence lengths, natural rhythm, concrete language.
3. Eliminate or replace formulaic transitions and stock phrases (e.g. "Moreover", "Furthermore", "It is important to note", "In today's digital world", "delve into", etc.).
4. Keep the requested style: {style_notes or "clear, professional, and engaging"}.
5. Do not add filler, new opinions, or padding.
{feedback}
Return ONLY the rewritten text. No commentary, no markdown fences.

TEXT TO REWRITE:
{original}
"""


def adaptive_humanize(
    text: str,
    generate_fn: Callable[[str, str], str],
    style_notes: str = "",
    target_score: int = 75,
    max_passes: int = 3,
) -> Tuple[str, List[Dict]]:
    """
    Adaptive multi-pass humanizer.
    Uses the local naturalness score as feedback to decide whether another pass is needed.
    generate_fn(system_prompt, user_prompt) -> str
    Returns (final_text, history_of_scores).
    """
    history = []
    current = text

    for i in range(max_passes):
        metrics = compute_metrics(current)
        score = metrics.get("naturalness_score", 50)
        history.append({"pass": i, "score": score, "metrics": metrics})

        if score >= target_score and i > 0:
            break

        prompt = build_humanize_prompt(
            original=current,
            style_notes=style_notes,
            previous_score=score if i > 0 else None,
            target_score=target_score,
        )
        system = "You are a careful developmental editor focused on natural, consistent human prose and integrity of meaning."
        try:
            current = generate_fn(system, prompt).strip()
            if not current:
                break
        except Exception:
            break

    final_metrics = compute_metrics(current)
    history.append({"pass": "final", "score": final_metrics.get("naturalness_score", 0), "metrics": final_metrics})
    return current, history


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
