"""
AI Writing Studio — Streamlit app
Legitimate drafting assistant for articles, books, and screenplays.
Supports user ideas, structured templates, style control, grammar & naturalness polish.
Pricing model: $9 per 100 words  or  $75 / month subscription.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Make the app more resistant to ModuleNotFoundError on Streamlit Cloud.
# This ensures "templates" and "utils" are found even if the working directory differs.
ROOT_DIR = Path(__file__).parent.resolve()
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
from typing import List

from templates.structures import (
    ARTICLE_STRUCTURES,
    BOOK_STRUCTURES,
    SCREENPLAY_STRUCTURES,
    SCREENPLAY_FORMAT_GUIDE,
    get_default_structure,
    get_structure_outline,
    get_all_structures,
)
from utils.llm_clients import list_models, generate_text
from utils.quality import (
    check_grammar,
    compute_metrics,
    build_humanize_prompt,
    build_draft_system_prompt,
    adaptive_humanize,
)
from utils.payments import (
    PLANS,
    create_stripe_checkout_session,
    create_paypal_order,
    verify_stripe_session,
    is_payments_configured,
)

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="AI Writing Studio",
    page_icon="✍️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Minimal “after payment success” handler
# Reads ?session_id=… or ?payment=success from the URL and sets session flags.
# ---------------------------------------------------------------------------
def handle_payment_return():
    """
    Called once at the start of each run.
    When Stripe redirects back with ?session_id=cs_… we verify (stub for now)
    and set st.session_state flags so the rest of the app knows the user paid.
    """
    # Initialise flags if missing
    if "plan_active" not in st.session_state:
        st.session_state.plan_active = False
    if "paid_plan" not in st.session_state:
        st.session_state.paid_plan = None          # "payg_100" | "monthly_75" | None
    if "word_credits" not in st.session_state:
        st.session_state.word_credits = 0
    if "payment_message" not in st.session_state:
        st.session_state.payment_message = None

    # Modern Streamlit query params
    params = st.query_params

    session_id = params.get("session_id")
    payment_status = params.get("payment")

    # Already handled this session_id? Avoid re-processing on every rerun.
    if "last_handled_session_id" not in st.session_state:
        st.session_state.last_handled_session_id = None

    if session_id and session_id != st.session_state.last_handled_session_id:
        # Call the verification stub (will become real Stripe call later)
        result = verify_stripe_session(session_id)

        if result.get("paid"):
            # Real implementation will know the plan from the session metadata
            # For now we assume success means the user has an active plan
            st.session_state.plan_active = True
            st.session_state.paid_plan = result.get("plan_id") or "monthly_75"
            if st.session_state.paid_plan == "payg_100":
                st.session_state.word_credits = 100
            st.session_state.payment_message = (
                f"✅ Payment successful! Plan activated: {st.session_state.paid_plan}"
            )
        else:
            # Stub currently always returns paid=False – show informative message
            st.session_state.payment_message = (
                "Payment return detected (session_id present). "
                "Stripe verification is still a stub – connect your keys in "
                "utils/payments.py to activate plans automatically."
            )

        st.session_state.last_handled_session_id = session_id

        # Clean the URL so the message doesn’t reappear on every interaction
        # (Streamlit ≥ 1.30)
        try:
            st.query_params.clear()
        except Exception:
            pass

    elif payment_status == "success" and not session_id:
        st.session_state.payment_message = (
            "Payment success flag received. "
            "Add full Stripe session verification for production use."
        )
        try:
            st.query_params.clear()
        except Exception:
            pass

    elif payment_status == "cancelled":
        st.session_state.payment_message = "Payment was cancelled. You can try again anytime."
        try:
            st.query_params.clear()
        except Exception:
            pass


# Run the handler early
handle_payment_return()

# Show any payment-related message at the top
if st.session_state.get("payment_message"):
    if "successful" in st.session_state.payment_message.lower() or "✅" in st.session_state.payment_message:
        st.success(st.session_state.payment_message)
    else:
        st.info(st.session_state.payment_message)
    # Clear after showing once (optional – comment out if you want it to persist)
    # st.session_state.payment_message = None

# ---------------------------------------------------------------------------
# Helper: rough word count
# ---------------------------------------------------------------------------
def count_words(text: str) -> int:
    return len([w for w in text.split() if w.strip()])


# ---------------------------------------------------------------------------
# Hero / What the app can do + Pricing
# ---------------------------------------------------------------------------
st.title("✍️ AI Writing Studio")
st.markdown(
    """
