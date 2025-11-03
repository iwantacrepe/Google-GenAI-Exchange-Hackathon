#  Legal Document Demystifier
[Deployed Pod](https://nyay-sahayak-amf4b3bcfkehbbgq.centralindia-01.azurewebsites.net)

**Make court orders and case files understandable in minutes.**
Upload a PDF (or image/DOCX), and the app builds a full workspace with:

* a clear **case summary**,
* simplified **legal terms**,
* a **timeline** of events (even when dates are missing),
* an **entity relationship graph** backed by **Neo4j**,
* **related / landmark cases** to read next,
* an **at-a-glance** one-pager, and
* a **pre-hearing readiness pack** for “what to say tomorrow”.

Built with **Flask + Gemini** (Google GenAI), **D3 / vis-timeline** on the frontend, and **Neo4j** for graph storage.

##  Why this exists

Indian court orders are long, jargon-heavy, and hard to scan before a hearing. This project turns a single upload into a set of actionable views so a lawyer/litigant can:

* grasp the **core story** fast,
* understand **terms** without flipping textbooks,
* see the **sequence** of what happened,
* map **people / places / entities** as a **graph**,
* read **similar / landmark cases** quickly,
* and prepare **arguments & exhibits** for the **very next hearing**.



##  Agents (What each one does)

All agents are in `agents/` and respond in the selected language.

1. **`summarizer_agent.py` – Case Summarizer**

   * Uploads the file to Gemini and returns a **structured Markdown** summary: overview, parties, issues, arguments, reasoning, decision, dates, takeaways.

2. **`jargons_agent.py` – Legal Term Simplifier**

   * Extracts legal terms / sections / citations and explains them in plain language.

3. **`timeline_agent.py` – Case Timeline**

   * Builds a **chronological** timeline from the document.
   * If explicit dates are missing, it **infers stages** (`Stage 1`, `Stage 2`, …).
   * Frontend uses **vis-timeline**; “Stage N” gets a safe **placeholder date** (Jan N, 2000) so the chart always renders.

4. **`graph_agent.py` – Case Relationship Graph**

   * Extracts **entities** (people, courts, police, events) and **relations**.
   * Returns a JSON `{ nodes, edges }` used by a **D3 force graph**.
   * If Neo4j env vars are set, it can **persist** entities/edges to **Neo4j Aura** for exploration later (Bloom/Browser).

5. **`related_cases_agent.py` – Related / Landmark Cases**

   * Uses the current case context to fetch a **curated list** of relevant Indian cases (by topic/sections/issues).
   * Returns a Markdown list with short summaries / why it’s relevant.

6. **`at_a_glance_agent.py` – At-a-Glance Summary**

   * A **one-pager**: who/what/why/where/when, key issues, ruling, and 5–7 bullet takeaways.

7. **`readiness_agent.py` – Pre-Hearing Readiness**

   * Generates a **checklist for tomorrow**: critical points, likely questions, evidence references, statutory hooks, risks, and a mini oral-argument outline.

8. **`thinker_agent.py` – Interactive Legal Assistant**

   * A chat agent that answers follow-ups about the uploaded file.
   * The chat box shows a **placeholder** (“How can I help you today?”) until the first message.

##  UI Panels (what you see)

* **Agents** (left sidebar) – now includes **Change Language** link and panels for:
  *At-a-Glance • Summarizer • Jargons • Timeline • Graph • Pre-Hearing Readiness • Related Cases • Thinker*

* **Markdown rendering** via `marked + DOMPurify`

* **Timeline** via `vis-timeline` with safe fallbacks for “Stage” dates

* **Graph** via `D3` force-directed layout (noise filtering for IPC/CrPC section-only nodes)

##  How the Timeline works

* `timeline_agent.py` asks Gemini to output **only** a JSON array.
* When dates are missing, Gemini emits `"date": "Stage N"`.
* In `dashboard.html` the code **maps “Stage N” → placeholder dates** (`2000-01-N`) so `vis.Timeline` **always** has a valid `start`.
* Examples of stages used when scant content is available:

  * Complaint / Incident → FIR → Investigation → Arrest / Charges → Hearings → Arguments → Judgment → Appeal.

##  How the Graph + Neo4j works

* `graph_agent.py` extracts **nodes** (`{ id, name, label }`) and **edges** (`{ source, target, relation }`).
* Frontend filters out noise (e.g., raw “Section 420 IPC” nodes) and renders the rest with **D3**.
* If the Neo4j env vars are provided, the agent will **upsert** nodes/edges to **Neo4j Aura**.

  * Useful for **querying cross-case patterns**, reusing parties, and exploring networks in **Neo4j Bloom**.

##  Project structure

```
.
├── agents/
│   ├── at_a_glance_agent.py
│   ├── graph_agent.py
│   ├── jargons_agent.py
│   ├── readiness_agent.py
│   ├── related_cases_agent.py
│   ├── summarizer_agent.py
│   ├── thinker_agent.py
│   └── timeline_agent.py
├── services/
│   └── gemini_client.py
├── static/
│   ├── app.js
│   └── style.css
├── templates/
│   ├── dashboard.html
│   ├── loading.html
│   └── welcome.html
├── uploads/                 # files saved during a session (container-safe: /tmp in prod)
├── app.py
├── Dockerfile
├── gunicorn.conf.py
├── requirements.txt
└── README.md
```

##  Tech stack

* **Backend**: Flask, Gunicorn
* **GenAI**: Google **Gemini** (via `google-genai` / `google.ai.generativelanguage`)
* **Graph DB**: **Neo4j** (optional, via official Python driver)
* **Frontend**: HTML, CSS, **D3**, **vis-timeline**, **marked + DOMPurify**
* **Runtime**: Docker (local & Azure Web App for Containers)

## Environment variables

Create a `.env` (or configure in your container environment):

```
GEMINI_API_KEY=your_google_generative_ai_key

# Neo4j (optional, enables graph persistence)
NEO4J_URI=neo4j+s://<your-aura-hostname>        # e.g., neo4j+s://xxxx.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=********
NEO4J_DATABASE=neo4j
AURA_INSTANCEID=<optional for ops/observability>
```

> If both `GOOGLE_API_KEY` and `GEMINI_API_KEY` are present, the code prefers `GEMINI_API_KEY`.

## Run locally (no Docker)

Requirements: Python 3.11+

```bash
git clone https://github.com/iwantacrepe/Google-GenAI-Exchange-Hackathon.git
cd Google-GenAI-Exchange-Hackathon

python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt

# Set envs (PowerShell)
$env:GEMINI_API_KEY="YOUR_KEY"
# (Optionally) Neo4j envs here too

# Run with Flask’s built-in (dev)
python app.py
# or run with Gunicorn (recommended):
gunicorn -c gunicorn.conf.py app:app
```

Open [http://localhost:8080](http://localhost:8080) (Gunicorn) or the port shown by Flask if using dev server.

## Run with Docker (recommended)

Build:

```bash
docker build -t <image_name> .
```

Run:

```bash
docker run --rm -p 8080:8080 ^
  -e GEMINI_API_KEY=YOUR_KEY ^
  -e NEO4J_URI=neo4j+s://xxxx.databases.neo4j.io ^
  -e NEO4J_USERNAME=neo4j ^
  -e NEO4J_PASSWORD=******** ^
  -e NEO4J_DATABASE=neo4j ^
  <<image_name>
```

Health check:

```bash
curl http://localhost:8080/healthz
# -> OK
```

> The app writes uploads to `/tmp/uploads` in containers (see `app.py`). Azure and other platforms treat `/tmp` as writable ephemeral storage.

##  Deploy to **Azure Web App for Containers**

1. Push your image to a registry (Docker Hub or ACR).

   ```bash
   docker build -t <image_name>:latest .
   docker push <image_name>:latest
   ```
2. Create an **Azure Web App** → **Docker** → **Single container** → point to your image.
3. **App settings** (Configuration → Application settings):

   * `GEMINI_API_KEY=...`
   * (Optional) `NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD, NEO4J_DATABASE`
4. **Health check**: Settings → Health check → Path: `/healthz`
5. **Port**: the container listens on **`8080`** (set by `gunicorn.conf.py`).
6. Browse your Web App URL.

> If you see 504/timeout on `/dashboard`, check outbound access to Gemini and increase Gunicorn `timeout` (already **180s** in `gunicorn.conf.py`). The readiness/related-cases/timeline calls upload to Gemini and may take longer on large PDFs.

##  HTTP API (used by the frontend)

* `POST /api/glance` → At-a-Glance Markdown
* `POST /api/summarizer` → Full summary Markdown (also preloaded into `#summary-content`)
* `POST /api/jargons` → Terms & explanations Markdown
* `POST /api/timeline` → `[{ date, title, description }]` JSON (stringified)
* `POST /api/graph` → `{ nodes, edges }` JSON (stringified)
* `POST /api/related_cases` → Related cases Markdown
* `POST /api/readiness` → Readiness Markdown
* `POST /api/thinker_chat` → `{ reply }` (chat)
* `GET  /healthz` → `"OK"`

##  Frontend notes

* Sidebar is translated at runtime from `translations` in `dashboard.html`.
* **Default active panel** is **Summarizer**. (If you prefer “At-a-Glance” first, move the `active` class to `#glance` and the corresponding list item.)
* The **Thinker chat** shows a background placeholder **“How can I help you today?”** until the first message.

##  Troubleshooting

* **Timeline blank?**
  Make sure your `dashboard.html` is using the **fixed mapping** for `"Stage N"` to placeholder dates. Items with `undefined` start will not render.

* **504 GatewayTimeout on Azure**

  * Ensure outbound network allows access to Gemini API.
  * Keep **`timeout = 180`** in `gunicorn.conf.py`.
  * Large PDFs or slow networks can hit timeouts; consider smaller uploads.

* **Neo4j not showing data**

  * Confirm env vars are correct and **TLS** (`neo4j+s://`).
  * Check that the graph agent’s persistence branch is enabled in your code (some deployments only return JSON by design).

* **Uploads path**

  * In containers, files go to **`/tmp/uploads`**. This is **ephemeral** and cleared on restart.

##  Acknowledgements

* Google **Gemini** for LLM capabilities
* **Neo4j Aura** for graph storage
* **D3** and **vis-timeline** for rich visualization


