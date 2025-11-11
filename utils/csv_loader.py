"""Utility functions for loading college data from CSV files."""

import pandas as pd
import streamlit as st
from typing import Dict, List, Any, Optional
import json


def load_csv_file(file_path: str) -> Optional[pd.DataFrame]:
    """
    Load a CSV file and return as DataFrame.

    Args:
        file_path: Path to the CSV file

    Returns:
        DataFrame or None if error
    """
    try:
        df = pd.read_csv(file_path)
        return df
    except Exception as e:
        st.error(f"Error loading CSV: {str(e)}")
        return None


def load_csv_from_upload(uploaded_file) -> Optional[pd.DataFrame]:
    """
    Load a CSV file from Streamlit file uploader.

    Args:
        uploaded_file: Streamlit UploadedFile object

    Returns:
        DataFrame or None if error
    """
    try:
        df = pd.read_csv(uploaded_file)
        return df
    except Exception as e:
        st.error(f"Error loading CSV: {str(e)}")
        return None


def convert_csv_to_college_data(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Convert CSV DataFrame to the college data format expected by display functions.

    Args:
        df: DataFrame with college data

    Returns:
        List of college data dictionaries
    """
    colleges = []

    for idx, row in df.iterrows():
        college = {
            'college_id': row.get('ID', idx),
            'name': row.get('Name', 'N/A'),
            'city': row.get('City', 'N/A'),
            'state': row.get('State', 'N/A'),
            'district': row.get('City', 'N/A'),  # Using city as district if not available
            'website': row.get('Website', 'N/A'),
            'college_is_active': _parse_checkbox(row.get('Active', False)),
            'is_college_verified': _parse_checkbox(row.get('Verified', False)),
            'alternative_names': [],
            'accreditations': _parse_accreditations(row.get('Accreditations', 0)),
            'infrastructure': _parse_infrastructure(row.get('Facilities', 0)),
            'utilities': [],
            'nearby_places': []
        }
        colleges.append(college)

    return colleges


def _parse_checkbox(value) -> bool:
    """Parse checkbox values (✅/❌) to boolean."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip() in ['✅', 'Yes', 'yes', 'True', 'true', '1']
    return False


def _parse_accreditations(count) -> List[Dict[str, Any]]:
    """
    Create placeholder accreditation entries based on count.

    Args:
        count: Number of accreditations

    Returns:
        List of accreditation dictionaries
    """
    try:
        count = int(count)
    except (ValueError, TypeError):
        count = 0

    accreditations = []
    for i in range(count):
        accreditations.append({
            'grade': None,
            'status': 'Available',
            'accreditation_body': f'Accreditation #{i+1}',
            'accreditation_body_code': f'acc_{i+1}',
            'accreditation_public_id': f'acc-{i+1}'
        })

    return accreditations


def _parse_infrastructure(count) -> List[Dict[str, Any]]:
    """
    Create placeholder infrastructure entries based on count.

    Args:
        count: Number of facilities

    Returns:
        List of infrastructure dictionaries
    """
    try:
        count = int(count)
    except (ValueError, TypeError):
        count = 0

    infrastructure = []
    categories = ['Academic Spaces', 'Laboratories', 'Library', 'Hostel Facilities',
                  'Sports & Fitness', 'IT Facilities', 'Basic Services']

    for i in range(count):
        category = categories[i % len(categories)]
        infrastructure.append({
            'summary': f'Facility #{i+1} - Description not available in CSV',
            'category': category,
            'facility_name': f'Facility #{i+1}',
            'data_source': 'CSV Import',
            'infrastructure_public_id': f'infra-{i+1}'
        })

    return infrastructure


def display_csv_summary(df: pd.DataFrame) -> None:
    """
    Display a summary of the loaded CSV data.

    Args:
        df: DataFrame to summarize
    """
    st.markdown("### 📊 CSV File Summary")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Colleges", len(df))

    with col2:
        active_count = df['Active'].apply(_parse_checkbox).sum() if 'Active' in df.columns else 0
        st.metric("Active Colleges", int(active_count))

    with col3:
        verified_count = df['Verified'].apply(_parse_checkbox).sum() if 'Verified' in df.columns else 0
        st.metric("Verified Colleges", int(verified_count))

    with col4:
        unique_states = df['State'].nunique() if 'State' in df.columns else 0
        st.metric("States Covered", unique_states)

    st.markdown("---")

    # Show column information
    st.markdown("#### 📋 Available Columns")
    cols_df = pd.DataFrame({
        'Column Name': df.columns,
        'Data Type': df.dtypes.astype(str),
        'Non-Null Count': df.count(),
        'Sample Value': [str(df[col].iloc[0])[:50] if len(df) > 0 else 'N/A' for col in df.columns]
    })
    st.dataframe(cols_df, use_container_width=True, hide_index=True)


def enrich_csv_data_from_db(csv_colleges: List[Dict[str, Any]], db_connection) -> List[Dict[str, Any]]:
    """
    Enrich CSV data with detailed information from the database if available.

    Args:
        csv_colleges: List of college data from CSV
        db_connection: Database connection instance

    Returns:
        Enriched list of college data
    """
    enriched = []

    for college in csv_colleges:
        college_id = college.get('college_id')

        try:
            # Try to fetch detailed data from database
            query = f"""
                SELECT *
                FROM mvx_college_data_flattened
                WHERE college_id = {college_id} AND college_is_active = true
                LIMIT 1;
            """

            result = db_connection.execute_query(query)

            if result and len(result) > 0:
                # Use database data (more detailed)
                enriched.append(result[0])
                st.info(f"✅ Enhanced data for {college.get('name')} from database")
            else:
                # Use CSV data as fallback
                enriched.append(college)
                st.warning(f"⚠️ Using CSV data for {college.get('name')} (not found in database)")

        except Exception as e:
            # If database query fails, use CSV data
            enriched.append(college)
            st.warning(f"⚠️ Database lookup failed for {college.get('name')}: {str(e)}")

    return enriched


def export_to_csv(colleges_data: List[Dict[str, Any]], filename: str = "colleges_export.csv") -> str:
    """
    Export college data to CSV format.

    Args:
        colleges_data: List of college data dictionaries
        filename: Output filename

    Returns:
        CSV string
    """
    # Create simplified version for CSV export
    export_data = []

    for college in colleges_data:
        export_data.append({
            'ID': college.get('college_id', 'N/A'),
            'Name': college.get('name', 'N/A'),
            'City': college.get('city', 'N/A'),
            'State': college.get('state', 'N/A'),
            'Active': '✅' if college.get('college_is_active') else '❌',
            'Verified': '✅' if college.get('is_college_verified') else '❌',
            'Accreditations': len(college.get('accreditations', [])),
            'Facilities': len(college.get('infrastructure', [])),
            'Website': college.get('website', 'N/A')
        })

    df = pd.DataFrame(export_data)
    return df.to_csv(index=False)