**Turn your ideas into polished drafts** — articles, book chapters, industry-standard screenplays, and research writing with simulation support.

### What this app can do
- Accept **your own ideas, plot points, arguments, characters, research notes, or data descriptions** and turn them into structured writing
- Offer professional templates for articles, novels, non-fiction, and screenplays
- Let you choose (or describe) the writing style you want
- Generate a full draft using Gemini, Grok, or OpenRouter models
- Check grammar and polish the text for more natural rhythm and flow
- **For researchers**: help design simulations, suggest or review code, and guide you toward robust, reproducible results
- Give you an editable draft you can download and refine further

> **Always review the output.** You are responsible for facts, originality, scientific validity, and the final edit.
"""
)

st.divider()

# Pricing section
st.subheader("Pricing")

price_col1, price_col2 = st.columns(2)

with price_col1:
    st.markdown(
        """
#### Pay-as-you-go  
**$9 per 100 words**

- Perfect for testing or occasional use  
- You only pay for the words you generate  
- Ideal for short pieces and experiments
"""
    )
    st.info(
        "**Try it risk-free with a short piece**  \n"
        "Generate an article, scene, or short screenplay **under 100 words**.  \n"
        "This lets you experience the full workflow for the price of one small credit block."
    )

    # Payment buttons for pay-as-you-go
    pg1, pg2 = st.columns(2)
    with pg1:
        if st.button("Pay $9 with Stripe", key="stripe_payg", use_container_width=True):
            result = create_stripe_checkout_session(
                plan_id="payg_100",
                success_url="https://your-app-url.streamlit.app/?session_id={CHECKOUT_SESSION_ID}",
                cancel_url="https://your-app-url.streamlit.app/?payment=cancelled",
            )
            if result.get("url"):
                st.link_button("Continue to Stripe Checkout", result["url"])
            else:
                st.warning(result.get("message", "Stripe not yet connected."))
    with pg2:
        if st.button("Pay $9 with PayPal", key="paypal_payg", use_container_width=True):
            result = create_paypal_order(
                plan_id="payg_100",
                return_url="https://your-app-url.streamlit.app/?payment=success",
                cancel_url="https://your-app-url.streamlit.app/?payment=cancelled",
            )
            if result.get("approve_url"):
                st.link_button("Continue to PayPal", result["approve_url"])
            else:
                st.warning(result.get("message", "PayPal not yet connected."))

with price_col2:
    st.markdown(
        """
#### Monthly Subscription  
**$75 / month**

- Unlimited generation during the month*  
- Best for regular writers, freelancers, researchers, and teams  
- **Cancel anytime** — you keep access until the end of the paid period  
- After cancelling you can **reactivate any available plan** whenever you want
"""
    )
    st.caption("*Fair-use policy applies. Extremely high volume may be rate-limited.")

    # Payment buttons for monthly
    m1, m2 = st.columns(2)
    with m1:
        if st.button("Subscribe $75 / mo – Stripe", key="stripe_monthly", use_container_width=True):
            result = create_stripe_checkout_session(
                plan_id="monthly_75",
                success_url="https://your-app-url.streamlit.app/?session_id={CHECKOUT_SESSION_ID}",
                cancel_url="https://your-app-url.streamlit.app/?payment=cancelled",
            )
            if result.get("url"):
                st.link_button("Continue to Stripe Checkout", result["url"])
            else:
                st.warning(result.get("message", "Stripe not yet connected."))
    with m2:
        if st.button("Subscribe $75 / mo – PayPal", key="paypal_monthly", use_container_width=True):
            result = create_paypal_order(
                plan_id="monthly_75",
                return_url="https://your-app-url.streamlit.app/?payment=success",
                cancel_url="https://your-app-url.streamlit.app/?payment=cancelled",
            )
            if result.get("approve_url"):
                st.link_button("Continue to PayPal", result["approve_url"])
            else:
                st.warning(result.get("message", "PayPal not yet connected."))

st.markdown(
    """
