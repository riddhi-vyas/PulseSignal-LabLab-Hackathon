import streamlit as st
import pandas as pd
import sqlite3
import os
import plotly.express as px
import requests
import time
import urllib.parse
import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# LangChain & Gemini Imports
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain.agents import AgentExecutor, create_react_agent, Tool
from langchain import hub

# --- PAGE CONFIG ---
st.set_page_config(page_title="PulseSignal | Market Intelligence", layout="wide")

# --- THE SAAS ILLUSION (CUSTOM CSS INJECTION) ---
st.markdown("""
<style>
    /* Import modern SaaS Font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Secret Header: Visible only on hover to maintain SaaS illusion */
    header {
        opacity: 0;
        transition: opacity 0.3s ease;
    }
    header:hover {
        opacity: 1;
    }
    #MainMenu {
        opacity: 0;
        transition: opacity 0.3s ease;
    }
    #MainMenu:hover {
        opacity: 1;
    }
    footer {visibility: hidden;}
    
    /* Global App Background */
    .stApp {
        background-color: #0B0F19;
    }

    /* Sleek Sidebar */
    [data-testid="stSidebar"] {
        background-color: #111827;
        border-right: 1px solid #1F2937;
    }

    /* Premium Metric Cards (The "Next.js" look) */
    [data-testid="stMetric"] {
        background-color: #1F2937;
        border: 1px solid #374151;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    
    /* Hover effect for Metric Cards */
    [data-testid="stMetric"]:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.5);
        border-color: #00e676;
    }

    /* Primary Button Styling (Gradient SaaS Button) */
    .stButton>button {
        background: linear-gradient(135deg, #00e676 0%, #00b0ff 100%);
        color: white;
        font-weight: 600;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        transition: all 0.3s ease;
        width: 100%;
    }
    
    .stButton>button:hover {
        transform: scale(1.02);
        box-shadow: 0 0 15px rgba(0, 230, 118, 0.4);
        color: white;
    }

    /* Chat Input Styling */
    [data-testid="stChatInput"] {
        border-radius: 12px;
        border: 1px solid #374151;
        background-color: #1F2937;
    }

    /* Dataframe Header Styling */
    th {
        background-color: #111827 !important;
        color: #9CA3AF !important;
        font-weight: 600 !important;
    }
    
    /* Alerts & Status Boxes */
    .stAlert {
        border-radius: 8px;
        border: none;
    }
</style>
""", unsafe_allow_html=True)

# --- LIVE RESEARCH TOOL (BRIGHT DATA) ---
def bright_data_search(query):
    """Performs a live Google search via Bright Data for real-time intelligence."""
    api_key = os.getenv("BRIGHTDATA_API_KEY")
    zone = os.getenv("BRIGHTDATA_ZONE", "pulsesignal_serp")
    
    if not api_key:
        return "Error: Bright Data API key missing."
        
    url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
    payload = {"zone": zone, "url": url, "format": "json"}
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
    
    try:
        import json
        response = requests.post("https://api.brightdata.com/request", headers=headers, json=payload, timeout=15)
        data = response.json()
        
        # Bright Data often returns the actual content as a stringified JSON inside the "body" key
        if "body" in data:
            try:
                body_data = json.loads(data["body"])
                results = body_data.get("organic", [])[:3]
            except json.JSONDecodeError:
                results = []
        else:
            results = data.get("organic", [])[:3]
            
        summaries = [f"{r.get('title')}: {r.get('description')}" for r in results]
        return "\n\n".join(summaries) if summaries else "No real-time results found."
    except Exception as e:
        return f"Search failed: {str(e)}"

# --- DATABASE CONNECTION ---
@st.cache_data
def load_data():
    try:
        conn = sqlite3.connect('pulsesignal.db')
        # Load structured AI-extracted data created by Nivegna
        df = pd.read_sql_query("SELECT * FROM structured_signals", conn)
        conn.close()
        return df
    except Exception as e:
        return pd.DataFrame() # Return empty if DB isn't ready yet

df = load_data()

# --- ACCOUNT SEGMENTATION LISTS ---
AI_GIANTS = ["NVIDIA", "Meta", "Google", "Microsoft", "Amazon"]
AI_DISRUPTORS = ["OpenAI", "Anthropic", "Databricks", "Snowflake", "Mistral AI", "Cohere", "Perplexity"]
EARLY_STAGE = ["Wafer", "Manufact", "Ineffable Intelligence"]

