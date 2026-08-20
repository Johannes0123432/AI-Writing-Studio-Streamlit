"""
Original, non-copyrighted structural templates for articles, books, and screenplays.
These are generic industry-standard outlines only — no copyrighted content.
"""

from __future__ import annotations

from typing import Dict, List

# ---------------------------------------------------------------------------
# ARTICLE STRUCTURES
# ---------------------------------------------------------------------------

ARTICLE_STRUCTURES: Dict[str, Dict] = {
    "Standard Feature / Narrative": {
        "description": "Classic long-form feature: hook → context → development → climax/insight → resolution.",
        "outline": [
            "Opening hook or anecdote",
            "Background / context / stakes",
            "Rising action / key developments or arguments",
            "Central insight, turning point, or climax",
            "Resolution, implications, and closing reflection",
        ],
        "default": True,
    },
    "Problem – Agitate – Solve (PAS)": {
        "description": "Popular persuasive structure: state the problem, amplify pain, present solution.",
        "outline": [
            "Clear statement of the problem",
            "Agitate: consequences, examples, emotional impact",
            "Introduce the solution / approach",
            "How it works (steps or evidence)",
            "Benefits and call to action / next steps",
        ],
    },
    "How-to / Tutorial": {
        "description": "Step-by-step instructional article.",
        "outline": [
            "Introduction: what the reader will achieve and why it matters",
            "Prerequisites / materials / assumptions",
            "Step-by-step instructions (numbered)",
            "Tips, common pitfalls, variations",
            "Conclusion and further resources",
        ],
    },
    "Listicle": {
        "description": "Numbered or bulleted list with explanatory paragraphs.",
        "outline": [
            "Engaging introduction that promises value",
            "List items (each with heading + explanation + example)",
            "Summary or ranking if appropriate",
            "Closing takeaway",
        ],
    },
    "News / Inverted Pyramid": {
        "description": "Most important information first, then supporting details.",
        "outline": [
            "Lead: who, what, when, where, why (most newsworthy facts)",
            "Key supporting details and quotes",
            "Background context",
            "Additional details / related information",
            "Least essential background",
        ],
    },
    "Opinion / Editorial": {
        "description": "Clear thesis + supporting arguments + counterpoints + conclusion.",
        "outline": [
            "Thesis / clear stance",
            "Supporting argument 1 + evidence",
            "Supporting argument 2 + evidence",
            "Address strongest counter-argument",
            "Reinforce thesis and call to action or reflection",
        ],
    },
    "Comparison / Review": {
        "description": "Side-by-side evaluation of options or a single product/service review.",
        "outline": [
            "Introduction and criteria for comparison",
            "Option / product A: strengths and weaknesses",
            "Option / product B (or alternatives)",
            "Direct comparison table or summary",
            "Recommendation and final verdict",
        ],
    },
    "Explainer / Q&A": {
        "description": "Break down a complex topic into clear questions and answers.",
        "outline": [
            "Why this topic matters now",
            "Core concept explanation",
            "Key questions answered one by one",
            "Common misconceptions",
            "Practical takeaways",
        ],
    },
}

# ---------------------------------------------------------------------------
# BOOK STRUCTURES
# ---------------------------------------------------------------------------

BOOK_STRUCTURES: Dict[str, Dict] = {
    "Three-Act Structure (Novel default)": {
        "description": "Classic beginning–middle–end for fiction. Most widely used commercial structure.",
        "outline": [
            "Act 1 – Setup: Ordinary world, inciting incident, first plot point",
            "Act 2A – Rising action / complications",
            "Midpoint: Major shift or revelation",
            "Act 2B – Further complications, lowest point",
            "Act 3 – Climax, resolution, new equilibrium",
        ],
        "default": True,
    },
    "Hero's Journey (simplified)": {
        "description": "Archetypal monomyth stages adapted for modern storytelling.",
        "outline": [
            "Ordinary World & Call to Adventure",
            "Refusal, Meeting the Mentor, Crossing the Threshold",
            "Tests, Allies, Enemies",
            "Approach to the Inmost Cave / Ordeal",
            "Reward, Road Back, Resurrection, Return with Elixir",
        ],
    },
    "Save the Cat! Beat Sheet (approx)": {
        "description": "Popular commercial screenplay-derived beat structure adapted for novels.",
        "outline": [
            "Opening Image & Theme Stated",
            "Setup & Catalyst",
            "Debate & Break into Two",
            "B Story & Fun and Games",
            "Midpoint & Bad Guys Close In",
            "All Is Lost & Dark Night of the Soul",
            "Break into Three, Finale, Final Image",
        ],
    },
    "Non-fiction: Problem → Solution": {
        "description": "Common structure for self-help, business, and practical non-fiction.",
        "outline": [
            "The problem and why it matters (reader pain)",
            "Root causes and failed approaches",
            "The core framework / method",
            "Detailed application chapters",
            "Case studies / results",
            "Implementation plan and next steps",
        ],
    },
    "Non-fiction: Chronological / Narrative": {
        "description": "History, biography, memoir, or process told in time order.",
        "outline": [
            "Opening scene or framing device",
            "Early period / origins",
            "Rising developments and turning points",
            "Climax or pivotal events",
            "Aftermath and lasting impact",
            "Reflection / lessons",
        ],
    },
    "Non-fiction: Thematic / Modular": {
        "description": "Each chapter explores a distinct theme or pillar while building a larger argument.",
        "outline": [
            "Overarching thesis and map of the book",
            "Theme / pillar chapters (each self-contained yet progressive)",
            "Synthesis chapter that ties themes together",
            "Practical application or manifesto close",
        ],
    },
    "Chapter Outline (flexible)": {
        "description": "Simple sequential chapter list — user supplies the actual chapter titles later.",
        "outline": [
            "Chapter 1: [Opening / Hook]",
            "Chapter 2–N: Rising development",
            "Climactic chapter(s)",
            "Resolution / final chapter",
        ],
    },
}