**Subscription flexibility**  
You can cancel your monthly subscription at any time. After cancellation you retain access until the current billing period ends. You are always free to activate any available plan (pay-as-you-go or a new monthly subscription) later — there is no lock-in.

**How to start**  
1. Choose the **$9 / 100 words** plan if you want to test with a short piece (< 100 words).  
2. Or choose the **$75 monthly** plan for ongoing work.  
3. After payment (or while testing locally) enter your LLM API key in the sidebar and start writing.
"""
)

# Owner note about connecting real payments
with st.expander("For the app owner – how to connect Stripe & PayPal", expanded=False):
    st.markdown(
        """
**Current status**: Payment buttons are in place and call stub functions in `utils/payments.py`.  
They will show a “not yet connected” message until you add real keys.

### Stripe (recommended first)
1. Create account at https://dashboard.stripe.com  
2. Create a Product + recurring Price for the $75/month plan (copy the `price_…` ID).  
3. Get your **Secret key** and **Publishable key**.  
4. In Streamlit Cloud → App settings → Secrets, add:
   ```toml
   STRIPE_SECRET_KEY = "sk_live_…"
   STRIPE_PUBLISHABLE_KEY = "pk_live_…"
   ```
5. Open `utils/payments.py` and replace the TODO sections in  
   `create_stripe_checkout_session` and `verify_stripe_session` with real `stripe` library calls.  
6. Change the success/cancel URLs in the buttons above to your real app URL.  
7. (Optional but recommended) Add a Stripe webhook endpoint to reliably record successful payments.

### PayPal
1. Create a Business / Developer account at https://developer.paypal.com  
2. Create an app and obtain Client ID + Secret.  
3. Add them to Streamlit secrets.  
4. Implement the TODO in `create_paypal_order`.

### After payment succeeds
- Verify the session (Stripe) or capture the order (PayPal).  
- Set `st.session_state["plan"] = "monthly"` or add word credits.  
- Optionally store the customer/subscription ID in a small database (Supabase, Firebase, or even a simple JSON/SQLite file).

Once the stubs are replaced with real API calls, the existing buttons will start working without further UI changes.
"""
    )

st.divider()

# ---------------------------------------------------------------------------
# Sidebar — provider, keys, plan indicator
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("Your Plan")

    # Show real status if a payment has been processed
    if st.session_state.get("plan_active"):
        st.success(f"Active plan: **{st.session_state.get('paid_plan', 'unknown')}**")
        if st.session_state.get("word_credits", 0) > 0:
            st.write(f"Word credits remaining: **{st.session_state.word_credits}**")
    else:
        st.caption("No paid plan detected yet (demo mode).")

    selected_plan = st.radio(
        "Select plan (demo selector)",
        ["Test / Pay-as-you-go ($9 per 100 words)", "Monthly Subscription ($75)"],
        index=0,
        help="In a production version this is set automatically after Stripe/PayPal payment.",
    )

    if "Test" in selected_plan:
        st.info("Test mode — aim for under 100 words to try the workflow cheaply.")
    else:
        st.info("Monthly plan selected (demo).")

    st.divider()
    st.header("LLM Provider")
    provider = st.selectbox(
        "Provider",
        ["Gemini", "Grok", "OpenRouter"],
        help="Grok uses the xAI API. OpenRouter gives access to many models.",
    )

    api_key = st.text_input(
        f"{provider} API Key",
        type="password",
        help="Key stays in this browser session only. Never stored on a server.",
    )

    models = list_models(provider, api_key)
    model = st.selectbox("Model", models, index=0)

    st.divider()
    st.subheader("Generation Settings")
    temperature = st.slider("Temperature", 0.0, 1.2, 0.7, 0.05)
    max_tokens = st.slider("Max tokens", 512, 8192, 4096, 256)

    st.divider()
    st.markdown(
        """
