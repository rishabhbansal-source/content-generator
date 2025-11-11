"""Main Streamlit application for content generation."""

import streamlit as st
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Changed to DEBUG for better troubleshooting
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import modules
from models.llm_factory import LLMFactory
from database.connection import DatabaseConnection
from agents.simple_query_agent import SimpleQueryAgent
from agents.topic_agent import TopicAgent
from agents.template_agent import TemplateAgent
from agents.content_agent import ContentAgent
from utils.serpapi_helper import SerpAPIHelper
from utils.content_types import get_content_type_options, get_content_type_display_names
from utils.college_data_display import display_college_data_preview
from config.llm_config import MODEL_OPTIONS

# Page configuration
st.set_page_config(
    page_title="College Content Generator",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
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
    .section-header {
        font-size: 1.5rem;
        font-weight: bold;
        margin-top: 2rem;
        margin-bottom: 1rem;
        color: #2c3e50;
    }
    .stButton>button {
        width: 100%;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        margin: 1rem 0;
    }
    .info-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        margin: 1rem 0;
    }
    .selected-prompt-box {
        padding: 1.5rem;
        border-radius: 0.5rem;
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        border: 2px solid #667eea;
        margin: 1rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    .topic-card {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: white;
        border: 1px solid #e1e4e8;
        margin: 0.5rem 0;
        transition: all 0.3s ease;
    }
    .topic-card:hover {
        border-color: #667eea;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.15);
        transform: translateY(-2px);
    }
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """Initialize Streamlit session state variables."""
    if 'llm' not in st.session_state:
        st.session_state.llm = None
    if 'db' not in st.session_state:
        st.session_state.db = None
    if 'query_agent' not in st.session_state:
        st.session_state.query_agent = None
    if 'topic_agent' not in st.session_state:
        st.session_state.topic_agent = None
    if 'template_agent' not in st.session_state:
        st.session_state.template_agent = None
    if 'content_agent' not in st.session_state:
        st.session_state.content_agent = None
    if 'serp_helper' not in st.session_state:
        st.session_state.serp_helper = None

    # College selection
    if 'colleges_list' not in st.session_state:
        st.session_state.colleges_list = []
    if 'selected_college' not in st.session_state:
        st.session_state.selected_college = None

    # Workflow state
    if 'data_fetched' not in st.session_state:
        st.session_state.data_fetched = False
    if 'topics_generated' not in st.session_state:
        st.session_state.topics_generated = False
    if 'template_generated' not in st.session_state:
        st.session_state.template_generated = False
    if 'content_generated' not in st.session_state:
        st.session_state.content_generated = False

    # Data storage
    if 'fetched_data' not in st.session_state:
        st.session_state.fetched_data = None
    if 'generated_topics' not in st.session_state:
        st.session_state.generated_topics = []
    if 'selected_topic' not in st.session_state:
        st.session_state.selected_topic = None
    if 'user_prompt' not in st.session_state:
        st.session_state.user_prompt = ""
    if 'template' not in st.session_state:
        st.session_state.template = None
    if 'final_content' not in st.session_state:
        st.session_state.final_content = ""


def sidebar_configuration():
    """Render sidebar configuration."""
    with st.sidebar:
        st.markdown("## ⚙️ Configuration")

        # LLM Provider Selection
        st.markdown("### LLM Provider")
        provider_options = list(MODEL_OPTIONS.keys())
        selected_provider = st.selectbox(
            "Choose Provider",
            provider_options,
            key="provider_select"
        )

        # Model Selection
        model_options = MODEL_OPTIONS[selected_provider]
        selected_model_name = st.selectbox(
            "Choose Model",
            list(model_options.keys()),
            key="model_select"
        )
        selected_model = model_options[selected_model_name]

        # API Key Input
        api_key = st.text_input(
            f"{selected_provider} API Key",
            type="password",
            key="api_key_input",
            help="Enter your API key. It will only be stored in session memory."
        )

        # LLM Parameters
        with st.expander("Advanced Settings"):
            temperature = st.slider(
                "Temperature",
                min_value=0.0,
                max_value=1.0,
                value=0.7,
                step=0.1,
                help="Higher values make output more creative"
            )

            max_tokens = st.number_input(
                "Max Tokens",
                min_value=500,
                max_value=8000,
                value=4000,
                step=500
            )

        # SerpAPI Key
        st.markdown("### SerpAPI (Optional)")
        serp_api_key = st.text_input(
            "SerpAPI Key",
            type="password",
            key="serp_key_input",
            help="Optional: For fetching latest trends and info"
        )

        # Initialize button
        if st.button("🚀 Initialize System", type="primary"):
            if not api_key:
                st.error("Please provide an API key")
                return

            try:
                with st.spinner("Initializing system..."):
                    # Initialize LLM
                    provider_map = {
                        "OpenAI": "openai",
                        "Google Gemini": "gemini",
                        "Anthropic Claude": "claude",
                        "xAI Grok": "grok"
                    }

                    st.session_state.llm = LLMFactory.create_from_params(
                        provider=provider_map[selected_provider],
                        api_key=api_key,
                        model_name=selected_model,
                        temperature=temperature,
                        max_tokens=max_tokens
                    )

                    # Test LLM connection
                    if st.session_state.llm.test_connection():
                        st.success("✅ LLM initialized successfully!")
                    else:
                        st.error("❌ LLM connection failed. Please check your API key and try again.")
                        # Reset LLM to None so user knows system isn't ready
                        st.session_state.llm = None
                        return

                    # Initialize database
                    try:
                        db = DatabaseConnection()
                        if db.test_connection():
                            st.success("✅ Database connected!")
                        else:
                            st.error("❌ Database connection test failed")
                            return
                    except (ValueError, ConnectionError) as db_error:
                        # Display detailed database connection error
                        error_msg = str(db_error)
                        st.error("❌ Database Connection Failed")
                        with st.expander("🔍 Error Details & Solutions", expanded=True):
                            st.markdown(f"**Error:** {error_msg}")
                            st.markdown("---")
                            st.markdown("### 📋 Setup Instructions")
                            st.markdown("""
                            1. **Create a `.env` file** in your project root with:
                               ```env
                               DB_HOST=your_database_host
                               DB_PORT=5432
                               DB_NAME=your_database_name
                               DB_USER=your_username
                               DB_PASSWORD=your_password
                               ```
                            
                            2. **If using a local PostgreSQL server:**
                               - Make sure PostgreSQL is running
                               - Verify credentials in `.env`
                            
                            3. **If using a remote database (recommended for cloud deployments):**
                               - Use your database provider's connection details
                               - Ensure firewall rules allow connections from your IP
                               - For Streamlit Cloud: Use environment variables in app settings
                            """)
                        logger.error(f"Database initialization error: {db_error}", exc_info=True)
                        return
                    except Exception as db_error:
                        st.error(f"❌ Database initialization failed: {str(db_error)}")
                        logger.error(f"Database initialization error: {db_error}", exc_info=True)
                        return

                    # Store database connection
                    st.session_state.db = db

                    # Load colleges list
                    colleges_query = """
                        SELECT college_id, name as college_name, city, state
                        FROM mvx_college_data_flattened
                        WHERE college_is_active = true
                        ORDER BY name
                        LIMIT 100;
                    """
                    st.session_state.colleges_list = db.execute_query(colleges_query)
                    st.info(f"📚 Loaded {len(st.session_state.colleges_list)} colleges")

                    # Initialize agents
                    st.session_state.query_agent = SimpleQueryAgent(
                        st.session_state.llm,
                        db
                    )
                    st.session_state.topic_agent = TopicAgent(st.session_state.llm)
                    st.session_state.template_agent = TemplateAgent(st.session_state.llm)
                    st.session_state.content_agent = ContentAgent(st.session_state.llm)

                    # Initialize SerpAPI if key provided
                    if serp_api_key:
                        st.session_state.serp_helper = SerpAPIHelper(serp_api_key)
                        if st.session_state.serp_helper.test_connection():
                            st.success("✅ SerpAPI initialized!")
                        else:
                            st.warning("⚠️ SerpAPI connection failed")
                    else:
                        st.session_state.serp_helper = None
                        st.info("ℹ️ SerpAPI not configured")

                    st.success("🎉 System ready!")

            except Exception as e:
                st.error(f"Error initializing system: {str(e)}")
                logger.error(f"Initialization error: {e}", exc_info=True)

        # System status
        if st.session_state.llm:
            st.markdown("---")
            st.markdown("### ✅ System Status")
            st.success("LLM: Ready")
            st.success("Database: Connected")
            if st.session_state.serp_helper:
                st.success("SerpAPI: Active")


def main_interface():
    """Render main content interface."""
    st.markdown('<div class="main-header">🎓 College Content Generator</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Generate high-quality educational content powered by AI</div>', unsafe_allow_html=True)

    # Check if system is initialized
    if not st.session_state.llm:
        st.info("👈 Please configure and initialize the system using the sidebar")
        st.markdown("""
        ### Getting Started:
        1. Select your preferred LLM provider
        2. Choose a model
        3. Enter your API key
        4. (Optional) Add SerpAPI key for trend data
        5. Click "Initialize System"
        """)
        return

    # Section 1: Content Type & College Selection
    st.markdown('<div class="section-header">📝 Step 1: Select Content Type & College</div>', unsafe_allow_html=True)

    # Content Type Selection
    content_type_options = get_content_type_options()
    display_names = get_content_type_display_names()

    content_type = st.selectbox(
        "Content Type",
        content_type_options,
        format_func=lambda x: display_names.get(x, x),
        key="content_type"
    )

    # College Selection (Optional)
    st.markdown("#### 🎯 College Selection (Optional)")
    
    # Filter options container
    filter_option = st.radio(
        "Filter colleges by:",
        ["Search by Name/City", "Select from List"],
        key="college_filter_option",
        horizontal=False
    )
    
    selected_college_id = None
    
    # Handle different filter options
    if filter_option == "All Colleges":
        st.session_state.selected_college = None
        st.info("ℹ️ Content will be generated for all colleges matching your query")
    
    elif filter_option == "Search by Name/City":
        if not st.session_state.db:
            st.warning("⚠️ Please initialize the system first to enable college search")
        else:
            search_term = st.text_input(
                "Search colleges",
                placeholder="Enter college name, city, or state",
                key="college_search",
                help="Search for colleges by name, city, or state"
            )

            if search_term:
                with st.spinner("🔍 Searching colleges..."):
                    search_query = f"""
                        SELECT college_id, name as college_name, city, state
                        FROM mvx_college_data_flattened
                        WHERE college_is_active = true
                            AND (
                                LOWER(name) LIKE LOWER('%{search_term}%')
                                OR LOWER(city) LIKE LOWER('%{search_term}%')
                                OR LOWER(state) LIKE LOWER('%{search_term}%')
                            )
                        ORDER BY name
                        LIMIT 50;
                    """
                    search_results = st.session_state.db.execute_query(search_query)
                    
                    if search_results:
                        college_options = {
                            f"{c['college_name']} - {c['city']}, {c['state']}": c['college_id']
                            for c in search_results
                        }
                        
                        selected_college_name = st.selectbox(
                            "Select college",
                            list(college_options.keys()),
                            key="searched_college_select",
                            help=f"Found {len(search_results)} matching college(s)"
                        )
                        
                        if selected_college_name:
                            selected_college_id = college_options[selected_college_name]
                            st.session_state.selected_college = selected_college_id
                            st.success(f"✅ Selected: {selected_college_name}")
                    else:
                        st.warning("⚠️ No colleges found matching your search")
                        st.session_state.selected_college = None
            else:
                st.info("💡 Enter a search term to find colleges")
                st.session_state.selected_college = None
    
    elif filter_option == "Select from List":
        if not st.session_state.colleges_list:
            st.warning("⚠️ Please initialize the system first to load college list")
        else:
            college_options = {
                f"{c['college_name']} - {c['city']}, {c['state']}": c['college_id']
                for c in st.session_state.colleges_list[:100]  # Show first 100
            }
            
            selected_college_name = st.selectbox(
                "Select college",
                ["None"] + list(college_options.keys()),
                key="list_college_select",
                help=f"Showing {min(100, len(st.session_state.colleges_list))} colleges from the list"
            )
            
            if selected_college_name != "None":
                selected_college_id = college_options[selected_college_name]
                st.session_state.selected_college = selected_college_id
                st.success(f"✅ Selected: {selected_college_name}")
            else:
                st.session_state.selected_college = None

    if st.button("🔍 Fetch College Data", type="primary"):
        # Check if system is initialized
        if not st.session_state.query_agent:
            st.error("❌ System not initialized. Please initialize the system using the sidebar first.")
            return

        try:
            with st.spinner("Fetching college data..."):
                # Get selected college ID (if any)
                college_id = st.session_state.selected_college if st.session_state.selected_college else None

                # Generate a simple query based on selection
                if college_id:
                    auto_query = f"Fetch detailed information for college ID {college_id}"
                else:
                    auto_query = f"Fetch information about colleges for {content_type} content"

                # Fetch data using simplified agent
                result = st.session_state.query_agent.fetch_college_data(
                    auto_query,
                    content_type,
                    selected_college_id=college_id
                )

                st.session_state.fetched_data = result
                st.session_state.data_fetched = True

                st.success(f"✅ Data fetched successfully! Found {result['row_count']} records")

        except Exception as e:
            st.error(f"Error fetching data: {str(e)}")
            logger.error(f"Data fetch error: {e}", exc_info=True)

    # Show data preview after fetching
    if st.session_state.data_fetched and st.session_state.fetched_data:
        st.markdown("---")

        # Show data preview with enhanced UI
        with st.expander("📊 View Data Preview", expanded=False):
            st.markdown("**SQL Query Used:**")
            st.code(st.session_state.fetched_data['sql_query'], language='sql')

            st.markdown("---")

            if st.session_state.fetched_data['data']:
                # Use the new visualization component (use_expander=False because we're already inside one)
                display_college_data_preview(st.session_state.fetched_data['data'], max_display=3, use_expander=False)
            else:
                st.warning("⚠️ No data returned from the query")

    # Section 2: Topic Generation
    if st.session_state.data_fetched:
        st.markdown("---")
        st.markdown('<div class="section-header">💡 Step 2: Select Content Topic</div>', unsafe_allow_html=True)

        # Generate topics button
        if st.button("✨ Generate Topic Suggestions", key="generate_topics_btn"):
            try:
                with st.spinner("Generating topic ideas based on college data..."):
                    # Prepare data summary
                    data_summary = f"Found {st.session_state.fetched_data['row_count']} college(s)\n"
                    if st.session_state.fetched_data['data']:
                        # Create a concise summary
                        colleges = st.session_state.fetched_data['data'][:3]
                        for college in colleges:
                            data_summary += f"\n- {college.get('name', 'N/A')} in {college.get('city', 'N/A')}, {college.get('state', 'N/A')}"
                            data_summary += f"\n  Accreditations: {len(college.get('accreditations', []))}, Facilities: {len(college.get('infrastructure', []))}"

                    # Generate topics
                    topics = st.session_state.topic_agent.generate_topics(
                        data_summary,
                        content_type,
                        num_topics=8
                    )

                    st.session_state.generated_topics = topics
                    st.session_state.topics_generated = True

                    if topics and len(topics) > 0:
                        st.success(f"✅ Generated {len(topics)} topic ideas!")
                    else:
                        st.warning("⚠️ Using default topic suggestions (custom generation unavailable)")

            except Exception as e:
                st.error(f"Error generating topics: {str(e)}")
                logger.error(f"Topic generation error: {e}", exc_info=True)

        # Display generated topics
        if st.session_state.topics_generated and st.session_state.generated_topics:
            st.markdown("### 📌 Select a Topic")
            st.info("💡 Choose a topic from the suggestions below, or add your own custom topic")

            # Display topics as a clean vertical list
            for i, topic in enumerate(st.session_state.generated_topics):
                with st.container():
                    col1, col2 = st.columns([4, 1])

                    with col1:
                        st.markdown(f"**{i+1}. {topic['topic']}**")
                        st.caption(topic['focus'])

                    with col2:
                        if st.button("Select", key=f"select_topic_{i}", use_container_width=True):
                            st.session_state.selected_topic = topic.copy()
                            st.success(f"✅ Selected: {topic['topic']}")
                            st.rerun()

                    st.markdown("---")

        # Custom topic input
        st.markdown("### ✏️ Or Enter Custom Topic")
        custom_topic = st.text_input(
            "Enter your own topic",
            placeholder="Example: Complete guide to MBA admissions and placements",
            key="custom_topic_input"
        )

        if custom_topic and st.button("Use Custom Topic"):
            st.session_state.selected_topic = {
                "topic": custom_topic,
                "focus": "Custom user-defined topic"
            }
            st.success(f"✅ Using custom topic: {custom_topic}")
            st.rerun()

    # Display selected topic
    if st.session_state.selected_topic:
        st.markdown("---")
        st.markdown('<div class="selected-prompt-box">', unsafe_allow_html=True)
        st.markdown("### 🎯 Selected Topic")
        st.markdown(f"**{st.session_state.selected_topic['topic']}**")
        st.caption(f"Focus: {st.session_state.selected_topic['focus']}")
        st.markdown('</div>', unsafe_allow_html=True)

    # Section 3: Enter Custom Prompt
    if st.session_state.selected_topic:
        st.markdown("---")
        st.markdown('<div class="section-header">📝 Step 3: Define Your Content Prompt</div>', unsafe_allow_html=True)

        # Predefined prompt templates
        prompt_templates = {
            "Custom (Write your own)": "",
            "Comprehensive College Guide": """Write a comprehensive guide about the college(s) in the dataset. The content should include:

1. Overview and Introduction: Brief history, establishment year, location highlights
2. Academic Excellence: Top programs, accreditations, rankings (NIRF, NAAC)
3. Admission Process: Eligibility criteria, entrance exams, application procedures, important dates
4. Fees Structure: Detailed breakdown by program, scholarship opportunities
5. Infrastructure & Facilities: Campus amenities, library, labs, hostels, sports facilities
6. Placements & Career: Average packages, top recruiters, placement statistics
7. Student Life: Clubs, events, cultural activities
8. Contact Information: Address, phone, email, website

Target audience: Students and parents making informed decisions about higher education.
Tone: Professional yet approachable, factual with engaging narrative.""",

            "Comparison & Rankings Focus": """Create a detailed comparison and ranking analysis of the college(s):

1. Rankings Analysis: Break down NIRF rankings, NAAC grades, and other accreditations
2. Program Comparisons: Compare similar programs across metrics (fees, duration, seats)
3. Competitive Analysis: Position relative to other colleges in the region
4. Strengths & Weaknesses: Honest assessment of what makes these colleges stand out
5. Best For: Recommendations for different student profiles
6. Value Proposition: ROI analysis considering fees vs. placement outcomes

Include data-driven insights, statistics, and comparative tables where relevant.
Tone: Analytical, objective, data-focused.""",

            "Admission & Career Guide": """Develop a practical guide focused on admissions and career outcomes:

1. Admission Strategy: Step-by-step application guide, important deadlines
2. Entrance Exam Preparation: Required exams, cutoffs, preparation tips
3. Eligibility Requirements: Academic qualifications, age limits, reservation criteria
4. Career Opportunities: Industry connections, internship programs
5. Placement Track Record: Year-wise placement data, sector-wise distribution
6. Alumni Network: Notable alumni, career trajectories
7. Industry Partnerships: Corporate tie-ups, training programs

Target audience: Aspiring students preparing for admissions.
Tone: Action-oriented, motivational, practical.""",

            "Structured Query Expansion": """Analyze the college(s) data and expand the content across multiple dimensions:

CONTENT DIMENSIONS:
1. Factual Information: Establish year, location, governance type, affiliations
2. Academic Portfolio: Programs offered, specializations, unique courses
3. Infrastructure Deep-dive: Physical facilities, digital infrastructure, accessibility
4. Financial Aspects: Fees structure, payment plans, scholarships, financial aid
5. Quality Metrics: Accreditations, certifications, compliance standards
6. Student Experience: Campus life, diversity, support services
7. Career Pathways: Placement cell, industry connections, entrepreneurship support

TRANSFORMATION TYPES:
- Core Facts: Direct information from database
- Comparative Insights: How it compares with peer institutions
- Implicit Details: What prospective students typically want to know
- Entity Expansions: Detailed breakdowns of programs, facilities, etc.
- User Intent Matching: Address common questions and concerns

Provide comprehensive coverage with proper structure, headings, and data-backed claims.
Tone: Systematic, thorough, information-rich."""
        }

        # Dropdown to select template
        selected_template = st.selectbox(
            "Choose a prompt template or write custom",
            list(prompt_templates.keys()),
            key="prompt_template_select"
        )

        # Get the template text
        template_text = prompt_templates[selected_template]

        # Button to load selected template
        if selected_template != "Custom (Write your own)" and st.button("📋 Load Template"):
            st.session_state.user_prompt = template_text
            st.rerun()

        # User enters their own prompt or edits template
        custom_prompt = st.text_area(
            "Content prompt/instructions",
            value=st.session_state.user_prompt if st.session_state.user_prompt else template_text,
            placeholder="Example: Write a comprehensive guide covering admission process, fees structure, top courses, and placement statistics.",
            height=250,
            key="custom_prompt_input",
            help="Describe what you want in the content - the angle, tone, key points to cover, etc."
        )


        # Update session state when prompt changes
        if custom_prompt != st.session_state.user_prompt:
            st.session_state.user_prompt = custom_prompt

        # Show styled box if prompt is entered
        if st.session_state.user_prompt:
            st.markdown("### 📝 Your Prompt")
            st.markdown(st.session_state.user_prompt)
            st.markdown('</div>', unsafe_allow_html=True)

    # Section 4: Template Generation
    if st.session_state.user_prompt:
        st.markdown("---")
        st.markdown('<div class="section-header">📋 Step 4: Review Content Structure</div>', unsafe_allow_html=True)

        if st.button("🏗️ Generate Content Template", disabled=not st.session_state.user_prompt):
            try:
                with st.spinner("Creating content structure..."):
                    # Prepare data summary
                    data_summary = f"Records: {st.session_state.fetched_data['row_count']}\n"
                    if st.session_state.fetched_data['data']:
                        import json
                        data_summary += json.dumps(st.session_state.fetched_data['data'][:5], indent=2, default=str)

                    # Get SerpAPI context
                    serp_context = ""
                    if st.session_state.serp_helper:
                        serp_context = st.session_state.serp_helper.get_context_for_llm(st.session_state.user_prompt)

                    # Create a prompt dict combining topic and user's custom prompt
                    topic_text = st.session_state.selected_topic['topic'] if st.session_state.selected_topic else ""
                    combined_prompt = f"Topic: {topic_text}\n\n{st.session_state.user_prompt}"

                    user_prompt_dict = {
                        'title': topic_text if topic_text else 'Custom Content',
                        'angle': st.session_state.user_prompt,
                        'description': combined_prompt
                    }

                    # Generate template
                    template = st.session_state.template_agent.generate_template(
                        user_prompt_dict,
                        content_type,
                        data_summary,
                        serp_context
                    )

                    st.session_state.template = template
                    st.session_state.template_generated = True

                    st.success("✅ Content structure created!")

            except Exception as e:
                st.error(f"Error generating template: {str(e)}")
                logger.error(f"Template generation error: {e}", exc_info=True)

        # Display template
        if st.session_state.template_generated and st.session_state.template:
            with st.expander("📄 View Content Structure", expanded=True):
                summary = st.session_state.template_agent.get_template_summary(st.session_state.template)
                st.markdown(summary)

    # Section 5: Content Generation
    if st.session_state.template_generated:
        st.markdown("---")
        st.markdown('<div class="section-header">📰 Step 5: Generate Final Content</div>', unsafe_allow_html=True)

        additional_instructions = st.text_area(
            "Additional instructions (optional)",
            placeholder="Any specific requirements or modifications...",
            height=80
        )

        if st.button("🎨 Generate Content", type="primary"):
            try:
                with st.spinner("Generating your content... This may take a moment..."):
                    # Prepare data
                    import json
                    data_str = json.dumps(st.session_state.fetched_data['data'], indent=2, default=str)

                    # Get SerpAPI context
                    serp_context = ""
                    if st.session_state.serp_helper:
                        serp_context = st.session_state.serp_helper.get_context_for_llm(st.session_state.user_prompt)

                    # Generate content
                    content = st.session_state.content_agent.generate_content(
                        st.session_state.template,
                        data_str,
                        serp_context,
                        additional_instructions
                    )

                    st.session_state.final_content = content
                    st.session_state.content_generated = True

                    st.success("✅ Content generated successfully!")

            except Exception as e:
                st.error(f"Error generating content: {str(e)}")
                logger.error(f"Content generation error: {e}", exc_info=True)

        # Display generated content
        if st.session_state.content_generated and st.session_state.final_content:
            st.markdown("---")
            st.markdown("### 📄 Generated Content")

            # Content editor
            edited_content = st.text_area(
                "Edit content if needed:",
                value=st.session_state.final_content,
                height=500,
                key="content_editor"
            )

            # Action buttons
            col1, col2, col3 = st.columns(3)

            with col1:
                if st.download_button(
                    label="⬇️ Download Markdown",
                    data=edited_content,
                    file_name="generated_content.md",
                    mime="text/markdown"
                ):
                    st.success("Content downloaded!")

            with col2:
                if st.button("📋 Copy to Clipboard"):
                    st.code(edited_content, language='markdown')
                    st.info("Content displayed above. Use your browser to copy.")

            with col3:
                if st.button("🔄 Regenerate"):
                    st.session_state.content_generated = False
                    st.rerun()

            # Preview
            with st.expander("👁️ Preview Rendered Markdown"):
                st.markdown(edited_content)


def main():
    """Main application entry point."""
    initialize_session_state()
    sidebar_configuration()
    main_interface()


if __name__ == "__main__":
    main()
