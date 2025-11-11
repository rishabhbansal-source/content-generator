"""Utility functions for displaying college data in Streamlit UI."""

import streamlit as st
import json
from typing import Dict, List, Any


def display_college_card(college_data: Dict[str, Any], index: int = 0) -> None:
    """
    Display a single college's data in a comprehensive card format.

    Args:
        college_data: Dictionary containing college information
        index: Index number for unique key generation
    """
    # Basic Information Header
    st.markdown(f"""
    <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 20px; border-radius: 10px 10px 0 0; color: white;'>
        <h2 style='margin: 0; color: white;'>{college_data.get('name', 'N/A')}</h2>
        <p style='margin: 5px 0 0 0; opacity: 0.9;'>
            📍 {college_data.get('city', 'N/A')}, {college_data.get('state', 'N/A')}
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Main content container
    with st.container():
        st.markdown("""
        <div style='border: 2px solid #667eea; border-top: none;
                    border-radius: 0 0 10px 10px; padding: 20px; margin-bottom: 20px;'>
        """, unsafe_allow_html=True)

        # Create tabs for different sections
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "📋 Basic Info",
            "🏅 Accreditations",
            "🏗️ Infrastructure",
            "🗺️ Nearby Places",
            "🚉 Utilities",
            "🔗 Raw Data"
        ])

        with tab1:
            _display_basic_info(college_data)

        with tab2:
            _display_accreditations(college_data)

        with tab3:
            _display_infrastructure(college_data)

        with tab4:
            _display_nearby_places(college_data)

        with tab5:
            _display_utilities(college_data)

        with tab6:
            _display_raw_data(college_data)

        st.markdown("</div>", unsafe_allow_html=True)


def _display_basic_info(college_data: Dict[str, Any]) -> None:
    """Display basic college information."""
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🎓 General Information")
        st.markdown(f"**College ID:** `{college_data.get('college_id', 'N/A')}`")
        st.markdown(f"**Name:** {college_data.get('name', 'N/A')}")
        st.markdown(f"**City:** {college_data.get('city', 'N/A')}")
        st.markdown(f"**State:** {college_data.get('state', 'N/A')}")
        st.markdown(f"**District:** {college_data.get('district', 'N/A')}")

    with col2:
        st.markdown("### 🌐 Online Presence")
        website = college_data.get('website', 'N/A')
        if website and website != 'NA':
            st.markdown(f"**Website:** [{website}]({website})")
        else:
            st.markdown(f"**Website:** Not Available")

        st.markdown(f"**Active:** {'✅ Yes' if college_data.get('college_is_active') else '❌ No'}")
        st.markdown(f"**Verified:** {'✅ Yes' if college_data.get('is_college_verified') else '❌ No'}")

        # Alternative names
        alt_names = college_data.get('alternative_names', [])
        if alt_names and isinstance(alt_names, list) and len(alt_names) > 0:
            st.markdown("**Alternative Names:**")
            for name in alt_names:
                st.markdown(f"- {name}")


def _display_accreditations(college_data: Dict[str, Any]) -> None:
    """Display accreditation information."""
    accreditations = college_data.get('accreditations', [])

    if not accreditations or len(accreditations) == 0:
        st.info("ℹ️ No accreditation information available")
        return

    st.markdown(f"### 🏅 Total Accreditations: {len(accreditations)}")

    for i, acc in enumerate(accreditations, 1):
        # Use container instead of expander to avoid nesting
        with st.container():
            st.markdown(f"#### {i}. {acc.get('accreditation_body', 'N/A')}")
            col1, col2 = st.columns(2)
            with col1:
                status = acc.get('status', 'N/A')
                status_color = "🟢" if status == "Approved" else "🟡"
                st.markdown(f"**Status:** {status_color} {status}")
                st.markdown(f"**Body:** {acc.get('accreditation_body', 'N/A')}")
            with col2:
                grade = acc.get('grade')
                st.markdown(f"**Grade:** {grade if grade else 'Not Specified'}")
                st.markdown(f"**Code:** `{acc.get('accreditation_body_code', 'N/A')}`")
            st.markdown("---")


def _display_infrastructure(college_data: Dict[str, Any]) -> None:
    """Display infrastructure facilities."""
    infrastructure = college_data.get('infrastructure', [])

    if not infrastructure or len(infrastructure) == 0:
        st.info("ℹ️ No infrastructure information available")
        return

    # Group by category
    categories = {}
    for facility in infrastructure:
        category = facility.get('category', 'Other')
        if category not in categories:
            categories[category] = []
        categories[category].append(facility)

    st.markdown(f"### 🏗️ Total Facilities: {len(infrastructure)}")
    st.markdown(f"**Categories:** {', '.join(categories.keys())}")

    # Display by category - use containers instead of expanders
    for category, facilities in categories.items():
        st.markdown(f"#### {category} ({len(facilities)})")

        for facility in facilities:
            with st.container():
                st.markdown(f"**{facility.get('facility_name', 'N/A')}**")
                st.markdown(facility.get('summary', 'No description available'))
                st.caption(f"📊 Data Source: {facility.get('data_source', 'N/A')}")
                st.markdown("---")


def _display_nearby_places(college_data: Dict[str, Any]) -> None:
    """Display nearby places information."""
    nearby_places = college_data.get('nearby_places', [])

    if not nearby_places or len(nearby_places) == 0:
        st.info("ℹ️ No nearby places information available")
        return

    # Group by place type
    place_types = {}
    for place in nearby_places:
        place_type = place.get('place_type', 'other')
        if place_type not in place_types:
            place_types[place_type] = []
        place_types[place_type].append(place)

    st.markdown(f"### 🗺️ Total Places: {len(nearby_places)}")

    # Create tabs for each place type
    if place_types:
        tabs = st.tabs(list(place_types.keys()))

        for tab, (place_type, places) in zip(tabs, place_types.items()):
            with tab:
                for place in places:
                    with st.container():
                        st.markdown(f"**📍 {place.get('place_name', 'N/A')}**")

                        distance = place.get('distance')
                        if distance:
                            st.markdown(f"*Distance: {distance}*")

                        about = place.get('about')
                        if about:
                            st.markdown(f"> {about}")

                        st.markdown("---")


def _display_utilities(college_data: Dict[str, Any]) -> None:
    """Display nearby utilities information."""
    utilities = college_data.get('utilities', [])

    if not utilities or len(utilities) == 0:
        st.info("ℹ️ No utilities information available")
        return

    st.markdown(f"### 🚉 Total Utilities: {len(utilities)}")

    # Group by utility type
    utility_types = {}
    for utility in utilities:
        util_type = utility.get('utility_type', 'other')
        if util_type not in utility_types:
            utility_types[util_type] = []
        utility_types[util_type].append(utility)

    # Display in columns
    for util_type, items in utility_types.items():
        st.markdown(f"#### {util_type.replace('_', ' ').title()}")

        for item in items:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**{item.get('name', 'N/A')}**")
            with col2:
                distance = item.get('distance', 'N/A')
                st.markdown(f"📏 {distance} km" if distance != 'N/A' else "Distance N/A")

        st.markdown("---")


def _display_raw_data(college_data: Dict[str, Any]) -> None:
    """Display raw JSON data."""
    st.markdown("### 🔍 Complete Data Structure")
    st.json(college_data)


def display_colleges_table(colleges_data: List[Dict[str, Any]]) -> None:
    """
    Display a summary table of multiple colleges.

    Args:
        colleges_data: List of college data dictionaries
    """
    import pandas as pd

    if not colleges_data or len(colleges_data) == 0:
        st.warning("⚠️ No college data available")
        return

    # Create summary dataframe
    summary_data = []
    for college in colleges_data:
        summary_data.append({
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

    df = pd.DataFrame(summary_data)

    st.markdown(f"### 📊 Summary of {len(colleges_data)} College(s)")
    st.dataframe(
        df,
        width='stretch',
        hide_index=True,
        column_config={
            "Website": st.column_config.LinkColumn("Website"),
            "Accreditations": st.column_config.NumberColumn("Accreditations", format="%d"),
            "Facilities": st.column_config.NumberColumn("Facilities", format="%d"),
        }
    )


def display_college_data_preview(colleges_data: List[Dict[str, Any]], max_display: int = 5, use_expander: bool = True) -> None:
    """
    Display a preview of college data with option to expand.

    Args:
        colleges_data: List of college data dictionaries
        max_display: Maximum number of colleges to display in detail
        use_expander: Whether to use expander for additional colleges (set to False if already in an expander)
    """
    if not colleges_data or len(colleges_data) == 0:
        st.warning("⚠️ No college data available")
        return

    st.markdown(f"## 🎓 College Data Preview ({len(colleges_data)} record(s))")

    # Show summary table first
    display_colleges_table(colleges_data)

    st.markdown("---")

    # Display detailed cards
    st.markdown("### 📋 Detailed View")

    display_count = min(len(colleges_data), max_display)

    if len(colleges_data) > max_display:
        st.info(f"ℹ️ Showing {display_count} of {len(colleges_data)} colleges. Use filters to narrow down results.")

    for i, college in enumerate(colleges_data[:display_count]):
        display_college_card(college, i)

    if len(colleges_data) > max_display:
        if use_expander:
            with st.expander(f"📚 View remaining {len(colleges_data) - max_display} colleges"):
                for i, college in enumerate(colleges_data[max_display:], display_count):
                    display_college_card(college, i)
        else:
            # If we can't use expander, show a button to toggle visibility
            if st.button(f"📚 Show remaining {len(colleges_data) - max_display} colleges"):
                for i, college in enumerate(colleges_data[max_display:], display_count):
                    display_college_card(college, i)
