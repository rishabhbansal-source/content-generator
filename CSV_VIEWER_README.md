# College CSV Viewer

A standalone Streamlit application for loading, visualizing, and enriching college data from CSV files.

## Features

### 📁 Data Loading
- **Upload CSV Files**: Drag and drop CSV files through the web interface
- **Load from File Path**: Specify a path to load CSV files directly
- **Sample Data**: Quick load with sample IIT Bombay data

### 📊 Data Visualization
- **Summary Statistics**: View total colleges, active/verified counts, and state coverage
- **Detailed Cards**: Each college displayed with:
  - 📋 Basic Info (name, location, website, status)
  - 🏅 Accreditations (list of all accreditations)
  - 🏗️ Infrastructure (facilities grouped by category)
  - 🗺️ Nearby Places (tourist spots, restaurants, shopping malls)
  - 🚉 Utilities (airports, bus stands, hospitals, railway stations)
  - 🔗 Raw Data (complete JSON structure)

### 🔄 Data Enrichment
- **Database Integration**: Automatically fetch detailed data from PostgreSQL database
- **Smart Fallback**: Use CSV data when database information is unavailable
- **Validation**: Check which colleges were enriched vs. using CSV data only

### 💾 Export Options
- **Download CSV**: Export processed data back to CSV format
- **Maintains Structure**: Exports summary view with ID, Name, City, State, etc.

## Installation

### Prerequisites
```bash
# Python 3.11+
# PostgreSQL database (optional, for enrichment)
# uv package manager
```

### Setup
```bash
cd /Users/rishabhbansal/HeroVired/Python/blog-generator

# Install dependencies (already done if main app is installed)
uv pip install -e .
```

## Usage

### Launch the CSV Viewer

```bash
streamlit run csv_viewer.py
```

The app will open in your browser at `http://localhost:8501`

### Load Your CSV File

#### Option 1: Upload File
1. Select "Upload CSV File" in the sidebar
2. Drag and drop your CSV or click to browse
3. Click "Load CSV"

#### Option 2: File Path
1. Select "Load from Path" in the sidebar
2. Enter the full path to your CSV file
   - Default: `/Users/rishabhbansal/Downloads/2025-11-11T06-49_export.csv`
3. Click "Load CSV"

#### Option 3: Sample Data
1. Select "Use Sample Data" in the sidebar
2. Click "Load Sample Data"
3. View IIT Bombay example

### Enrich with Database

If you have a PostgreSQL database configured:

1. Check "Enable Database Enrichment"
2. Click "Enrich from Database"
3. The system will:
   - Query the database for each college ID
   - Replace CSV data with detailed database records when found
   - Keep CSV data for colleges not in the database
   - Show status messages for each college

### Export Data

After loading or enriching data:

1. Scroll to the "Export Data" section in the sidebar
2. Click "⬇️ Download CSV"
3. Save the exported file

## CSV Format

### Required Columns

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| ID | Integer | College ID | 3 |
| Name | String | College name | Indian Institute of Technology Bombay |
| City | String | City name | Mumbai |
| State | String | State name | Maharashtra |
| Active | String/Boolean | Active status | ✅ or Yes |
| Verified | String/Boolean | Verified status | ❌ or No |
| Accreditations | Integer | Number of accreditations | 4 |
| Facilities | Integer | Number of facilities | 47 |
| Website | String | College website URL | https://www.iitb.ac.in |

### Example CSV

```csv
ID,Name,City,State,Active,Verified,Accreditations,Facilities,Website
3,Indian Institute of Technology Bombay,Mumbai,Maharashtra,✅,❌,4,47,https://www.iitb.ac.in
10,Delhi University,New Delhi,Delhi,✅,✅,6,52,https://www.du.ac.in
```

## How It Works

### Data Conversion

When you load a CSV file:

1. **Parsing**: Reads CSV using pandas
2. **Conversion**: Transforms each row to college data structure
3. **Placeholder Generation**: Creates placeholder entries for:
   - Accreditations (based on count)
   - Infrastructure/Facilities (distributed across categories)
4. **Visualization**: Displays using enhanced UI components

### Enrichment Process

When enriching from database:

1. For each college in CSV:
   ```sql
   SELECT * FROM mvx_college_data_flattened
   WHERE college_id = {id} AND college_is_active = true
   ```
2. If found: Replace with database record (full details)
3. If not found: Keep CSV data (limited details)
4. Display status for each lookup

### Categories

Infrastructure facilities are auto-assigned to these categories:
- Academic Spaces
- Laboratories
- Library
- Hostel Facilities
- Sports & Fitness
- IT Facilities
- Basic Services

## Troubleshooting

### "File not found" Error
- Check the file path is correct
- Use absolute paths, not relative
- Ensure file has `.csv` extension

### "No data returned from query"
- Check database connection in `.env` file
- Verify college IDs exist in database
- Ensure `mvx_college_data_flattened` view is accessible

### "CSV parse error"
- Verify CSV format matches required columns
- Check for proper encoding (UTF-8)
- Remove any extra columns or formatting

### "Expanders may not be nested"
- This has been fixed in the latest version
- Update `college_data_display.py` if using older version

## Files Structure

```
blog-generator/
├── csv_viewer.py              # Main CSV viewer application
├── utils/
│   ├── csv_loader.py          # CSV loading and conversion
│   └── college_data_display.py # Visualization components
├── database/
│   └── connection.py          # Database connection
└── .env                       # Database credentials
```

## Integration with Main App

The CSV viewer uses the same visualization components as the main content generator app. You can:

1. Export college data from the main app
2. Edit in spreadsheet software
3. Re-import using CSV viewer
4. Enrich with latest database info
5. Use for content generation

## Technical Details

### Performance
- **Lazy Loading**: Only loads what's visible
- **Pagination**: Max 10 colleges displayed by default
- **Caching**: Uses Streamlit session state

### Data Structure
All data converted to standardized format:
```python
{
    'college_id': int,
    'name': str,
    'city': str,
    'state': str,
    'website': str,
    'college_is_active': bool,
    'is_college_verified': bool,
    'accreditations': List[Dict],
    'infrastructure': List[Dict],
    'utilities': List[Dict],
    'nearby_places': List[Dict]
}
```

## Future Enhancements

- [ ] Bulk CSV upload (multiple files)
- [ ] Advanced filtering and search
- [ ] Edit data directly in UI
- [ ] Export to JSON, Excel formats
- [ ] Comparison view for multiple colleges
- [ ] Custom field mapping for different CSV formats

## Support

For issues or questions:
1. Check the main app documentation: `CLAUDE.md`
2. Review database schema: `database.dbml`
3. Check logs in console for error details

## Quick Test

Run this command to test with your file:

```bash
streamlit run csv_viewer.py
```

Then click "Load IIT Bombay Data" button on the main page for instant demo.
