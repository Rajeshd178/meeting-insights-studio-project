# Meeting Studio — Python AI Meeting Intelligence & Diarization

A modular, production-ready Python meeting intelligence studio divided into clean **backend**, **frontend**, and **environment configuration** layers.

Powered by a 3-model AI architecture:
- 🎙️ **Model 1: `gpt-4o-transcribe-diarize`** — Audio transcription, speaker diarization, and timestamp alignment.
- 📐 **Model 2: `text-embedding-3-small`** — Dense semantic embeddings for high-speed RAG vector chunk retrieval.
- 🧠 **Model 3: `gpt-4.1-mini`** — Multi-step executive summarization, action item & decision extraction, AI Critic verification, and grounded Q&A chat.

---

## 📁 Clean Architectural Separation

```
meeting-studio-main/
├── envs/                               # 🔑 Dedicated API Keys & Environment Folder
│   ├── .env                            # Active environment configuration (Add your OPENAI_API_KEY here)
│   └── .env.example                    # Template with instructions
│
├── backend/                            # ⚙️ All Python Backend Services & APIs
│   ├── app.py                          # Flask application & REST API routes
│   ├── config.py                       # Automatic environment loader (reads envs/.env)
│   ├── ai_service.py                   # Orchestrator for the 3 AI models
│   ├── rag.py                          # Vector retrieval, PII redaction & safety defenses
│   ├── models.py                       # Dataclasses & type schemas
│   ├── sample_data.py                  # Preloaded enterprise meeting datasets
│   ├── store.py                        # In-memory persistence & query layer
│   ├── requirements.txt                # Backend dependencies
│   └── uploads/                        # Audio/transcript storage directory
│
├── frontend/                           # 🎨 All Presentation & UI Assets
│   ├── templates/                      # Glassmorphic HTML templates
│   │   ├── base.html                   # Layout, sidebar, active models status pill
│   │   ├── dashboard.html              # Metrics, recent meetings, quick actions
│   │   ├── upload.html                 # 4-stage pipeline stepper
│   │   ├── meeting_detail.html         # 8-tab view (Transcript, Summary, Tasks, etc.)
│   │   ├── ask_all.html                # Cross-meeting RAG search engine
│   │   ├── brief.html                  # Executive daily brief rollup
│   │   ├── cost.html                   # Model usage & cost tracking dashboard
│   │   └── evaluation.html             # Quality & anti-hallucination metrics
│   └── static/
│       ├── css/style.css               # Dark-mode glassmorphic design system
│       └── js/main.js                  # Tabs, live chat, task toggle interactions
│
├── app.py                              # Root entry point (delegates to backend/app.py)
├── requirements.txt                    # Top-level dependencies
└── run.py                              # Root workspace launcher
```

---

## ⚡ Quick Start

### 1. Configure Your API Key in `envs/`
Open [envs/.env](envs/.env):
```ini
OPENAI_API_KEY=sk-your-openai-api-key-here

# The 3 Configured Models:
MODEL_TRANSCRIBE_DIARIZE=gpt-4o-transcribe-diarize
MODEL_EMBEDDING=text-embedding-3-small
MODEL_CHAT_ANALYSIS=gpt-4.1-mini
```
> *Note: If an API key is not yet set, the app runs in Demo Mode with full realistic enterprise samples.*

### 2. Install Requirements
```bash
pip install -r requirements.txt
```

### 3. Launch Meeting Studio
You can start the server using either:
```bash
python app.py
```
or directly from the backend:
```bash
python backend/app.py
```
Open **http://127.0.0.1:5000** in your browser.

---

## 🌟 Advanced Intelligence Features (Prompts A – I)

Meeting Insights Studio includes an enterprise suite of advanced accountable meeting intelligence:

### 1. Commitment Strength & Accountability (Prompt A)
- **Hedge-Word Lexicon & Rule Engine**: Evaluates action items using a lexical hedge detector (`maybe`, `probably`, `someone`, `at some point`, `we should`) combined with owner and deadline presence.
- **Commitment Chips**: Color-coded badges on every action item (`firm` in emerald, `soft` in amber, `vague` in red) with detailed tooltip explanations.
- **Filter**: 1-click filter for "At-risk commitments" on the Tasks tab and a dedicated dashboard stat card.
- **Open Questions Tracker**: Detects inquiry turns in transcript, tracks status (`answered`, `partially answered`, `unanswered`), grounds answering quotes with timestamps, and resolves carried-over questions across meetings via embedding similarity.

