# AI Engineering Lab

My practical work while following **AI Engineer Core Track: LLM Engineering,
RAG, QLoRA, Agents** by Ed Donner. Day 1 is a website summarizer using Gemini
through Google's OpenAI-compatible endpoint.

## Day 1 — Website briefing tool

Give the program a public webpage URL. Python downloads its HTML, Beautiful Soup
extracts readable text, and Gemini returns a Markdown briefing covering purpose,
intended audience, key points, and announcements.

My variation on the course example is a factual briefing with explicit handling
of missing information. The Python runner and notebook use the same prompts and
summarization function.

## Run it on Windows

For the default course website, double-click **`run_day1.bat`** after configuring
your `.env` as below. It installs the recorded dependencies and runs the program.

Alternatively, open a terminal in this repository:

```bat
uv sync --locked
```

Add or update these settings in your existing `.env` file in the project root.
If the file is missing, copy `.env.example` to `.env` first:

```dotenv
GEMINI_API_KEY=your_actual_key_here
GEMINI_MODEL=gemini-3.5-flash-lite
```

Replace the key placeholder with your own key, then run:

```bat
uv run python summarizer.py https://edwarddonner.com --output outputs/website_summary.md
```

The briefing appears in the terminal and is saved to `outputs/website_summary.md`.
You can replace the URL with another public HTML webpage. `uv run` selects the
project's Python environment automatically.

Inspect the extracted text and prepared prompts without making an AI request:

```bat
uv run python summarizer.py https://edwarddonner.com --preview
```

Select another model available to your Gemini project:

```bat
uv run python summarizer.py https://edwarddonner.com --model YOUR_GEMINI_MODEL
```

Google currently lists `gemini-3.5-flash-lite` with a free tier. Availability and quotas
depend on your project; this program does not change billing settings or switch
models automatically. See [Google's pricing](https://ai.google.dev/gemini-api/docs/pricing).

## Follow the notebook

Open [notebooks/01_llm_basics.ipynb](notebooks/01_llm_basics.ipynb) in Cursor.
Select this repository's `.venv` kernel and run the cells from top to bottom.
The notebook follows the course sequence:

1. Imports and project environment.
2. Load and check the Gemini key.
3. Prepare a greeting and make a first model call.
4. Fetch and inspect website text.
5. Inspect the system prompt, user prompt, and messages.
6. Summarize the page, display Markdown, and save the result.

Running every cell makes two model requests: the greeting and the website
summary. Restarting the kernel clears live variables; saving the notebook
preserves its code and displayed outputs.

| File | Responsibility |
| --- | --- |
| `scraper.py` | Retrieve and extract website text |
| `summarizer.py` | Prompts, Gemini client, summarization, and terminal entry point |
| `run_day1.bat` | Windows launcher for the default website |
| `notebooks/01_llm_basics.ipynb` | Course-aligned walkthrough using those functions |
| `.env.example` | Setting names and placeholders |
| `pyproject.toml`, `uv.lock` | Reproducible dependencies |
| `tests/test_day1.py` | Local HTTP integration checks |

## Checks

```bat
uv run python -m unittest discover -s tests -v
```

The tests use a local webpage and a local OpenAI-compatible HTTP endpoint. They
exercise extraction, actual SDK request/response handling, file output, and
error paths without contacting Gemini or needing a real key. They do not assess
the quality of real model-generated summaries.

Validation on 23 November 2026: all four integration tests passed; the live
course website was fetched successfully in preview mode; all 11 notebook code
cells executed in order in a fresh IPython session against local test endpoints.
A separate Jupyter kernel could not be launched in the build environment.
The live Gemini request still needs to be run with the user's own key.

## Limitations

- The scraper reads downloaded HTML; it does not render JavaScript or bypass
  login pages, paywalls, or anti-bot protection.
- The model sees at most the first 20,000 extracted characters from one page.
- Model output can be inaccurate; compare important claims with the source.
- `.env`, `.venv`, and generated `outputs/` are excluded from Git. The program
  reads the key from the project root and never prints it.

## Course attribution

The learning sequence and website-summary exercise come from Ed Donner's
**AI Engineer Core Track**. This is my course-based implementation, with Gemini
configuration, a factual briefing prompt, a terminal runner, documentation, and
local integration checks. The instructor's full notebook is not included.

- [Course resources](https://edwarddonner.com/2024/11/13/llm-engineering-resources/)
- [Gemini OpenAI compatibility](https://ai.google.dev/gemini-api/docs/openai)
- [Beautiful Soup documentation](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