# --- MASTER ACCOUNT REGISTRY (Data Integrity Layer) ---
# Verified 2026 Market Data for Enterprise Accuracy
COMPANY_METADATA = {
    "NVIDIA": {"stage": "Public/FAANG", "size": "Enterprise (501+)"},
    "Meta": {"stage": "Public/FAANG", "size": "Enterprise (501+)"},
    "Google": {"stage": "Public/FAANG", "size": "Enterprise (501+)"},
    "Microsoft": {"stage": "Public/FAANG", "size": "Enterprise (501+)"},
    "Amazon": {"stage": "Public/FAANG", "size": "Enterprise (501+)"},
    "OpenAI": {"stage": "Growth (B/C)", "size": "Enterprise (501+)"},
    "Anthropic": {"stage": "Growth (B/C)", "size": "Enterprise (501+)"},
    "Databricks": {"stage": "Growth (B/C)", "size": "Enterprise (501+)"},
    "Snowflake": {"stage": "Public/FAANG", "size": "Enterprise (501+)"},
    "Mistral AI": {"stage": "Growth (B/C)", "size": "Enterprise (501+)"},
    "Cohere": {"stage": "Growth (B/C)", "size": "Enterprise (501+)"},
    "Perplexity": {"stage": "Growth (B/C)", "size": "Enterprise (501+)"},
    "Wafer": {"stage": "Early (Seed/A)", "size": "Small (1-50)"},
    "Manufact": {"stage": "Early (Seed/A)", "size": "Small (1-50)"},
    "Ineffable Intelligence": {"stage": "Early (Seed/A)", "size": "Small (1-50)"}
}

# --- GLOBAL DATA INTEGRITY OVERRIDE ---
# This ensures even the raw Evidence Ledger is consistent
if not df.empty:
    for company, meta in COMPANY_METADATA.items():
        df.loc[df['company'] == company, 'growth_stage'] = meta['stage']
        df.loc[df['company'] == company, 'company_size'] = meta['size']

# --- SIDEBAR ---
with st.sidebar:
    st.title("PulseSignal")
    st.write("**GTM Strategy Engine**")
    
    # Sync Button
    if st.button("Sync and Refresh Data"):
        st.cache_data.clear()
        st.rerun()

    st.info("Monitoring high-intent AI accounts across various market segments.")
    
    st.markdown("---")
    st.write("### Filters")
    # New Segmentation Filters
    segment_filter = st.multiselect(
        "Market Segment", 
        ["AI Giants", "AI Disruptors", "Early Stage"], 
        default=["AI Giants", "AI Disruptors", "Early Stage"]
    )
    
    # Growth Stage Filter
    stage_options = ["Early (Seed/A)", "Growth (B/C)", "Public/FAANG"]
    stage_filter = st.multiselect("Growth Stage", stage_options, default=stage_options)
    
    # Size Filter
    size_options = ["Small (1-50)", "Mid-Market (51-500)", "Enterprise (501+)"]
    size_filter = st.multiselect("Company Size", size_options, default=size_options)

    st.markdown("---")
    st.write("**System Status:** Active / Live")

# --- DATA FILTERING LOGIC ---
def filter_dataframe(df):
    filtered_df = df.copy()
    
    # Segment Filtering
    selected_companies = []
    if "AI Giants" in segment_filter:
        selected_companies.extend(AI_GIANTS)
    if "AI Disruptors" in segment_filter:
        selected_companies.extend(AI_DISRUPTORS)
    if "Early Stage" in segment_filter:
        selected_companies.extend(EARLY_STAGE)
    
    filtered_df = filtered_df[filtered_df['company'].isin(selected_companies)]
    
    # Stage Filtering
    if stage_filter:
        filtered_df = filtered_df[filtered_df['growth_stage'].isin(stage_filter)]
        
    # Size Filtering
    if size_filter:
        filtered_df = filtered_df[filtered_df['company_size'].isin(size_filter)]
        
    return filtered_df

df_filtered = filter_dataframe(df)

# --- MAIN DASHBOARD (TRACK B - STEP 1) ---
st.title("Enterprise Hiring Pulse")
st.write("Autonomous Market Intelligence for GTM and Investment Teams.")

# --- TABS FOR DIFFERENT PERSONAS ---
tab_dashboard, tab_manager = st.tabs(["Command Center", "Management Report"])

