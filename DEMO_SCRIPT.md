# FitFindr — Demo Video Script (3–5 min)

Use this while recording. Show your **terminal**, **browser (Gradio UI)**, and optionally **`planning.md`** / **`agent.py`** for state-passing proof.

**Before you record**
- [ ] `python app.py` running → open http://localhost:7860
- [ ] Wardrobe set to **Example wardrobe**
- [ ] Close unrelated tabs/notifications
- [ ] Mic check — speak slowly and point at the screen

---

## PART 1 — Intro (0:00 – 0:30)

**ON SCREEN:** Gradio home page (empty panels)

**SAY:**
> "This is FitFindr, my AI201 Week 2 project. It's a multi-tool agent that helps you thrift: it searches secondhand listings, suggests outfits from your wardrobe, and writes a shareable fit card. Behind the UI, three tools run in a planning loop with session state passing results from one step to the next."

**OPTIONAL ON SCREEN:** Flash `planning.md` Architecture diagram for 3 seconds.

---

## PART 2 — Happy path: all 3 tools (0:30 – 2:30)

This is the **required** full workflow. Type exactly:

### Query to type
```
vintage graphic tee under $30
```

**Wardrobe:** `Example wardrobe`  
**Click:** `Find it`

---

### Step A — Parse + Search (Tool 1)

**ON SCREEN:** Query in the box → click Find it → **Top listing** panel fills first.

**SAY:**
> "When I submit this query, the agent doesn't jump straight to the LLM. First, `run_agent` in `agent.py` parses my text and extracts a description, optional size, and max price. Here that's 'vintage graphic tee' and under thirty dollars."

> "Then it calls **Tool 1: `search_listings`**. That filters the mock dataset by price and size, scores listings by keyword match, and returns the best hit. You can see the top listing in the first panel — title, price, size, platform, and a price-fairness note from the extra credit tool."

**POINT AT:** First panel — title, `$24`, `depop`, price assessment line.

**STATE TO MENTION:**
> "That listing is stored in the session as `selected_item`. The search results list is in `search_results`, and we take index zero as the winner."

---

### Step B — Outfit suggestion (Tool 2)

**ON SCREEN:** **Outfit idea** panel (middle column)

**SAY:**
> "Next, **Tool 2: `suggest_outfit`** runs. It receives the **same** `selected_item` from the session plus my wardrobe — not a re-typed description. The LLM reads the thrift find and names actual wardrobe pieces, like baggy jeans or chunky sneakers."

**POINT AT:** Middle panel — outfit text mentioning wardrobe items.

**STATE TO MENTION:**
> "The outfit string is saved in `session['outfit_suggestion']` and passed directly into the next tool."

---

### Step C — Fit card (Tool 3)

**ON SCREEN:** **Fit card** panel (right column)

**SAY:**
> "Finally, **Tool 3: `create_fit_card`** turns that outfit into a casual social caption. It uses the outfit text and the same listing for name, price, and platform. All three tools ran in order: search, suggest, fit card."

**POINT AT:** Right panel — caption mentioning item name, price, platform.

---

### Optional: prove state passing (30 sec)

**ON SCREEN:** Terminal — run:
```bash
cd E:\AI201\w2
.venv\Scripts\activate
python agent.py
```

**SAY:**
> "I can also run the agent from the CLI. The happy path prints the selected item title, outfit, and fit card from one session object — same pipeline as the UI, no hardcoded values between steps."

**SHOW:** Terminal output with item title + outfit + fit card snippets.

---

## PART 3 — Failure mode (2:30 – 3:30)

**Required:** at least one graceful failure.

### Query to type
```
designer ballgown size XXS under $5
```

**Wardrobe:** `Example wardrobe` (either is fine)  
**Click:** `Find it`

**ON SCREEN:** Error message in **first panel only**; outfit and fit card panels **blank**.

**SAY:**
> "This query is designed to fail on purpose. `search_listings` returns an empty list — nothing matches a designer ballgown in XXS under five dollars."

> "The planning loop checks for empty results, sets `session['error']` with a helpful message, and **returns early**. It does **not** call `suggest_outfit` or `create_fit_card`. That's the branch in my planning loop — the agent behaves differently when search fails."

**POINT AT:** Error text suggesting to raise budget or drop size filter.  
**POINT AT:** Empty middle and right panels.

---

### Optional: tool-level failure in terminal (15 sec)

**ON SCREEN:** Terminal:
```bash
python -c "from tools import create_fit_card; from utils.data_loader import load_listings; item = [l for l in __import__('utils.data_loader').data_loader.load_listings() if 'graphic' in l['title'].lower()][0]; print(create_fit_card('', item))"
```

Or simpler — from project root with venv active:
```bash
python -c "from tools import create_fit_card; print(create_fit_card('', {'title':'Test Tee','price':10,'platform':'depop'}))"
```

**SAY:**
> "`create_fit_card` also handles bad input — an empty outfit returns an error string instead of crashing the app."

---

## PART 4 — Empty wardrobe (optional, 3:30 – 4:00)

Shows second failure mode from the rubric.

### Query
```
vintage graphic tee under $30
```

**Wardrobe:** `Empty wardrobe (new user)`  
**Click:** `Find it`

**SAY:**
> "With an empty wardrobe, `suggest_outfit` doesn't crash. It switches to general styling advice, and the pipeline still produces a fit card."

**POINT AT:** Outfit panel — generic pairing advice, not named wardrobe pieces.

---

## PART 5 — Wrap-up (4:00 – 4:30)

**ON SCREEN:** All three panels from happy path, or `README.md` / `planning.md`

**SAY:**
> "To recap: three tools with defined interfaces, a planning loop that branches on empty search results, session state connecting each step, and error handling so the agent stays useful when something breaks. Tests are in `tests/test_tools.py` — eleven passing with the LLM mocked. Code and `planning.md` are in my GitHub repo."

---

## Quick reference — queries & what to show

| # | Query | Wardrobe | What happens | Show |
|---|--------|----------|--------------|------|
| 1 | `vintage graphic tee under $30` | Example | All 3 panels fill | **Main demo** |
| 2 | `designer ballgown size XXS under $5` | Either | Error only, panels 2–3 empty | **Required failure** |
| 3 | `vintage graphic tee under $30` | Empty | General styling advice | Optional |
| 4 | `90s track jacket in size M` | Example | Another happy path | Optional variety |

---

## Narration cheat sheet (tool names)

| Step | Tool | Session field written | Session field read next |
|------|------|----------------------|-------------------------|
| Parse | (agent) | `parsed` | → search args |
| Search | `search_listings` | `search_results` | → `selected_item` |
| Select | (agent) | `selected_item` | → outfit + fit card |
| Outfit | `suggest_outfit` | `outfit_suggestion` | → fit card |
| Caption | `create_fit_card` | `fit_card` | → UI |

---

## Assignment checklist (verify before upload)

- [ ] Video is **3–5 minutes**
- [ ] **All 3 tools** used in one happy-path query
- [ ] You **name each tool** and what it does while it runs
- [ ] You explain **state passing** (`selected_item`, `outfit_suggestion`)
- [ ] **One failure** shown (ballgown query recommended)
- [ ] Repo has `planning.md` + `README.md`
- [ ] Demo link pasted in README when done

---

## Recording tips

- Record at 1080p; zoom browser to 125% if text is small.
- Use Loom, OBS, or Windows Game Bar (Win + G).
- Do happy path **first**, failure **second** — graders look for both.
- If the LLM is slow, keep talking: "The agent is calling Groq for outfit suggestions now…"
