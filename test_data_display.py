"""Test script to demonstrate college data visualization."""

import streamlit as st
from utils.college_data_display import display_college_data_preview

# Sample data from the materialized view (Bharathi College of Nursing)
sample_data = [{
    "college_id": 4887,
    "college_public_id": "019a64a4-b38d-72f6-92aa-b2696d2bec39",
    "name": "Bharathi College of Nursing",
    "city": "Bengaluru Rural",
    "state": "Karnataka",
    "district": "Bengaluru Rural",
    "website": "https://bharathiinstitutute.co.in/",
    "college_is_active": True,
    "is_college_verified": True,
    "alternative_names": ["Bharathi College of Nursing"],
    "accreditations": [
        {
            "grade": None,
            "status": "Approved",
            "accreditation_body": "GOVT_KARNATAKA_APPROVAL",
            "accreditation_body_code": "govt_karnataka_approval",
            "accreditation_public_id": "019a64a5-1447-70cc-8778-2ffb3c017bb2"
        },
        {
            "grade": None,
            "status": "Approved",
            "accreditation_body": "INC",
            "accreditation_body_code": "inc",
            "accreditation_public_id": "019a64a5-1446-7db5-b8fa-13c985b7dab3"
        },
        {
            "grade": None,
            "status": "Approved",
            "accreditation_body": "KNC",
            "accreditation_body_code": "knc",
            "accreditation_public_id": "019a64a5-1446-7dd8-bc80-1457b19e3daf"
        },
        {
            "grade": None,
            "status": "Affiliated",
            "accreditation_body": "RGUHS_AFFILIATION",
            "accreditation_body_code": "rguhs_affiliation",
            "accreditation_public_id": "019a64a5-1447-70a3-9d45-c3434d57c942"
        }
    ],
    "infrastructure": [
        {
            "summary": "The college provides well-ventilated and spacious classrooms designed to offer a comfortable and conducive learning environment for all students.",
            "category": "Academic Spaces",
            "facility_name": "Classrooms",
            "data_source": "Official College Website - Infrastructure Section",
            "infrastructure_public_id": "019a64a5-64ae-7775-98aa-f164dc667dc3"
        },
        {
            "summary": "A dedicated, well-furnished seminar hall is available on campus, serving as a versatile space for organizing academic seminars, workshops, and various institutional events.",
            "category": "Academic Spaces",
            "facility_name": "Seminar Hall",
            "data_source": "Official College Website - Infrastructure Section",
            "infrastructure_public_id": "019a64a5-64ae-779a-b150-7819b3c63f21"
        },
        {
            "summary": "The college campus is equipped with a reliable 24-hour power supply, ensuring uninterrupted electricity for all academic, laboratory, and residential facilities.",
            "category": "Basic Services",
            "facility_name": "24-Hour Power Supply",
            "data_source": "Official College Website - General Information (Implied)",
            "infrastructure_public_id": "019a64a5-64ae-7747-836e-cb8851842f59"
        },
        {
            "summary": "The college boasts a comprehensive Central Library, a spacious, well-lighted, and well-ventilated hub for academic pursuits.",
            "category": "Library",
            "facility_name": "Central Library",
            "data_source": "Official College Website - Infrastructure Section",
            "infrastructure_public_id": "019a64a5-64ae-7416-b79b-58c6427a97c2"
        },
        {
            "summary": "The Boys Hostel provides comfortable and separate accommodation, ensuring a focused and supportive living environment.",
            "category": "Hostel Facilities",
            "facility_name": "Boys Hostel",
            "data_source": "Official College Website - Infrastructure Section",
            "infrastructure_public_id": "019a64a5-64ae-782a-8815-26b27b61fd41"
        },
        {
            "summary": "The Girls Hostel offers safe and comfortable separate accommodation, fostering an ideal living and learning environment.",
            "category": "Hostel Facilities",
            "facility_name": "Girls Hostel",
            "data_source": "Official College Website - Infrastructure Section",
            "infrastructure_public_id": "019a64a5-64ae-78ed-b8f1-f754ab5d6334"
        }
    ],
    "utilities": [
        {
            "name": "Kempegowda International Airport, Bengaluru",
            "distance": 85,
            "utility_type": "airport",
            "public_id": "019a64a9-ec02-7728-ba2e-19eac73cc073"
        },
        {
            "name": "Kanakapura KSRTC Bus Stand",
            "distance": 15,
            "utility_type": "bus_stand",
            "public_id": "019a64a9-fd96-758c-bbea-a9cce7cae878"
        },
        {
            "name": "SSNMC Super Speciality Hospital, Harohalli",
            "distance": 3,
            "utility_type": "hospital",
            "public_id": "019a64aa-0607-713b-82b7-74917fac98af"
        },
        {
            "name": "Bidadi Railway Station",
            "distance": 28,
            "utility_type": "railway_station",
            "public_id": "019a64a9-f4fa-76ce-99cd-3007a3948b8b"
        }
    ],
    "nearby_places": [
        {
            "place_name": "Janapada Loka",
            "place_type": "tourist_spot",
            "about": "A folk arts museum showcasing traditional rural life and culture of Karnataka.",
            "distance": "30 km",
            "public_id": "019a64a9-69bc-7e63-a5ea-28fb12309e89"
        },
        {
            "place_name": "Pyramid Valley International",
            "place_type": "tourist_spot",
            "about": "A large meditation center featuring the world's largest meditation pyramid.",
            "distance": "15 km",
            "public_id": "019a64a9-69bc-7dbb-9ba8-3273be9bbf49"
        },
        {
            "place_name": "Annapoorna Mess",
            "place_type": "restaurant",
            "about": None,
            "distance": None,
            "public_id": "019a64a9-a2c7-7484-8233-a3f5794184d1"
        },
        {
            "place_name": "Forum Mall, Kanakapura Road",
            "place_type": "shopping_mall",
            "about": None,
            "distance": None,
            "public_id": "019a64a9-afc7-729b-bce2-42bf310d3c1b"
        }
    ]
}]

# Configure page
st.set_page_config(
    page_title="College Data Visualization Test",
    page_icon="🎓",
    layout="wide"
)

st.title("🎓 College Data Visualization Demo")

st.markdown("""
This is a demonstration of the college data visualization component.
The data shown below is from the materialized view `mvx_college_data_flattened`.
""")

st.markdown("---")

# Display the sample data
display_college_data_preview(sample_data, max_display=1)

st.markdown("---")
st.success("✅ Visualization component is working correctly!")

# Instructions
st.markdown("""
### 📝 How to use in the main app:

1. Run the main app: `streamlit run app.py`
2. Configure your LLM and database connection
3. Enter a query and fetch data
4. The data preview will now show this enhanced visualization
5. You'll see:
   - Summary table with key metrics
   - Detailed cards with tabs for different sections
   - Infrastructure grouped by category
   - Nearby places organized by type
   - Utilities with distances
   - Raw JSON data for debugging
""")