**Notes**
- This tool helps you draft and polish. Final responsibility for accuracy and originality is yours.
- Grammar check uses LanguageTool.
- “Polish for Naturalness” improves rhythm — it is **not** an AI-detector bypass.
- Always verify facts.
"""
    )

# ---------------------------------------------------------------------------
# Main form — project type & structure
# ---------------------------------------------------------------------------
st.header("1. Choose what you want to create")

col1, col2 = st.columns([1, 1])

with col1:
    category = st.radio(
        "Project type",
        ["Article", "Book", "Screenplay"],
        horizontal=True,
    )

with col2:
    structures = get_all_structures(category)
    default_name = get_default_structure(category)
    structure_names = list(structures.keys())
    default_idx = structure_names.index(default_name) if default_name in structure_names else 0
    structure_name = st.selectbox(
        "Structure / Template",
        structure_names,
        index=default_idx,
        help=structures[structure_names[default_idx]]["description"],
    )

# Show outline
outline = get_structure_outline(category, structure_name)
with st.expander("Structure outline (what the model will follow)", expanded=False):
    for item in outline:
        st.markdown(f"- {item}")
    if category == "Screenplay":
        st.markdown("---")
        st.markdown(SCREENPLAY_FORMAT_GUIDE)

# ---------------------------------------------------------------------------
# Style
# ---------------------------------------------------------------------------
st.header("2. Choose the writing style")

style_presets = {
    "Clear professional (default)": "Clear, precise, professional prose. Varied sentence length. Avoid jargon unless necessary. Engaging but not flashy.",
    "Conversational / Friendly": "Warm, approachable, conversational tone as if explaining to a smart friend. Contractions OK. Light humor where appropriate.",
    "Journalistic / News": "Objective, concise, inverted-pyramid friendly. Active voice. Short paragraphs. Attribution for claims.",
    "Literary / Narrative": "Evocative, sensory, character-driven where relevant. Strong verbs, concrete images, controlled lyricism.",
    "Technical / Precise": "Exact terminology, logical flow, minimal ornamentation. Definitions for specialized terms.",
    "Academic (formal)": "Formal register, measured claims, hedging where evidence is incomplete. Clear structure and transitions.",
    "Humorous / Wry": "Dry wit, understatement, occasional playful asides. Still informative and structured.",
}

style_choice = st.selectbox("Reference style preset", list(style_presets.keys()), index=0)
custom_style = st.text_area(
    "Additional style notes (optional)",
    placeholder="e.g. Prefer short paragraphs, use American English, avoid passive voice…",
    height=80,
)

reference_sample = st.text_area(
    "Optional style sample (paste 200–800 words of writing whose voice you want imitated)",
    height=100,
    help="The model will imitate cadence and vocabulary level, not copy content.",
)

full_style = style_presets[style_choice]
if custom_style.strip():
    full_style += "\n\nAdditional notes: " + custom_style.strip()

# ---------------------------------------------------------------------------
# Research & Simulation helper (especially useful for research articles)
# ---------------------------------------------------------------------------
st.header("2b. Research & Simulation Helper (optional)")

st.markdown(
    """
For **research articles** the app can help you design simulations, suggest code, review your code, and reason about robustness and reproducibility.

**Important for trustworthy results**
- The app can **suggest** and **review** simulation code (usually Python with NumPy, SciPy, Pandas, Matplotlib, etc.).
- For safety and scientific integrity, **run the actual simulations in your own controlled environment** (local machine, Jupyter, Google Colab, institutional cluster, etc.).
- Always validate assumptions, random seeds, statistical methods, and sensitivity analyses yourself.
- Treat any numerical results the model discusses as illustrative until you have re-run and verified them.
"""
)

with st.expander("Open Research / Simulation assistant", expanded=False):
    sim_goal = st.text_area(
        "What do you want to simulate or analyse?",
        height=100,
        placeholder="e.g. Agent-based model of epidemic spread, Monte Carlo simulation of portfolio risk, ODE model of population dynamics, bootstrap confidence intervals for my experiment…",
    )
    sim_code_in = st.text_area(
        "Paste existing code here (optional) for review or improvement",
        height=150,
        placeholder="Paste Python code if you already have a draft simulation.",
    )
    sim_requirements = st.text_area(
        "Requirements for robust results (optional)",
        height=80,
        placeholder="e.g. Use fixed random seeds, report confidence intervals, include sensitivity analysis, prefer open-source libraries only…",
    )

    if st.button("Suggest / Review simulation code", key="sim_btn"):
        if not api_key.strip():
            st.error("Please enter an API key in the sidebar first.")
        elif not sim_goal.strip() and not sim_code_in.strip():
            st.error("Describe the simulation or paste some code.")
        else:
            with st.spinner("Working on simulation guidance…"):
                sim_system = """You are an expert scientific computing assistant.
