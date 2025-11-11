"""Standalone CSV Viewer for College Data."""

import streamlit as st
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from utils.csv_loader import (
    load_csv_file,
    load_csv_from_upload,
    convert_csv_to_college_data,
    display_csv_summary,
    enrich_csv_data_from_db,
    export_to_csv
)
from utils.college_data_display import display_college_data_preview
from database.connection import DatabaseConnection

# Page configuration
st.set_page_config(
    page_title="College CSV Viewer",
    page_icon="📊",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'csv_data' not in st.session_state:
    st.session_state.csv_data = None
if 'college_data' not in st.session_state:
    st.session_state.college_data = None
if 'enriched_data' not in st.session_state:
    st.session_state.enriched_data = None

# Header
st.markdown('<div class="main-header">📊 College CSV Viewer</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Load and visualize college data from CSV files</div>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("## 📁 Data Source")

    data_source = st.radio(
        "Choose data source:",
        ["Upload CSV File", "Load from Path", "Use Sample Data"]
    )

    if data_source == "Upload CSV File":
        uploaded_file = st.file_uploader(
            "Upload CSV file",
            type=['csv'],
            help="Upload a CSV file with college data"
        )

        if uploaded_file:
            if st.button("Load CSV", type="primary"):
                with st.spinner("Loading CSV file..."):
                    df = load_csv_from_upload(uploaded_file)
                    if df is not None:
                        st.session_state.csv_data = df
                        st.session_state.college_data = convert_csv_to_college_data(df)
                        st.success(f"✅ Loaded {len(df)} college(s) from CSV")

    elif data_source == "Load from Path":
        file_path = st.text_input(
            "Enter CSV file path:",
            value="/Users/rishabhbansal/Downloads/2025-11-11T06-49_export.csv",
            help="Full path to the CSV file"
        )

        if st.button("Load CSV", type="primary"):
            if Path(file_path).exists():
                with st.spinner("Loading CSV file..."):
                    df = load_csv_file(file_path)
                    if df is not None:
                        st.session_state.csv_data = df
                        st.session_state.college_data = convert_csv_to_college_data(df)
                        st.success(f"✅ Loaded {len(df)} college(s) from CSV")
            else:
                st.error(f"❌ File not found: {file_path}")

    elif data_source == "Use Sample Data":
        if st.button("Load Sample Data", type="primary"):
            # Sample data (IIT Bombay)
            import pandas as pd
            sample_df = pd.DataFrame([{
                'ID': 3,
                'Name': 'Indian Institute of Technology Bombay',
                'City': 'Mumbai',
                'State': 'Maharashtra',
                'Active': '✅',
                'Verified': '❌',
                'Accreditations': 4,
                'Facilities': 47,
                'Website': 'https://www.iitb.ac.in'
            }])
            st.session_state.csv_data = sample_df
            st.session_state.college_data = convert_csv_to_college_data(sample_df)
            st.success("✅ Loaded sample data (IIT Bombay)")

    # Database enrichment option
    if st.session_state.college_data:
        st.markdown("---")
        st.markdown("### 🔄 Data Enrichment")

        if st.checkbox("Enable Database Enrichment", help="Fetch detailed data from database if available"):
            if st.button("Enrich from Database"):
                try:
                    db = DatabaseConnection()
                    if db.test_connection():
                        with st.spinner("Enriching data from database..."):
                            st.session_state.enriched_data = enrich_csv_data_from_db(
                                st.session_state.college_data,
                                db
                            )
                        st.success("✅ Data enrichment complete!")
                    else:
                        st.error("❌ Database connection failed")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

    # Export option
    if st.session_state.college_data or st.session_state.enriched_data:
        st.markdown("---")
        st.markdown("### 💾 Export Data")

        data_to_export = st.session_state.enriched_data if st.session_state.enriched_data else st.session_state.college_data

        csv_export = export_to_csv(data_to_export)
        st.download_button(
            label="⬇️ Download CSV",
            data=csv_export,
            file_name="colleges_export.csv",
            mime="text/csv"
        )

# Main content
if st.session_state.csv_data is not None:
    # Show CSV summary
    display_csv_summary(st.session_state.csv_data)

    st.markdown("---")

    # Determine which data to display
    display_data = st.session_state.enriched_data if st.session_state.enriched_data else st.session_state.college_data

    if display_data:
        # Show detailed visualization
        display_college_data_preview(display_data, max_display=10, use_expander=True)
    else:
        st.warning("⚠️ No college data to display")

else:
    # Welcome message
    st.info("""
    ### 👋 Welcome to College CSV Viewer!

    This tool helps you visualize college data from CSV files.

    **Features:**
    - 📁 Load CSV files from upload or file path
    - 📊 View summary statistics
    - 🎓 Detailed college cards with tabs for different sections
    - 🔄 Enrich CSV data with database information (if available)
    - 💾 Export processed data to CSV

    **Get Started:**
    1. Use the sidebar to select a data source
    2. Upload or specify a CSV file
    3. Click "Load CSV" to view the data

    **CSV Format:**
    The CSV should contain columns: ID, Name, City, State, Active, Verified, Accreditations, Facilities, Website
    """)

    st.markdown("---")

    # Quick load button for the specific file
    st.markdown("### 🚀 Quick Load")
    if st.button("Load IIT Bombay Data", type="primary"):
        file_path = "/Users/rishabhbansal/Downloads/2025-11-11T06-49_export.csv"
        if Path(file_path).exists():
            with st.spinner("Loading CSV file..."):
                df = load_csv_file(file_path)
                if df is not None:
                    st.session_state.csv_data = df
                    st.session_state.college_data = convert_csv_to_college_data(df)
                    st.rerun()
        else:
            st.error(f"❌ File not found: {file_path}")