### 2. Speaker Coaching Scorecards (Prompt B)
- **Deterministic Speaking Metrics**: Talk-time share, words per minute (WPM), turn count, average/longest turn, short-gap interruptions made/received, questions asked, filler-word rate (`um`, `uh`, `like`, `you know`), and hedging rate.
- **Five 0-100 Sub-Scores**:
  - *Clarity*: Inverse of filler & hedge rate.
  - *Participation*: Balance relative to ideal even distribution.
  - *Listening*: Minimal short-gap cut-ins.
  - *Inquiry*: Frequency of probing questions.
  - *Concision*: Brevity and turn length discipline.
- **AI Constructive Coaching**: Generates 2 strengths, 2 improvements, and 1 concrete tip grounded in verbatim quotes.
- **Privacy Toggle**: 1-click toggle to blur/hide individual scores and display team-aggregate metrics.

### 3. AI Devil's Advocate Decision Risk Review (Prompt C)
- **Decision Stress-Testing**: Rigorously analyzes decisions for hidden assumptions, operational risks, missing stakeholders (restricted to meeting history), and alternative unchosen paths.
- **Anti-Hallucination Grounding**: Every claim is verified with `quote_exists()`; ungrounded claims are automatically flagged with an `[AI Inferred]` tag.
- **Discussion Points Export**: 1-click "Copy as discussion points" button for leadership alignment.

### 4. Decision Lineage & Recurring Issues Radar (Prompt D)
- **Cross-Meeting Decision Lineage**: Traces why a decision was made by clustering prior transcript segments across meetings (`proposed` → `debated` → `objection` → `finalized`) with an interactive vertical timeline.
- **Recurring Issues Radar**: Greedy embedding clustering identifying risks, blockers, and questions recurring across 2+ meetings with age and resolution tracking.

### 5. Interactive Meeting Knowledge Graph (Prompt E)
- **Vanilla JS Force-Directed Physics Graph**: Visualizes high-density connections between People, Meetings, Topics, Decisions, and Tasks.
- **Interactive Features**: Drag nodes, pan/zoom, node type filter checkboxes, person neighborhood focus, and click-to-inspect side panel.

### 6. Meeting Cost, Value Score & Agenda Adherence (Prompt F)
- **Meeting Cost Calculator**: Configurable hourly rates (default INR or USD) computing total meeting cost = `Duration × Attendees × Rate`.
- **"Could this have been an email?" Score**: 0-100 Meeting Value Score measuring decisions/10min, task clarity, interactive back-and-forth vs one-way status monologues, producing 3 verdicts: *Worth a meeting*, *Could be shortened*, or *Could have been an email*.
- **Agenda Adherence Checklist**: Paste an agenda on upload; automatically matches items against transcript segments using embeddings and displays % coverage and minutes spent per agenda item.

### 7. Microsoft Teams Webhook & Multi-Meeting Tools (Prompt G)
- **Microsoft Teams Integration**: Dispatches formatted Adaptive Cards with TL;DR, decisions, and owner action items with deadlines via standard library `urllib` (secrets masked in UI and DB).
- **Weekly Leadership Digest**: Map-reduce rollup across meetings in a customizable date window with highlights, decisions, and at-risk commitments.
- **Compare Meetings**: Side-by-side comparison revealing what was added, changed, or dropped between any two meetings.
- **Related Meetings**: Top 3 similar meetings ranked by dense vector cosine similarity.

### 8. Live Meeting Mode (Prompt I)
- **Real-Time Browser Recording**: Audio recording using standard `getUserMedia` and `MediaRecorder` with self-contained 15-second record-stop-restart chunks.
- **RMS Audio Gating**: Live Web Audio API level meter that skips silent chunks to conserve quota.
- **Rolling Live Captions & Incremental Summary**: Polling updates every 2 seconds; rolling summaries update every minute with small token prompts.
- **"Catch Me Up"**: Instant 5-line executive debrief for late meeting joiners.
- **Stop-to-Pipeline Transition**: Seamlessly concatenates chunks and triggers the complete multi-agent intelligence pipeline.
- **Simulated Live Session**: Instant offline demo replay with realistic timer for 100% foolproof live stage demonstrations without needing an active microphone.

---

## ⏱️ 3-Minute Judge Demo Script