Help the researcher design or improve a simulation that produces robust, reproducible, and trustworthy results.
Prefer clear, well-commented Python using widely available libraries (numpy, scipy, pandas, matplotlib, seaborn, networkx, etc.).
Always:
- Suggest fixed random seeds where randomness is used
- Recommend appropriate statistical summaries (means, CIs, effect sizes)
- Point out key assumptions and how to test sensitivity
- Warn about common pitfalls (pseudo-replication, multiple comparisons, etc.)
- Never claim results are final until the researcher has run and verified the code themselves
Return practical code and clear explanations. Do not invent data or fabricated numerical results presented as real findings.
"""
                sim_user = f"""Simulation / analysis goal:
{sim_goal}

Existing code (if any):
```python
{sim_code_in or "# none provided"}
```

Additional requirements for robustness:
{sim_requirements or "Standard good practices for reproducibility and statistical validity."}

Please suggest improved or complete code and explain how to interpret results responsibly.
"""
                try:
                    sim_reply = generate_text(
                        provider=provider,
                        api_key=api_key,
                        model=model,
                        system_prompt=sim_system,
                        user_prompt=sim_user,
                        temperature=0.4,
                        max_tokens=max_tokens,
                    )
                    st.markdown("#### Simulation guidance & code")
                    st.markdown(sim_reply)
                    st.info(
                        "Copy the code into your own environment (Jupyter, Colab, local IDE, etc.), "
                        "run it, inspect diagnostics, and only then incorporate verified results into your article."
                    )
                except Exception as e:
                    st.error(f"Simulation helper failed: {e}")

# ---------------------------------------------------------------------------
# USER IDEAS — the most important input
# ---------------------------------------------------------------------------
st.header("3. Your ideas & what the writing must include")

st.markdown(
    """
