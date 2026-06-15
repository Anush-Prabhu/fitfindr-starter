# ThriftThread

**ThriftThread** is a multi-tool AI agent that helps you shop secondhand smarter. Describe what you want in plain English — the agent finds matching listings, suggests outfits from your wardrobe, and drafts a shareable fit card.

> Built for **AI201 Week 2** (*Show What You Know: FitFindr*). The assignment codename is **FitFindr**; **ThriftThread** is this implementation's project name.

📹 **Demo video:** *(add your Loom/YouTube link here)*

---

## Fork & attribution

This project is a **fork** of the AI201 course starter:

**[jamjamgobambam/ai201-project2-fitfindr-starter](https://github.com/jamjamgobambam/ai201-project2-fitfindr-starter)**

**What came from the starter:** mock data (`data/listings.json`, `data/wardrobe_schema.json`), `utils/data_loader.py`, project layout, and assignment scaffolding.

**What was implemented here:** `tools.py`, `agent.py`, `app.py`, `planning.md`, `tests/`, and documentation.

To fork and run yourself:

```bash
# 1. Fork jamjamgobambam/ai201-project2-fitfindr-starter on GitHub
# 2. Clone YOUR fork
git clone https://github.com/YOUR_USER/ai201-project2-fitfindr-starter.git thriftthread
cd thriftthread
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
# 3. Add GROQ_API_KEY to .env (see Setup below)
python app.py
```

---

## Setup

### Requirements

- Python 3.10+
- Free [Groq API key](https://console.groq.com) (model: `llama-3.3-70b-versatile`)

### Install

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Mac/Linux
pip install -r requirements.txt
```

Create `.env` in the project root (see `.env.example`):

```
GROQ_API_KEY=your_key_here
```

### Run

```bash
python app.py          # Gradio UI → http://localhost:7860
python agent.py        # CLI happy-path + no-results smoke test
pytest tests/          # 11 unit tests (LLM mocked, no API key needed)
```

### Example queries

| Query | Expected result |
|-------|-----------------|
| `vintage graphic tee under $30` | All 3 panels fill |
| `90s track jacket in size M` | Filtered search + outfit |
| `designer ballgown size XXS under $5` | Error only (no outfit/card) |

Price: `under $30`, `below 40`, `less than $25`, or bare `$30`.  
Size: use `size M` / `in size 8`; `XXS`/`XL` also work standalone.

---

## Tool inventory

### 1. `search_listings(description, size, max_price)`

- **Purpose:** Search and rank mock secondhand listings.
- **Inputs:**
  - `description` (`str`) — e.g. `"vintage graphic tee"`
  - `size` (`str | None`) — case-insensitive token match (`"M"` matches `"S/M"`)
  - `max_price` (`float | None`) — inclusive ceiling
- **Output:** `list[dict]` sorted by relevance (weighted keyword score). `[]` if no match — never raises.
- **Fields per listing:** `id`, `title`, `description`, `category`, `style_tags`, `size`, `condition`, `price`, `colors`, `brand`, `platform`

### 2. `suggest_outfit(new_item, wardrobe)`

- **Purpose:** LLM outfit ideas using wardrobe pieces or general advice when empty.
- **Inputs:**
  - `new_item` (`dict`) — listing from search
  - `wardrobe` (`dict`) — `{ "items": [...] }` per `wardrobe_schema.json`
- **Output:** `str` — non-empty styling suggestion (Groq, temperature 0.75)

### 3. `create_fit_card(outfit, new_item)`

- **Purpose:** Casual social-media caption for the outfit.
- **Inputs:** `outfit` (`str`), `new_item` (`dict`)
- **Output:** `str` — 2–4 sentence caption, or error message if `outfit` is empty

### 4. `estimate_price_fairness(new_item)` *(stretch)*

- **Purpose:** Compare price to same-category listings in the dataset (no LLM).
- **Output:** `{ verdict, item_price, median_comparable, sample_size, message }`
- **Verdicts:** `great_deal` / `fair` / `overpriced` / `unknown`

---

## Planning loop

`run_agent()` in `agent.py` runs a **linear pipeline** with two early-exit branches:

1. **Init** — `_blank_session(query, wardrobe)`
2. **Parse** — `parse_user_query()` → if empty description → `session["error"]`, return
3. **Search** — `search_listings()` → if `[]` → `session["error"]`, return *(skip outfit + fit card)*
4. **Select** — `selected_item = search_results[0]`
5. **Price check** — `estimate_price_fairness()` → `price_assessment`
6. **Outfit** — `suggest_outfit(selected_item, wardrobe)`
7. **Fit card** — `create_fit_card(outfit_suggestion, selected_item)`
8. **Return** session

The agent **does not** call all tools unconditionally — empty search stops before LLM tools run.

---

## State management

One `session` dict per interaction:

| Field | Written by | Read by |
|-------|------------|---------|
| `query` | init | parser |
| `parsed` | parse step | search |
| `search_results` | `search_listings` | select + error branch |
| `selected_item` | select step | outfit, fit card |
| `price_assessment` | price tool | UI listing panel |
| `wardrobe` | init | `suggest_outfit` |
| `outfit_suggestion` | `suggest_outfit` | `create_fit_card` |
| `fit_card` | `create_fit_card` | UI |
| `error` | early exits | UI |

Data flows: `search_results[0]` → `selected_item` → `outfit_suggestion` → `fit_card`. Tools never call each other directly.

---

## Error handling

| Tool | Failure | Response |
|------|---------|----------|
| `search_listings` | No matches | `[]`; agent sets actionable `session["error"]`; panels 2–3 blank |
| `suggest_outfit` | Empty wardrobe | General styling advice; pipeline continues |
| `create_fit_card` | Empty outfit | Descriptive error string; no exception |

**Tested example (no results):**  
Query `designer ballgown size XXS under $5` → error message, `fit_card` stays `None`, downstream tools not called.

**Tested example (empty outfit):**  
`create_fit_card("", item)` → *"No outfit to caption yet…"* — no crash.

---

## Spec reflection

**What worked well:** The three-tool pipeline maps cleanly to find → style → share. Session dict made state easy to verify in tests and the demo.

**Judgment calls:**
- No automatic size-filter retry — predictable behavior; error message tells user to drop size instead.
- Single-letter sizes (`S`/`M`/`L`) require the word `size` in the query to avoid misparsing conversational text.

**Known limitation:** Regex parser leaves filler words in long conversational queries; keyword scoring still ranks correctly for assignment example queries.

---

## AI usage

1. **`search_listings`** — Spec from `planning.md` + `load_listings()` docstring. Chose **weighted scoring** (title ×3, tags ×2, body ×1) instead of flat keyword counts.
2. **`run_agent`** — Planning loop diagram + session table from `planning.md`. Reviewed early-exit branches and confirmed downstream tools are skipped on empty search via `agent.py` CLI test.

---

## Project structure

```
thriftthread/
├── agent.py              # Planning loop + query parser
├── tools.py              # Four tools (3 required + price stretch)
├── app.py                # Gradio UI
├── planning.md           # Design spec (pre-implementation)
├── DOCUMENTATION.md      # Full technical documentation
├── DEMO_SCRIPT.md        # Demo video script
├── data/
│   ├── listings.json
│   └── wardrobe_schema.json
├── utils/
│   └── data_loader.py
├── tests/
│   └── test_tools.py
├── requirements.txt
├── .env.example
└── README.md
```

---

## Related docs

- **[DOCUMENTATION.md](DOCUMENTATION.md)** — architecture, API reference, testing, troubleshooting
- **[planning.md](planning.md)** — design spec and Mermaid diagram
- **[DEMO_SCRIPT.md](DEMO_SCRIPT.md)** — 3–5 min video recording script

---

## Course submission checklist

- [ ] Fork pushed to **your** GitHub
- [ ] `planning.md` in repo root
- [ ] `README.md` with all required sections (this file)
- [ ] Demo video (3–5 min) linked above
- [ ] `pytest tests/` passes
