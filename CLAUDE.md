# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

An AI-powered content generation system for creating high-quality educational content about colleges, universities, and higher education programs. The system uses multiple LLM providers (OpenAI, Google Gemini, Anthropic Claude, xAI Grok) to generate structured content based on real PostgreSQL database data.

## Development Setup

### Prerequisites
- Python 3.11+
- PostgreSQL database with college data
- uv package manager (faster alternative to pip)
- API key for at least one LLM provider

### Environment Setup

```bash
# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install from pyproject.toml (recommended)
uv pip install -e .

# Or install from requirements.txt
uv pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your database credentials and API keys
```

### Running the Application

```bash
# Start the Streamlit app
streamlit run app.py
```

The application will be available at `http://localhost:8501`

### Database Requirements

The application requires a PostgreSQL database with a materialized view called `mvx_college_data_flattened` that aggregates college data. This view contains 32 fields including:
- Basic info (college_id, name, city, state, year_of_established)
- Rankings (JSON with NIRF, NAAC ratings)
- Accreditations (JSON with grades, bodies, validity)
- Degrees (JSON with programs, duration, seats)
- Infrastructure (JSON with facilities)
- Contact info, fees, faculty ratio

The database schema is documented in `database.dbml` (57+ tables).

## Architecture

### Multi-Agent Workflow

The system uses a **6-step progressive workflow** where each agent handles a specific task:

1. **SimpleQueryAgent** (`agents/simple_query_agent.py`)
   - Extracts filters from natural language queries (city, state, keywords)
   - Builds SQL queries against `mvx_college_data_flattened` materialized view
   - Fetches comprehensive college data from PostgreSQL
   - Simple filter-based approach (no complex LLM query generation)

2. **PromptAgent** (`agents/prompt_agent.py`)
   - Generates 5 creative prompt variations using LLM
   - Each variation has: title, angle, description
   - User selects and can edit the preferred prompt

3. **TemplateAgent** (`agents/template_agent.py`)
   - Creates structured content outlines based on selected prompt
   - Uses content type metadata to determine structure
   - Incorporates data preview and optional SerpAPI trends
   - User reviews and can modify the template

4. **ContentAgent** (`agents/content_agent.py`)
   - Generates final markdown content following the template
   - Uses full college data from database
   - Incorporates SerpAPI context for latest trends (optional)
   - Supports regeneration, section expansion, and SEO enhancement

### LLM Provider System

The system uses a factory pattern for LLM abstraction:

- **Interface**: `models/llm_interface.py` defines `BaseLLM` abstract class
- **Implementations**:
  - `models/openai_model.py` - OpenAI GPT models
  - `models/gemini_model.py` - Google Gemini
  - `models/claude_model.py` - Anthropic Claude
  - `models/grok_model.py` - xAI Grok
- **Factory**: `models/llm_factory.py` creates instances based on configuration
- **Config**: `config/llm_config.py` contains model options and parameters

All LLM implementations follow the same interface:
```python
def generate(prompt: str, system_prompt: str = None, temperature: float = 0.7, max_tokens: int = 4000) -> str
def test_connection() -> bool
```

### Database Layer

- **Connection**: `database/connection.py` - Singleton connection pool manager
  - Uses psycopg2 with connection pooling (1-10 connections)
  - Methods: `execute_query()`, `execute_update()`, `test_connection()`
  - Returns results as list of dictionaries with column names as keys

- **Schema**: `database/schema_parser.py` - DBML schema parser (not actively used in current workflow)
- **Query Generator**: `database/query_generator.py` - SQL query builder (not actively used; SimpleQueryAgent uses direct SQL)

### Content Type System

Located in `utils/content_types.py`:
- Defines 23+ content types (BLOG, ARTICLE, FAQ, COMPARISON, HOW_TO, etc.)
- Each type has metadata: name, description, typical sections, ideal length, tone
- Used by agents to generate appropriate content structure

### External Integrations

- **SerpAPI**: `utils/serpapi_helper.py` - Optional trend data fetching
  - Provides latest news and trends for content context
  - Can be enabled/disabled per generation

## Key Workflows

### Adding a New LLM Provider

1. Create new model class in `models/` inheriting from `BaseLLM`
2. Implement `generate()` and `test_connection()` methods
3. Add provider to `LLMProvider` enum in `config/llm_config.py`
4. Update `LLMFactory` in `models/llm_factory.py`
5. Add model options to `MODEL_OPTIONS` in `config/llm_config.py`

### Adding a New Content Type

1. Add constant to `ContentType` class in `utils/content_types.py`
2. Create `ContentTypeMetadata` entry with:
   - name, description, typical_sections, ideal_length, tone
3. Add to `CONTENT_TYPE_METADATA` dictionary

### Database Query Development

The system uses `mvx_college_data_flattened` materialized view exclusively. When working with data fetching:
- SimpleQueryAgent builds WHERE clauses based on extracted filters
- Always include `college_is_active = true` filter
- Use LOWER() for case-insensitive string matching
- Limit results appropriately (default: 50)
- Handle NULL values with `NULLS LAST` in ORDER BY

## Important Notes

### Data Flow
- All college data flows through `mvx_college_data_flattened` view
- SimpleQueryAgent does NOT use LLM for query generation (uses rule-based filter extraction)
- Data is passed to LLM agents as JSON strings
- Content generation uses full data, not summaries

### LLM Usage Pattern
- SimpleQueryAgent: No LLM usage (rule-based)
- PromptAgent: Generates 5 variations (1 LLM call)
- TemplateAgent: Creates outline (1 LLM call with data preview)
- ContentAgent: Final generation (1 LLM call with full data)

### Session State Management
The Streamlit app uses extensive session state for workflow progression:
- `st.session_state.llm` - Active LLM instance
- `st.session_state.db` - Database connection
- `st.session_state.query_agent`, `prompt_agent`, `template_agent`, `content_agent` - Agent instances
- `st.session_state.fetched_data`, `generated_prompts`, `selected_prompt`, `template`, `final_content` - Workflow data
- Boolean flags: `data_fetched`, `prompts_generated`, `template_generated`, `content_generated`

### Security Considerations
- API keys stored in session state only (not persisted)
- SQL injection risk: SimpleQueryAgent uses f-strings for filters (consider parameterized queries for production)
- Credentials in .env should never be committed

### Dependencies Management
- Primary dependency file: `pyproject.toml`
- Lock file: `uv.lock` (maintained by uv)
- Legacy: `requirements.txt` (kept for compatibility)
- Use `uv pip install -e .` for development installations
