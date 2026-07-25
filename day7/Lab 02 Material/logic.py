import streamlit as st
import os
import sqlite3
from datetime import datetime
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Load local environment variables if testing locally
load_dotenv()

# --- CONFIGURATION & SECURITY GATEKEEPER ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = "gemini-2.5-flash"
DB_NAME = "review_history.db"

if not GEMINI_API_KEY:
    st.error("❌ Configuration Error: GEMINI_API_KEY is missing!")
    st.info("Please add your key to a `.env` file locally or inside Streamlit's Secrets panel on the cloud.")
    st.stop()

# Initialize the official Gemini Client
client = genai.Client(api_key=GEMINI_API_KEY)

# --- DATABASE OPERATIONS ---

def init_db():
    """Initializes the SQLite database and creates the table if it doesn't exist."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS summaries 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  filename TEXT, 
                  summary TEXT, 
                  rating INTEGER, 
                  category TEXT, 
                  created_at DATETIME)''')
    conn.commit()
    conn.close()

def save_summary(filename, summary, rating, category):
    """Saves a new analysis record to the database."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""INSERT INTO summaries (filename, summary, rating, category, created_at) 
                 VALUES (?, ?, ?, ?, ?)""", 
              (filename, summary, rating, category, datetime.now()))
    conn.commit()
    conn.close()

def get_summaries_by_category(category):
    """Retrieves all past summaries belonging to a specific category."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, filename, created_at FROM summaries WHERE category = ? ORDER BY created_at DESC", (category,))
    data = c.fetchall()
    conn.close()
    return data