This is the most important section. Tell the app **exactly** what you want in the piece.
You can include plot points, arguments, characters, research notes, must-have facts, tone preferences, or any other instructions.
"""
)

title = st.text_input("Title / Working title")

topic = st.text_area(
    "Core idea, premise, or logline",
    height=100,
    placeholder="Describe the main idea in a few sentences.",
)

user_ideas = st.text_area(
    "Your detailed ideas, points, scenes, arguments, research notes, or simulation results to include",
    height=180,
    placeholder=(
        "Examples:\n"
        "- Main character is a tired detective who hates coffee\n"
        "- Must include the statistic that 40% of remote workers feel isolated\n"
        "- Scene should end with a cliffhanger about the missing USB drive\n"
        "- Argue that remote work increases productivity when done right\n"
        "- Include results from my Monte Carlo simulation (mean = 0.42, 95% CI …)\n"
        "- Keep the whole piece under 100 words for a quick test"
    ),
    help="The model will treat these as mandatory content to include.",
)

length_target = st.selectbox(
    "Approximate length target",
    [
        "Very short – under 100 words (great for testing the $9 plan)",
        "Short (~400–700 words)",
        "Medium (~800–1500 words)",
        "Long (~1500–3000 words)",
        "Chapter / Full scene (let model decide based on structure)",
        "Custom (specify in the ideas box above)",
    ],
    index=0,  # default to under 100 words to encourage testing
)

extra_instructions = st.text_area(
    "Any other instructions (audience, POV, things to avoid, etc.)",
    height=80,
)

# Live word-cost estimator
st.markdown("#### Estimated cost preview")
est_words = {
    "Very short – under 100 words (great for testing the $9 plan)": 80,
    "Short (~400–700 words)": 550,
    "Medium (~800–1500 words)": 1200,
    "Long (~1500–3000 words)": 2200,
    "Chapter / Full scene (let model decide based on structure)": 1500,
    "Custom (specify in the ideas box above)": 500,
}.get(length_target, 500)

blocks = max(1, (est_words + 99) // 100)
est_cost = blocks * 9

if "Test" in selected_plan or "Pay-as-you-go" in selected_plan:
    st.write(f"Rough estimate: ~**{est_words} words** → **{blocks}** blocks of 100 words → **${est_cost}**")
    if est_words <= 100:
        st.success("This length fits nicely in a single $9 test block.")
else:
    st.write("Monthly plan selected — generation is included (fair use).")

# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
st.divider()
generate = st.button("Generate Draft", type="primary", use_container_width=True)

if "draft" not in st.session_state:
    st.session_state.draft = ""
if "humanized" not in st.session_state:
    st.session_state.humanized = ""
if "metrics" not in st.session_state:
    st.session_state.metrics = {}
if "grammar_issues" not in st.session_state:
    st.session_state.grammar_issues = []

if generate:
    if not api_key.strip():
        st.error("Please enter an API key in the sidebar.")
    elif not topic.strip() and not title.strip() and not user_ideas.strip():
        st.error("Please provide at least a title, topic, or your ideas.")
    else:
        with st.spinner("Generating structured draft from your ideas…"):
            system_prompt = build_draft_system_prompt(
                category=category,
                structure_name=structure_name,
                outline=outline,
                style=full_style,
                reference_sample=reference_sample,
                extra_instructions=extra_instructions,
            )

            user_prompt = f"""Write a complete {category.lower()} draft based strictly on the user's ideas.

Title: {title or "(untitled)"}

Core idea / premise:
{topic}

USER'S DETAILED IDEAS AND MUST-INCLUDE CONTENT:
{user_ideas or "(none specified beyond the core idea)"}

Length guidance: {length_target}