Follow this step-by-step walkthrough during competition judging or presentations:

### 1. (00:00 – 00:30) Dashboard Attention Panel & Recurring Issues
1. Start at **Dashboard (`/`)**. Point to the high-contrast Nebula dark UI and top stat cards:
   - Point out **Soft/Vague Commitments (2)**, **Open Questions (3)**, **High-Risk Decisions (1)**, and **Time Cost (₹12,400)**.
2. Scroll to the **Attention Needed** panel:
   - Show cross-meeting contradiction between *Client Kickoff* and *Sprint Review*. Click the timestamp link to jump directly to the quote.
3. Open **Recurring Issues** from the sidebar (`/radar`):
   - Highlight the "Database Connection Pooling" issue seen across 2 meetings for 14 days, linking to exact meeting quotes.

### 2. (00:30 – 01:10) Meeting Detail: Devil's Advocate & Decision Lineage
1. Open **Meeting Detail** for *Sprint Review & Architecture Planning* (`/meeting/demo-1`).
2. Navigate to the **Decisions** tab:
   - On the "Adopt Redis for Caching" card, click **"Challenge this decision" (AI Devil's Advocate)**.
   - Show the slide-out panel with grounded operational risks, hidden assumptions, missing stakeholders, and the `AI-generated challenge, not a fact` disclaimer. Click **"Copy as discussion points"**.
3. On the same decision, click **"Lineage"**:
   - Walk the judges through the vertical timeline showing how the decision originated in Meeting 1, received an objection in Meeting 2, and finalized in Meeting 3.

### 3. (01:10 – 01:45) Tasks with Commitment Strength & Speaker Coaching
1. Click the **Tasks** tab:
   - Point to the **Commitment Strength Chips**: Green (`firm`), Amber (`soft`), Red (`vague`).
   - Hover over an amber chip to display the hedge words found (`"maybe"`, `"probably"`).
   - Toggle the **"At-risk commitments"** filter.
2. Click the **Analytics / Coaching** tab:
   - Review the **Speaker Coaching Scorecard** for Sarah Jenkins.
   - Show the 5 sub-scores (Clarity, Participation, Listening, Inquiry, Concision), WPM, and constructive AI tip grounded in transcript quotes.
   - Toggle **"Hide individual scores"** to showcase executive team privacy mode.

### 4. (01:45 – 02:15) Meeting Knowledge Graph & Business Value
1. Navigate to **Knowledge Graph** in the sidebar (`/graph`):
   - Show the interactive force-directed graph connecting People, Meetings, Topics, Decisions, and Tasks.
   - Drag a node to demonstrate the physics engine; click on Sarah Jenkins to view her open tasks and decisions in the side panel.
2. Back on Meeting 1's **Overview** tab:
   - Show the **"Could this have been an email?" Score (82/100 - "Worth a meeting")** with breakdown of back-and-forth interactivity vs status updates.
   - Point to the **Agenda Adherence Checklist** with coverage % and time spent per item.

### 5. (02:15 – 02:40) Microsoft Teams Webhook & Weekly Digest
1. Open **Settings** (`/settings`):
   - Show the masked Teams Webhook URL. Click **"Test Webhook"** to demonstrate instant Adaptive Card dispatch.
2. Navigate to **Weekly Digest** (`/digest`):
   - Show the map-reduce cross-meeting rollup with 1-click **"Copy Digest"**.

### 6. (02:40 – 03:00) Live Meeting Mode & Offline Demo Replay
1. Navigate to **Live Meeting** (`/live`):
   - Show the clean live view with live RMS audio meter.
   - Click **"Simulate Live Session (Demo)"**:
     - Watch rolling captions stream in real-time.
     - Observe the live incremental running summary and tentative action items appearing.
     - Click **"Catch Me Up"** to demonstrate the 5-line instant executive catch-up.
   - Click **"Stop & Process Meeting"** to show the handoff to the full analytical pipeline.

---

## 🧪 Testing & Verification

Run the full automated test suite:
```bash
# 1. Run all unit and integration tests (31+ tests)
pytest -q

# 2. Run the end-to-end endpoint & page smoke test
python scripts/smoke_test.py

# 3. Run model & pipeline anti-hallucination benchmark evaluation
python scripts/evaluate.py

# 4. Run the live audio chunking & streaming simulation
python scripts/live_simulation.py
```

