![PulseSignal Cover](cover_image.png)

# PulseSignal: Executive GTM Strategy Engine

**Built for the Web Data UNLOCKED Hackathon (May 2026)**

PulseSignal is an autonomous Multi-Agent Market Intelligence platform designed for Go-To-Market (GTM) and Sales teams. It intercepts live web hiring data, enriches account metadata, and synthesizes executive-level strategies to identify immediate buying signals.

---

## 1. Executive Summary: The Problem & Solution

**The Problem:** Sales and Go-To-Market teams waste hours manually scouring company career pages and news sites to find buying signals. Unstructured web data is too noisy to act on efficiently, and lagging indicators, like quarterly earnings, mean missing the optimal window for outreach.

**The Solution:** PulseSignal treats unstructured web data as leading indicators of corporate strategy. We define a "Signal" as a specific data point, such as a targeted job posting, that reveals where a company is investing its capital before the information becomes public knowledge. If a target company suddenly opens 15 requisitions for CUDA optimization, PulseSignal autonomously detects the signal, structures the data, estimates the pipeline value, and drafts a personalized outreach email to the VP of Engineering.

---

## 2. System Architecture & Data Pipeline

Our pipeline consists of three core stages, transforming raw web data into actionable business intelligence:

### Stage 1: Data Ingestion & Live Scraper (`scraper.py`)
*   **Technology:** Python, Requests, Bright Data SERP API.
*   **Process:** We execute targeted, live Google Search queries across a segmented list of 12 critical AI companies.
*   **Storage:** Raw HTML and text snippets are ingested into a local SQLite database (`pulsesignal.db`) within the `raw_cache` table.

### Stage 2: AI Structuring & Extraction (`extract_signals.py`)
*   **Technology:** Google Gemini Flash (`gemini-flash-latest`), SQLite.
*   **Process:** Gemini acts as our high-speed data parser. It reads the noisy, unstructured `raw_cache` data and strictly formats it into a defined JSON schema extracting specific elements: Skills, Seniority, Team Signal, and Business Priority.
*   **Data Integrity:** The pipeline utilizes a master metadata registry to ensure consistent "Company Size" and "Growth Stage" segmentation for 2026 accuracy. The clean, structured data is saved to the `structured_signals` table.

### Stage 3: The Agentic UI & Dashboard (`app.py`)
*   **Technology:** Streamlit, Pandas, Plotly.
*   **UI:** Custom CSS injection provides a premium, dark-themed "SaaS Illusion" interface.
*   **Features:** ICP Filtering, Account Prioritization Bubble Charts, Pipeline Velocity metrics, and a dynamic "Manager's Weekly Report" for strategic resource allocation.

---

## 3. Hybrid Multi-Model AI Engine

To maximize both speed and reasoning capabilities, PulseSignal implements a **Hybrid Multi-Model Architecture**, strategically routing tasks to the best-suited AI model:

1.  **Embeddings & Retrieval (Google):** We utilize `models/gemini-embedding-2` via LangChain for the lightning-fast vectorization of our structured data chunks into a local FAISS vector store.
2.  **Executive Reasoning (AI/ML API - DeepSeek V4 Flash):** We route complex, executive-level reasoning tasks through the **AI/ML API** using `deepseek/deepseek-v4-flash`. DeepSeek serves as the core reasoning engine, powering our Persona Playbooks (calculating estimated pipeline value), drafting highly personalized cold outreach emails, and driving the autonomous ReAct chatbot.

---

## 4. The Autonomous ReAct Agent (Chatbot)

PulseSignal features a robust, natural language interface powered by a LangChain `AgentExecutor` utilizing a `ReAct` (Reasoning and Acting) framework.

*   **Tools Provided:**
    1.  `Market_Database`: Grants the agent access to the FAISS vector store to answer specific questions about hiring signals and internal database contents.
    2.  `Live_Web_Search`: A custom tool utilizing Bright Data to search Google live for real-time information that does not exist in the local database.
*   **Functionality:** The DeepSeek agent autonomously analyzes the user's prompt, decides whether to query the local database or execute a live web search, and synthesizes a final, grounded answer.

---

## 5. Core Business Features

*   **Evidence Ledger:** Transparent, deterministic tracking that allows users to view the raw scraped data backing up the AI's strategic claims.
*   **CRM Export:** A one-click CSV export functionality to seamlessly move targeted account data into existing CRM workflows.
*   **Real-World Action (Gmail Integration):** The "Initiate Outreach" capability takes the DeepSeek-drafted email and directly opens the user's local web email client (Gmail) with the subject, recipient, and body perfectly pre-populated.

---

## 6. Setup & Execution Instructions

### Prerequisites
1.  Python 3.10+
2.  Install dependencies: `pip install -r requirements.txt`
3.  Create a `.env` file in the root directory with your API keys:
    ```
    BRIGHTDATA_API_KEY="your_brightdata_key"
    BRIGHTDATA_ZONE="your_brightdata_zone"
    GOOGLE_API_KEY="your_google_key"
    AIML_API_KEY="your_aiml_key"
    ```

### Execution Flow
1.  **Fetch Live Data:** Run `python3 scraper.py` to pull fresh market signals via Bright Data.
2.  **Extract & Structure:** Run `python3 extract_signals.py` to structure the data using Gemini.
3.  **Launch Dashboard:** Run `streamlit run app.py` to launch the Executive GTM Engine locally.