# ---------------------------------------------------------------------------
# SCREENPLAY FORMATTING RULES (industry standard)
# ---------------------------------------------------------------------------

SCREENPLAY_FORMAT_GUIDE = """
Use standard screenplay formatting conventions (Fountain-compatible / Final Draft style):

- Scene Headings (Sluglines): ALL CAPS. Format: INT./EXT. LOCATION - DAY/NIGHT
  Example: INT. COFFEE SHOP - DAY

- Action / Description: Present tense, concise, visual. Left-aligned.
  Never include camera directions unless essential.

- Character Names: ALL CAPS, centered (or left with proper margin in plain text).
  Appear immediately before their dialogue.

- Dialogue: Left-aligned under the character name. Natural speech.

- Parentheticals: (in parentheses) under character name, before dialogue.
  Use sparingly for essential acting notes only.

- Transitions: ALL CAPS, right-aligned when needed (CUT TO:, FADE OUT., etc.).
  Most modern scripts omit most transitions.

- Page length target: roughly 1 page ≈ 1 minute of screen time.

Always write in present tense. Keep action lines tight. Let dialogue and behavior reveal character.
"""

SCREENPLAY_STRUCTURES: Dict[str, Dict] = {
    "Three-Act Screenplay (default)": {
        "description": "Standard Hollywood three-act structure with approximate page ranges.",
        "outline": [
            "Act 1 (pp. 1–25/30): Setup, ordinary world, inciting incident, first act turn",
            "Act 2 (pp. 30–90): Confrontation, rising complications, midpoint, lowest point",
            "Act 3 (pp. 90–110/120): Climax, resolution, final image",
        ],
        "default": True,
    },
    "Five-Act / Television Hour": {
        "description": "Common for one-hour drama episodes with act-outs.",
        "outline": [
            "Teaser / Cold open",
            "Act 1",
            "Act 2",
            "Act 3",
            "Act 4",
            "Act 5 / Tag",
        ],
    },
    "Sequence Approach": {
        "description": "Eight sequences of roughly equal length that build the story.",
        "outline": [
            "Sequence 1: Status quo & disturbance",
            "Sequence 2: Rising action & first major turn",
            "Sequence 3–4: Development & midpoint",
            "Sequence 5–6: Complications & crisis",
            "Sequence 7–8: Climax & resolution",
        ],
    },
}


def get_default_structure(category: str) -> str:
    structures = {
        "Article": ARTICLE_STRUCTURES,
        "Book": BOOK_STRUCTURES,
        "Screenplay": SCREENPLAY_STRUCTURES,
    }.get(category, {})
    for name, data in structures.items():
        if data.get("default"):
            return name
    return next(iter(structures), "")


def get_structure_outline(category: str, name: str) -> List[str]:
    structures = {
        "Article": ARTICLE_STRUCTURES,
        "Book": BOOK_STRUCTURES,
        "Screenplay": SCREENPLAY_STRUCTURES,
    }.get(category, {})
    return structures.get(name, {}).get("outline", [])


def get_all_structures(category: str) -> Dict[str, Dict]:
    return {
        "Article": ARTICLE_STRUCTURES,
        "Book": BOOK_STRUCTURES,
        "Screenplay": SCREENPLAY_STRUCTURES,
    }.get(category, {})
