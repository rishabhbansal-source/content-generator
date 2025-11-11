# <� College Content Generator

An AI-powered content generation system for creating high-quality educational content about colleges, universities, and higher education programs.

## Features

- **Multi-LLM Support**: Choose from OpenAI GPT, Google Gemini, Anthropic Claude, or xAI Grok
- **Database Integration**: Connects to PostgreSQL database with comprehensive college information
- **Intelligent Data Fetching**: Automatically analyzes queries and fetches relevant data
- **Multiple Content Types**: Support for 23+ content formats (articles, FAQs, comparisons, case studies, etc.)
- **Prompt Variations**: Generates multiple creative prompt variations for content
- **Structured Templates**: Creates detailed content outlines before generation
- **Trend Integration**: Optional SerpAPI integration for latest trends and news
- **Interactive UI**: Single-page Streamlit interface for seamless workflow
- **Markdown Output**: Generates clean, formatted markdown content

## Prerequisites

- Python 3.8+
- [uv](https://github.com/astral-sh/uv) - Fast Python package installer
- PostgreSQL database with college data
- API keys for at least one LLM provider
- (Optional) SerpAPI key for trend data

## Installation

1. **Install uv** (if not already installed):
   ```bash
   # macOS/Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # Windows
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

   # Or via pip
   pip install uv
   ```

2. **Clone/Navigate to the repository**:
   ```bash
   cd /path/to/blog-generator
   ```

3. **Quick Setup (Recommended)**:

   Use the provided setup scripts for automated installation:

   **macOS/Linux:**
   ```bash
   ./setup.sh
   ```

   **Windows (PowerShell):**
   ```powershell
   .\setup.ps1
   ```

   The setup script will:
   - Install uv (if not already installed)
   - Create a virtual environment
   - Install all dependencies
   - Create .env file from template

4. **Manual Setup**:

   **Option A: Using pyproject.toml (Recommended)**
   ```bash
   # Create virtual environment and install from pyproject.toml
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate

   # Install project dependencies
   uv pip install -e .

   # Or install with dev dependencies
   uv pip install -e ".[dev]"
   ```

   **Option B: Using requirements.txt**
   ```bash
   # Create virtual environment
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate

   # Install from requirements.txt
   uv pip install -r requirements.txt
   ```

5. **Configure environment** (if not using setup script):
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials and API keys
   ```

## Configuration

### Database Setup

Edit `.env` file with your PostgreSQL credentials:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=your_database_name
DB_USER=your_username
DB_PASSWORD=your_password
```

### API Keys

You can either:
1. Set API keys in `.env` file (static)
2. Enter API keys in the Streamlit UI (recommended for security)

```env
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=AI...
ANTHROPIC_API_KEY=sk-ant-...
GROK_API_KEY=xai-...
SERPAPI_API_KEY=your_serpapi_key
```

## Usage

### Running the Application

```bash
streamlit run app.py
```

The application will open in your browser at `http://localhost:8501`

### How Content Generation Works

The system uses a **6-step progressive workflow** with user control at each stage:

### Step 1: User Input & System Initialization

**User provides:**
- LLM provider selection (OpenAI/Gemini/Claude/Grok) + API key
- Content type (blog, article, FAQ, comparison, etc.)
- Natural language query (e.g., "Write about top engineering colleges in Mumbai")
- Optional: Specific college selection from dropdown

**System initializes:**
- LLM connection and testing
- PostgreSQL database connection
- SimpleQueryAgent (data fetching)
- PromptAgent (prompt variations)
- TemplateAgent (content structure)
- ContentAgent (final content)

### Step 2: Data Fetching (SimpleQueryAgent)

**Process:**
1. Extract filters from user query (city, state, keywords)
2. Build simple SQL query to `mvx_college_data_flattened` materialized view
3. Execute query and fetch comprehensive college data

**Example Queries:**
```sql
-- Specific college
SELECT * FROM mvx_college_data_flattened
WHERE college_id = 457 AND college_is_active = true;

-- Filtered by city
SELECT * FROM mvx_college_data_flattened
WHERE college_is_active = true AND LOWER(city) = 'mumbai'
ORDER BY year_of_established DESC LIMIT 50;
```

**Returns:** Complete college data with 32 fields including:
- Basic info (name, city, state, address, established year)
- Rankings (JSON with NIRF, NAAC ratings)
- Accreditations (JSON with grades, bodies, validity)
- Degrees (JSON with programs, duration, seats)
- Infrastructure (JSON with facilities, labs, sports)
- Contact info, fees, faculty ratio, and more

### Step 3: Prompt Generation (PromptAgent)

**LLM generates 5 creative prompt variations**, each with:
- **Title**: Catchy, SEO-friendly headline
- **Angle**: Unique perspective (rankings-focused, cost-focused, placement-focused, etc.)
- **Description**: What the content will cover

**Example variations:**
1. "Top 10 Engineering Colleges in Mumbai 2024" - Rankings & placements angle
2. "Mumbai Engineering Colleges: Complete Fee Structure" - Cost comparison angle
3. "Student Life at Mumbai's Best Engineering Colleges" - Campus experience angle

**User selects one prompt** and can edit title, angle, or description.

### Step 4: Template Generation (TemplateAgent)

**LLM creates a structured content outline** based on:
- Selected prompt (title, angle, description)
- Content type requirements (length, tone, typical sections)
- Available college data (first 5 records shown)
- Latest trends (if SerpAPI enabled)

**Example template:**
```markdown
# Top 10 Engineering Colleges in Mumbai 2024

## Introduction
- Overview of Mumbai's engineering landscape
- Selection criteria

## Top 10 Colleges Detailed
### 1. [College Name]
- NIRF Ranking & NAAC Grade
- Established year & accreditations
- Key programs offered
- Infrastructure highlights

## Comparison Tables
- Rankings comparison
- Fee structure comparison
- Placement records

## Admission Process
- Eligibility criteria
- Important dates
- Application process

## Conclusion
- Summary & recommendations
```

**User reviews and can modify** sections before content generation.

### Step 5: Final Content Generation (ContentAgent)

**LLM generates complete markdown content** using:
- Approved template structure
- Full college data from database
- Latest trends (if SerpAPI enabled)
- Content type guidelines (tone, length, style)

**The LLM receives actual data** like:
```json
{
  "name": "Maharashtra National Law University Mumbai",
  "city": "Mumbai",
  "year_of_established": 2014,
  "rankings": {"NIRF": {"rank": 15, "year": 2024}},
  "degrees": [{"name": "BA LLB", "seats": 120}],
  "infrastructure": {"library": "50,000+ books"},
  "total_degrees": 6
}
```

**Output:** Publication-ready markdown with:
- Factual information from database
- Proper structure following template
- SEO-optimized headings and content
- Specific details (rankings, fees, dates)

### Step 6: Review & Edit

**User can:**
- Review the generated content
- Make edits directly in the interface
- Copy to clipboard or download as markdown
- Regenerate with different instructions if needed

---

## Workflow Quick Reference

```
User Input
    ↓
┌─────────────────────┐
│ SimpleQueryAgent    │ → SQL Query → mvx_college_data_flattened → College Data
└─────────────────────┘
    ↓
┌─────────────────────┐
│ PromptAgent + LLM   │ → 5 Variations → User Selects & Edits
└─────────────────────┘
    ↓
┌─────────────────────┐
│ TemplateAgent + LLM │ → Content Outline → User Reviews & Modifies
└─────────────────────┘
    ↓
┌─────────────────────┐
│ ContentAgent + LLM  │ → Final Markdown → User Edits & Publishes
└─────────────────────┘
```

## Key Features of Data-Driven Generation

- **Accurate**: Uses real database records, not hallucinated information
- **Comprehensive**: Access to 32 fields per college including JSON objects
- **Fast**: Simple queries to pre-computed materialized view
- **Flexible**: 23+ content types with customizable templates
- **Controllable**: Human-in-the-loop at every stage

## Content Types Supported

- Web Articles
- FAQ Pages
- How-To Guides
- Comparison Tables
- Buyer's Guides
- Checklists
- Case Studies
- Review Roundups
- Press Releases
- And 15+ more formats!

## Project Structure

```
blog-generator/
   config/              # Configuration modules
      database.py      # Database configuration
      llm_config.py    # LLM configuration
   database/            # Database modules
      connection.py    # PostgreSQL connection
      schema_parser.py # DBML schema parser
      query_generator.py # SQL query generator
   models/              # LLM implementations
      llm_interface.py # Abstract LLM interface
      openai_model.py  # OpenAI implementation
      gemini_model.py  # Google Gemini implementation
      claude_model.py  # Anthropic Claude implementation
      grok_model.py    # xAI Grok implementation
      llm_factory.py   # LLM factory
   agents/              # AI agents
      query_agent.py   # Query analysis & SQL generation
      prompt_agent.py  # Prompt generation
      template_agent.py # Template creation
      content_agent.py # Content generation
   utils/               # Utilities
      serpapi_helper.py # SerpAPI integration
      content_types.py  # Content type definitions
   app.py               # Main Streamlit application
   database.dbml        # Database schema
   requirements.txt     # Python dependencies
   .env.example         # Environment template
   README.md            # This file
```

## Troubleshooting

### Database Connection Issues

1. Verify PostgreSQL is running:
   ```bash
   pg_isready
   ```

2. Check credentials in `.env` file

3. Test connection:
   ```bash
   psql -h localhost -U your_username -d your_database
   ```

### LLM API Errors

1. Verify API key is correct
2. Check API quota/limits
3. Ensure internet connectivity
4. Try a different model

### Module Import Errors

1. Ensure virtual environment is activated
2. Reinstall dependencies:
   ```bash
   uv pip install -r requirements.txt --reinstall
   ```

### uv-Specific Tips

- **Fast installation**: uv is 10-100x faster than pip
- **Check uv version**: `uv --version`
- **Update uv**: `uv self update`
- **Clear cache**: `uv cache clean`

### Quick uv Command Reference

```bash
# Create virtual environment
uv venv

# Activate virtual environment
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows

# Install from pyproject.toml
uv pip install -e .

# Install specific package
uv pip install package-name

# Install from requirements.txt
uv pip install -r requirements.txt

# Sync exact versions (removes unneeded packages)
uv pip sync requirements.txt

# Update a package
uv pip install --upgrade package-name

# List installed packages
uv pip list

# Show package info
uv pip show package-name

# Uninstall package
uv pip uninstall package-name
```

## Best Practices

1. **API Keys**: Never commit API keys to version control
2. **Data Privacy**: Don't include sensitive data in generated content
3. **Rate Limits**: Be mindful of API rate limits
4. **Content Review**: Always review AI-generated content before publishing
5. **Database Queries**: Monitor generated SQL queries for performance

## Advanced Features

### Custom Content Types

Add custom content types in `utils/content_types.py`:

```python
ContentType.CUSTOM_TYPE = "custom_type"

CONTENT_TYPE_METADATA[ContentType.CUSTOM_TYPE] = ContentTypeMetadata(
    name="Custom Type",
    description="Your custom content type",
    typical_sections=["Intro", "Main", "Conclusion"],
    ideal_length="1000-1500 words",
    tone="Professional"
)
```

### Database Schema Customization

If your database schema differs from `database.dbml`, update the DBML file to match your structure.

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For issues and questions:
- Create an issue in the repository
- Check existing documentation
- Review logs in the Streamlit interface

## Acknowledgments

- Built with Streamlit
- Powered by LangChain
- Supports multiple LLM providers
- Database schema for college management

---

**Happy Content Creating! <�(**
# content-generator
