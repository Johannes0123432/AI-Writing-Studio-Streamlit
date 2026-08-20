# AI Writing Studio

A Streamlit web application for drafting **articles**, **book chapters**, and **screenplays** with:

- Structured templates (original, non-copyrighted outlines)
- Style presets + optional reference sample
- Support for **Gemini**, **Grok (xAI)**, and **OpenRouter**
- Grammar checking (LanguageTool)
- Naturalness polishing pass (rhythm, sentence variation, reduced formulaic phrasing)
- Simple readability & variation metrics
- Industry-standard screenplay formatting guidance

## Important

This is a **drafting and polishing assistant**.  
It does **not** guarantee any particular AI-detector score.  
You are responsible for fact-checking, originality, and final editing.

---

## Local Quick Start

```bash
cd writing_studio
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Open the URL shown (usually http://localhost:8501).

---

## Deploy to Streamlit Community Cloud (recommended, free)

1. Push this folder to a **public or private GitHub repository**.
2. Go to [https://share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
3. Click **New app** → select your repo → set:
   - Main file path: `app.py`
   - Python version: 3.12 (or 3.11)
4. Click **Deploy**.

The app will be live at `https://<your-app-name>.streamlit.app`.

**Notes for Streamlit Cloud**
- Users still enter their own API keys in the sidebar (recommended).
- If you want to pre-set keys via secrets, create `.streamlit/secrets.toml` in the repo (do **not** commit real keys) or use the Cloud secrets UI.
- LanguageTool requires Java; Streamlit Cloud images usually have it, but if grammar check fails you can disable it or use a custom Docker deploy.

---

## Deploy to Hugging Face Spaces (free)

1. Create a new Space at [https://huggingface.co/new-space](https://huggingface.co/new-space).
2. Choose **Streamlit** as the SDK.
3. Upload / push all files from this folder (or connect the GitHub repo).
4. The Space will automatically detect `app.py` and `requirements.txt`.
5. After build, the app is available at `https://huggingface.co/spaces/<your-username>/<space-name>`.

You can also set secrets in the Space settings for optional default keys (still better to let users enter their own).

---

## Deploy with Docker (Render, Railway, Fly.io, your own server)

```bash
# Build
docker build -t writing-studio .

# Run locally
docker run -p 8501:8501 writing-studio
```

Then point any container platform at the image or the Dockerfile.

**Render / Railway example**
- Connect the GitHub repo.
- Set the build command to use the Dockerfile (or `pip install -r requirements.txt`).
- Start command: `streamlit run app.py --server.port=$PORT --server.address=0.0.0.0`
- Expose the correct port.

---

## API Keys

Users enter keys in the sidebar at runtime. Keys stay in the browser session only.

| Provider   | Get a key                              |
|------------|----------------------------------------|
| Gemini     | https://aistudio.google.com/app/apikey |
| Grok (xAI) | https://console.x.ai/                  |
| OpenRouter | https://openrouter.ai/keys             |

---

## Project Structure

```
writing_studio/
├── app.py                  # Main Streamlit app
├── requirements.txt
├── Dockerfile
├── README.md
├── .streamlit/
│   └── config.toml
├── templates/
│   └── structures.py       # Article / Book / Screenplay outlines
└── utils/
    ├── llm_clients.py      # Gemini, Grok, OpenRouter wrappers
    └── quality.py          # Grammar, metrics, polish prompts
```

---

## Features Overview

1. Choose project type → structure/template (defaults to the most common).
2. Select or describe writing style; optionally paste a style sample.
3. Provide title, topic, key points, length target.
4. Generate draft.
5. Optionally run grammar check or “Polish for Naturalness”.
6. Edit in place, download as .txt, review metrics.

Screenplays follow standard industry conventions (scene headings, character names in caps, present-tense action, etc.).

---

## Extending

- Add more structures in `templates/structures.py`
- Improve the humanize prompt or add embedding-based similarity checks in `utils/quality.py`
- Add more providers in `utils/llm_clients.py`