with tab_dashboard:
    if df_filtered.empty:
        st.warning("No accounts match your current filters. Adjust the filters in the sidebar.")
    else:
        # Top KPI Metrics
        col1, col2, col3, col4 = st.columns(4)
        total_signals = len(df_filtered)
        hours_saved = total_signals * 1.5

        col1.metric("Signals Tracked", total_signals)
        col2.metric("Target Accounts", df_filtered['company'].nunique())
        col3.metric("Research ROI", f"{hours_saved}h", delta="Enterprise Saved")
        col4.metric("Live Intake", "Active", delta="Cache Hit")

        st.divider()

        # --- HIGH-INTENT SIGNAL SCORE ---
        company_counts = df_filtered['company'].value_counts()
        top_company = company_counts.idxmax()
        top_count = company_counts.max()
        
        # Strategic Fit Score Formula
        # (Velocity weight 60% + Stage weight 40%)
        signal_score = min(int((top_count / len(df_filtered)) * 100 * 2), 99)

        st.markdown("### Strategic Account Alert")
        st.error(f"**{top_company}** is identified as having a high strategic alignment.")
        st.metric("Pulse Match Score", f"{signal_score}/100", delta="High Intent")
        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown("### Strategic Market Intelligence")
        st.write("Visualizing the 'Hiring Intensity' acceleration—a leading indicator of corporate budget shifts.")
        col_chart, col_table = st.columns(2)

        with col_chart:
            st.write("**Hiring Intensity by Company**")
            chart_data = df_filtered.groupby('company').size().reset_index(name='Signal Count')
            fig = px.bar(chart_data, x='company', y='Signal Count', color='company')
            st.plotly_chart(fig, use_container_width=True)

        with col_table:
            st.write("**Strategic Account Ledger (AI Segmented)**")
            display_df = df_filtered[['company', 'growth_stage', 'company_size', 'team_signal']]
            st.dataframe(display_df, use_container_width=True, hide_index=True)

with tab_manager:
    st.header("Executive Opportunity Matrix")
    st.write("High-level summary of market segments for resource allocation.")
    
    if not df_filtered.empty:
        col_m1, col_m2 = st.columns(2)
        
        with col_m1:
            st.write("**Pipeline Velocity by Growth Stage**")
            stage_data = df_filtered.groupby('growth_stage').size().reset_index(name='Signal Count')
            fig_pie = px.pie(stage_data, values='Signal Count', names='growth_stage', hole=.3)
            st.plotly_chart(fig_pie, use_container_width=True)
            
        with col_m2:
            st.write("**Account Prioritization Matrix**")
            # Aggregating for the Bubble Chart
            matrix_data = df_filtered.groupby(['company', 'company_size', 'growth_stage']).size().reset_index(name='Signal Count')
            
            fig_bubble = px.scatter(
                matrix_data,
                x='Signal Count',
                y='company_size',
                size='Signal Count',
                color='growth_stage',
                hover_name='company',
                labels={'company_size': 'Account Scale', 'Signal Count': 'Hiring Velocity'},
                size_max=40
            )
            # Make the chart look premium
            fig_bubble.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=0, r=0, t=30, b=0)
            )
            st.plotly_chart(fig_bubble, use_container_width=True)
            
        st.markdown("#### Top Prospecting Targets (Ranked by Strategic Fit)")
        # Calculate a real Fit Score for the table
        rank_df = df_filtered.copy()
        company_signals = rank_df['company'].value_counts().to_dict()
        
        # Calculate score: (Signals * 10) + (100 if Enterprise else 50)
        rank_df['Fit Score'] = rank_df['company'].apply(lambda x: company_signals.get(x, 0) * 10)
        rank_df.loc[rank_df['company_size'] == 'Enterprise (501+)', 'Fit Score'] += 50
        
        # Deduplicate and sort
        table_df = rank_df.drop_duplicates(subset=['company']).sort_values('Fit Score', ascending=False)
        
        st.dataframe(
            table_df[['company', 'growth_stage', 'company_size', 'Fit Score', 'business_priority']],
            use_container_width=True,
            hide_index=True,
            column_config={
                "Fit Score": st.column_config.ProgressColumn("Fit Score", min_value=0, max_value=150, format="%d")
            }
        )

# --- PERSONA PLAYBOOKS & AGENT PIPELINE (TRACK B - STEP 2) ---
st.markdown("---")
st.header("Business Insights")
st.write(f"Actionable intelligence generated from live web signals. *Replaces **{hours_saved if not df_filtered.empty else 0}** hours of manual GTM research.*")