def get_summary_by_id(summary_id):
    """Retrieves a single complete analysis record using its unique ID."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT filename, summary, rating, category, created_at FROM summaries WHERE id = ?", (summary_id,))
    data = c.fetchone()
    conn.close()
    return data

# Initialize Database immediately
init_db()

# --- STREAMLIT PAGE LAYOUT ---
st.set_page_config(page_title="Review Analyst Pro", page_icon="📈", layout="wide")

# Initialize Session States to control UI navigation mapping
if "view_mode" not in st.session_state:
    st.session_state.view_mode = "new_analysis"
if "selected_summary_id" not in st.session_state:
    st.session_state.selected_summary_id = None

# --- SIDEBAR COMPONENT ---
with st.sidebar:
    st.title("📁 Navigation & History")
    
    # Primary action to reset UI to standard uploader
    if st.button("➕ Analyze New Reviews", use_container_width=True, type="primary"):
        st.session_state.view_mode = "new_analysis"
        st.session_state.selected_summary_id = None
        st.rerun()
        
    st.divider()
    st.subheader("📜 Filter Past Summaries")
    
    # Category expander folders
    categories = {
        "🟢 Good (8-10)": "Good",
        "🟡 Average (4-7)": "Average",
        "🔴 Bad (0-3)": "Bad"
    }
    
    for label, db_category in categories.items():
        with st.expander(label):
            records = get_summaries_by_category(db_category)
            if not records:
                st.caption("No historical records found.")
            for rec_id, filename, timestamp in records:
                # Format time string for cleaner UI listings
                time_str = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S.%f").strftime("%b %d, %H:%M")
                btn_label = f"📄 {filename} ({time_str})"
                
                # If a user clicks a historical record button, switch the view state
                if st.button(btn_label, key=f"rec_{rec_id}", use_container_width=True):
                    st.session_state.view_mode = "view_past"
                    st.session_state.selected_summary_id = rec_id
                    st.rerun()

# --- MAIN CONTROLLER ARENA ---

# MODE 1: View Past Record History
if st.session_state.view_mode == "view_past" and st.session_state.selected_summary_id is not None:
    record = get_summary_by_id(st.session_state.selected_summary_id)
    if record:
        filename, summary, rating, category, created_at = record
        
        st.title(f"📜 Archived Summary: {filename}")
        st.caption(f"Analyzed on: {created_at} | Category Tier: **{category}**")
        st.markdown("---")
        
        # Display the visual metric card
        col1, col2 = st.columns([1, 4])
        with col1:
            st.metric(label="Overall Rating", value=f"{rating} / 10")
        with col2:
            if category == "Good":
                st.success("🎯 Category Score: This batch reflects overall positive customer sentiment.")
            elif category == "Average":
                st.warning("⚖️ Category Score: This batch reflects mixed or average customer sentiment.")
            else:
                st.error("⚠️ Category Score: This batch reflects critical or negative customer sentiment.")
                
        st.markdown("### 📋 Core Synthesis Summary")
        st.markdown(summary)
    else:
        st.error("Could not retrieve the specified historical record.")

# MODE 2: Run Fresh Analysis Uploader
else:
    st.title("📊 Customer Review Analytics Engine")
    st.caption(f"Cloud Architecture Backend: **{MODEL_NAME}**")
    st.markdown("---")
    
    st.markdown("""
    ### 📥 Processing Pipeline
    Upload a text file containing compilation feedback. The platform will evaluate metrics, 
    generate structured takeaways, and catalog the entry into the database repository automatically.
    """)
    
    uploaded_file = st.file_uploader("Drop customer feedback .txt file here", type=["txt"])
    
    if uploaded_file is not None:
        try:
            review_text = uploaded_file.read().decode("utf-8")
            
            with st.expander("📄 Review File Context Preview", expanded=False):
                st.text(review_text)
                
            st.markdown("---")
            
            if st.button("🚀 Execute Sentiment Analysis", use_container_width=True):
                with st.spinner("Gemini is interpreting text blocks and mapping score parameters..."):
                    try:
                        # Define structural prompt system rules
                        system_prompt = (
                            "You are a database-integrated text processing utility. Analyze the user text data. "
                            "You MUST output your response in a strict formatted style containing two sections:\n"
                            "1. A bulleted summary synthesized from the reviews.\n"
                            "2. A standalone single line stating exactly: 'FINAL_RATING: X' (where X is an integer score from 0 to 10).\n\n"
                            "Keep your response analytical and professional."
                        )
                        
                        response = client.models.generate_content(
                            model=MODEL_NAME,
                            contents=review_text,
                            config=types.GenerateContentConfig(
                                system_instruction=system_prompt,
                                temperature=0.1
                            )
                        )
                        
                        raw_output = response.text
                        
                        # PARSING LOGIC: Extract score metrics from structural wrapper tags
                        rating = 5  # Safe default fallback score if parsing fails
                        clean_summary = raw_output
                        
                        if "FINAL_RATING:" in raw_output:
                            parts = raw_output.split("FINAL_RATING:")
                            clean_summary = parts[0].strip()
                            try:
                                # Clean extract trailing numerical characters
                                rating = int("".join(filter(str.isdigit, parts[1])))
                            except ValueError:
                                rating = 5
                        
                        # Determine Category routing bracket
                        if 8 <= rating <= 10:
                            category = "Good"
                        elif 4 <= rating <= 7:
                            category = "Average"
                        else:
                            category = "Bad"
                            
                        # COMMIT INSIGHTS TO PERMANENT DISK STORAGE
                        save_summary(uploaded_file.name, clean_summary, rating, category)
                        
                        st.success(f"✅ Processing Finalized! Saved under **{category}** classification category.")
                        
                        # Live presentation rendering
                        m_col, d_col = st.columns([1, 4])
                        m_col.metric(label="Calculated Score", value=f"{rating} / 10")
                        d_col.info(f"Database Router Pipeline assigned this to the **{category}** segment container.")
                        
                        st.markdown("### 📋 AI Generated Synthesis Review")
                        st.markdown(clean_summary)
                        
                    except Exception as api_err:
                        st.error(f"❌ Cloud API Request Interrupted: {api_err}")
                        
        except Exception as file_err:
            st.error(f"❌ Structural Read Error: {file_err}")