Follow the structure and style instructions exactly.
Treat the user's ideas as mandatory — include them.
Do not invent major facts that contradict or go far beyond what the user provided.
Output only the draft itself (no meta commentary).
"""

            try:
                draft = generate_text(
                    provider=provider,
                    api_key=api_key,
                    model=model,
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                st.session_state.draft = draft
                st.session_state.humanized = ""
                st.session_state.metrics = compute_metrics(draft)
                st.success("Draft generated from your ideas. Review and edit below.")
            except Exception as e:
                st.error(f"Generation failed: {e}")

# ---------------------------------------------------------------------------
# Display & post-processing
# ---------------------------------------------------------------------------
if st.session_state.draft:
    st.header("Your Draft")
    draft_text = st.text_area(
        "Editable draft",
        value=st.session_state.draft,
        height=420,
        key="draft_area",
    )
    st.session_state.draft = draft_text

    # Metrics + actual word cost + adaptive naturalness score
    metrics = compute_metrics(draft_text)
    st.session_state.metrics = metrics
    actual_words = metrics.get("word_count", 0)
    actual_blocks = max(1, (actual_words + 99) // 100) if actual_words > 0 else 0
    actual_cost = actual_blocks * 9
    naturalness = metrics.get("naturalness_score", 0)

    mcols = st.columns(8)
    mcols[0].metric("Words", actual_words)
    mcols[1].metric("Sentences", metrics.get("sentence_count", 0))
    mcols[2].metric("Avg sent. len", metrics.get("avg_sentence_length", 0))
    mcols[3].metric("Sent. len std", metrics.get("sentence_length_std", 0),
                    help="Higher = more natural rhythm variation (burstiness)")
    mcols[4].metric("Unique word ratio", metrics.get("unique_word_ratio", 0))
    mcols[5].metric("AI-phrase hits", metrics.get("ai_tell_phrase_count", 0))
    mcols[6].metric("Naturalness", f"{naturalness}/100",
                    help="Local adaptive score (higher = more consistent human-like prose). Not a commercial AI detector.")
    mcols[7].metric("Est. cost", f"${actual_cost}" if "Test" in selected_plan or "Pay-as-you-go" in selected_plan else "Included")

    if naturalness >= 75:
        st.success(f"Local naturalness score: {naturalness}/100 — prose looks consistently human-like by internal metrics.")
    elif naturalness >= 55:
        st.info(f"Local naturalness score: {naturalness}/100 — acceptable, but Adaptive Polish can improve consistency.")
    else:
        st.warning(f"Local naturalness score: {naturalness}/100 — recommend running Adaptive Humanize for better integrity of voice.")

    if actual_words > 0 and actual_words <= 100:
        st.success(f"This draft is {actual_words} words — perfect for the $9 test block.")
    elif actual_words > 100 and ("Test" in selected_plan or "Pay-as-you-go" in selected_plan):
        st.warning(f"This draft is {actual_words} words ≈ {actual_blocks} blocks → ${actual_cost}.")

    if metrics.get("flesch_reading_ease") is not None:
        st.caption(
            f"Flesch Reading Ease: {metrics['flesch_reading_ease']:.1f} · "
            f"Grade level: {metrics.get('flesch_kincaid_grade', 'n/a')}"
        )

    # Action buttons
    b1, b2, b3, b4 = st.columns(4)

    with b1:
        if st.button("Run Grammar Check", use_container_width=True):
            with st.spinner("Checking grammar…"):
                corrected, issues = check_grammar(draft_text)
                st.session_state.draft = corrected
                st.session_state.grammar_issues = issues
                st.rerun()

    with b2:
        if st.button("Adaptive Humanize", use_container_width=True,
                     help="Multi-pass polish that adapts using the local naturalness score for consistent human-like prose"):
            if not api_key.strip():
                st.error("API key required for polishing.")
            else:
                with st.spinner("Running adaptive humanizer (up to 3 passes)…"):
                    try:
                        def _gen(system: str, user: str) -> str:
                            return generate_text(
                                provider=provider,
                                api_key=api_key,
                                model=model,
                                system_prompt=system,
                                user_prompt=user,
                                temperature=0.65,
                                max_tokens=max_tokens,
                            )

                        polished, history = adaptive_humanize(
                            text=draft_text,
                            generate_fn=_gen,
                            style_notes=full_style,
                            target_score=75,
                            max_passes=3,
                        )
                        st.session_state.humanized = polished
                        st.session_state.draft = polished
                        st.session_state.metrics = compute_metrics(polished)
                        st.session_state.humanize_history = history
                        st.rerun()
                    except Exception as e:
                        st.error(f"Adaptive humanize failed: {e}")

    with b3:
        if st.button("Show raw text", use_container_width=True):
            st.code(draft_text, language=None)

    with b4:
        st.download_button(
            "Download .txt",
            data=draft_text,
            file_name=f"{(title or 'draft').replace(' ', '_')[:40]}.txt",
            mime="text/plain",
            use_container_width=True,
        )

    if st.session_state.grammar_issues:
        with st.expander(f"Grammar / style issues found ({len(st.session_state.grammar_issues)})"):
            for issue in st.session_state.grammar_issues[:30]:
                st.markdown(f"- **{issue.get('message', '')}**")
                if issue.get("replacements"):
                    st.caption("Suggestions: " + ", ".join(issue["replacements"]))
            if len(st.session_state.grammar_issues) > 30:
                st.caption("… and more")

    if st.session_state.get("humanize_history"):
        with st.expander("Adaptive Humanize history (local naturalness scores)"):
            for step in st.session_state.humanize_history:
                st.write(f"Pass {step.get('pass')}: score **{step.get('score')}/100**")

    st.info(
        "Always fact-check any numbers or claims and perform a human edit pass. "
        "This tool improves structure and readability; it does not guarantee originality or detector scores."
    )
else:
    st.info("Fill in your ideas above and click **Generate Draft** to begin. Start with a short piece under 100 words to test the workflow.")