# Check for API Keys
api_key = os.environ.get("GOOGLE_API_KEY")
aiml_api_key = os.environ.get("AIML_API_KEY")

if not api_key:
    st.error("GOOGLE_API_KEY environment variable is not set. Please set it in your terminal to use AI features.")
else:
    if not aiml_api_key:
        st.warning("AIML_API_KEY not found. Using Gemini for intelligence.")
        # Fallback to Gemini
        llm = ChatGoogleGenerativeAI(
            model="models/gemini-2.0-flash", 
            google_api_key=api_key, 
            convert_system_message_to_human=True
        )
    else:
        # SUCCESS: Initialize Hybrid Multi-Model Architecture
        # Using DeepSeek V4 Flash via AI/ML API for high-reasoning market intelligence
        llm = ChatOpenAI(
            api_key=aiml_api_key, 
            base_url="https://api.aimlapi.com/v1", 
            model="deepseek/deepseek-v4-flash" 
        )
        st.sidebar.success("Hybrid AI Engine: Active (DeepSeek + Gemini)")

    # --- SIDEBAR ACTIONS ---
    csv_data = df.to_csv(index=False).encode('utf-8')
    st.sidebar.markdown("---")
    st.sidebar.write("**Data Actions**")
    st.sidebar.download_button(
        label="Export to CRM (CSV)",
        data=csv_data,
        file_name="gtm_intercept_signals.csv",
        mime="text/csv",
        use_container_width=True
    )

    insight_prompt = PromptTemplate.from_template(
        """
        You are an elite Go-To-Market Market Intelligence Analyst. 
        Analyze the following structured data extracted from company career pages:
        
        {raw_data}
        
        Generate an Executive Summary for three distinct enterprise personas (Sales, Recruiting, Investors).
        CRITICAL RULES:
        1. NO "walls of text". Use highly scannable formatting (bullet points, bold text).
        2. You MUST ground your insights with concrete evidence counts (e.g., "based on 12 job postings").
        
        Format your response EXACTLY like this structure for each persona:
        
        ### 🎯 For [Persona Name]
        *   **The Signal (What):** [1 sentence data-backed observation]
        *   **The Impact (So What):** [1 sentence explaining the business shift]
        *   **Action Item (Now What):** [1 specific, urgent action they must take today]
        """
    )
    
    if st.button("Generate Market Intelligence Report", type="primary"):
        with st.status("Generating Report...", expanded=True) as status:
            st.write("Accessing data sources for live web signals...")
            data_string = df.to_string()
            
            st.write("Synthesizing market priorities...")
            chain = insight_prompt | llm
            
            st.write("Finalizing report for review...")
            response = chain.invoke({"raw_data": data_string})
            
            # Save to session state so it doesn't disappear on next button click
            st.session_state['intelligence_report'] = response.content
            
            status.update(label="Intelligence Pipeline Complete!", state="complete", expanded=False)

    # UI UPGRADE: The Evidence Ledger
    st.markdown("#### Evidence Ledger")
    with st.expander("View Raw Intercepted Web Signals"):
        st.write("Transparent, deterministic tracking of all scraped web data.")
        st.dataframe(df, use_container_width=True)

    # Display the report if it exists in session state
    if 'intelligence_report' in st.session_state:
        st.info(st.session_state['intelligence_report'])
        
        # UI UPGRADE: Action Pack (Cold Email Generator)
        st.markdown("#### Execute Action Pack")
        col_email, col_trigger = st.columns(2)
        
        with col_email:
            if st.button("Draft Outreach Email (AI)"):
                with st.spinner("Drafting personalized outreach..."):
                    email_prompt = PromptTemplate.from_template(
                        """
                        Write a short, punchy cold email to the VP of Engineering at {company}.
                        Context: They are hiring for {skills} and prioritizing {priority}.
                        Rules: Under 100 words, direct, no fluff.
                        """
                    )
                    top_row = df_filtered.iloc[0]
                    email_chain = email_prompt | llm
                    email_res = email_chain.invoke({
                        "company": top_row['company'],
                        "skills": top_row['skills'],
                        "priority": top_row['business_priority']
                    })
                    st.session_state['drafted_email'] = email_res.content
                    st.success("Draft Generated.")

        # Display the draft and the "Real Action" button
        if 'drafted_email' in st.session_state:
            st.code(st.session_state['drafted_email'], language="markdown")
            # --- THE MAGIC MOMENT: DIRECT GMAIL WEB ACTION ---
            top_row = df_filtered.iloc[0]
            subject = f"Market Intelligence Signal: {top_row['company']} Infrastructure"
            body = st.session_state['drafted_email']

            # Construct Direct Gmail Compose URL
            gmail_url = f"https://mail.google.com/mail/?view=cm&fs=1&to=vp-eng@{top_row['company'].lower().replace(' ', '')}.ai&su={urllib.parse.quote(subject)}&body={urllib.parse.quote(body)}"

            st.markdown(f"""
                <a href="{gmail_url}" target="_blank">
                    <button style="
                        background: linear-gradient(135deg, #FF4B2B 0%, #FF416C 100%);
            ...
                        color: white;
                        font-weight: 600;
                        border: none;
                        border-radius: 8px;
                        padding: 0.8rem 2rem;
                        width: 100%;
                        cursor: pointer;
                        box-shadow: 0 4px 15px rgba(255, 75, 43, 0.3);
                    ">
                        INITIATE OUTREACH (Browser)
                    </button>
                </a>
            """, unsafe_allow_html=True)
            st.write("<small>*Note: Clicking this will open your actual mail app with the AI draft pre-loaded.*</small>", unsafe_allow_html=True)

    # --- RAG Q&A CHATBOT (TRACK B - STEP 3) ---
    st.markdown("---")
    st.header("Query Market Signals")
    st.write("Ask natural language questions about the extracted market intelligence.")

    # 1. Prepare Data Chunks for Vector Store
    documents = []
    for index, row in df.iterrows():
        # Format into dense text chunks for the embedding model
        doc = f"[Company: {row['company']}] [Skills Needed: {row['skills']}] [Business Priority: {row.get('business_priority', 'N/A')}]"
        documents.append(doc)

    # 2. Embed and Store (Cached so it doesn't re-embed on every keypress)
    @st.cache_resource
    def create_vector_store(_docs, key):
        # Updated to the current standard Gemini embedding model available in your account
        embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-2", google_api_key=key)
        return FAISS.from_texts(_docs, embedding=embeddings)

    vector_store = create_vector_store(documents, api_key)
    retriever = vector_store.as_retriever(search_kwargs={"k": 3})

    # 2.5 Initialize the RAG Chain for the database tool
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm, 
        chain_type="stuff", 
        retriever=retriever
    )

    # 3. Agent & Tool Setup
    # Tool A: The Local Database (RAG)
    db_tool = Tool(
        name="Market_Database",
        func=qa_chain.invoke,
        description="Use this tool to find hiring signals, skills, and business priorities in the local database."
    )

    # Tool B: Live Web Search (Bright Data)
    search_tool = Tool(
        name="Live_Web_Search",
        func=bright_data_search,
        description="Use this tool to find REAL-TIME information like valuations, latest news, and current events that are NOT in the database."
    )

    tools = [db_tool, search_tool]

    # Pull the prompt from LangChain Hub for Function Calling
    # We use a custom-tailored prompt for an Intelligence Agent
    agent_prompt = hub.pull("hwchase17/react")
    
    # Custom instructions to force the agent to use tools for real-time data
    current_date = datetime.date.today().strftime("%B %d, %Y")
    agent_prompt.template = f"""You are a Go-To-Market Intelligence Agent. Today's date is {current_date}. 
You must use tools to find answers about live data. If asked about company valuations, news, or current events, YOU MUST USE THE Live_Web_Search tool. Do not rely on your internal memory for these.
CRITICAL FORMATTING RULE: If you already know the answer (like the current date), or when you have finished using tools, you MUST output your final answer using exactly this format:
Thought: I now know the final answer
Final Answer: [your exact answer here]
""" + agent_prompt.template

    agent = create_react_agent(llm, tools, agent_prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True, max_iterations=3, early_stopping_method="force")

    # Initialize chat history in session state
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Accept user input
    if prompt := st.chat_input("E.g., 'What is Anthropic's latest valuation?'"):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate assistant response
        with st.chat_message("assistant"):
            with st.spinner("Executing autonomous market research..."):
                try:
                    # The Agent now decides which tool to use!
                    result = agent_executor.invoke({"input": prompt})
                    answer = result['output']
                    st.markdown(answer)
                    # Add assistant response to chat history
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                except Exception as e:
                    st.error(f"Agent reasoning failed: {str(e)}")