# NASA OSDR Dashboard JSON Generator

A Python script that regenerates the OSDR (Open Science Data Repository) filter-options JSON file by fetching all data in real-time from the OSDR API. **No input files required!**

## Overview

This script:
- ✅ **Fully automated** - Downloads current filter-options and fetches all API data
- ✅ **No input files needed** - Everything is fetched from OSDR in real-time
- ✅ Preserves **ALL** existing values from the current OSDR filter-options
- ✅ Adds new metadata values discovered from the API
- ✅ Creates a new **Mission** grouping with 10 categories
- ✅ Handles misspellings and capitalization differences
- ✅ Generates verification and tracking reports
- ✅ Validates that no original data is lost

## Requirements

- Python 3.7+
- `requests` library (for API calls)

### Installing Requirements

```bash
pip install requests
```

Or if you have permission issues:

```bash
pip install requests --user
```

## Usage

### Simple - Just Run It!

```bash
python3 osdr_generator.py
```

That's it! No arguments, no input files needed.

### What Happens

The script automatically:
1. Downloads current filter-options from `https://osdr.nasa.gov/geode-py/ws/repo/filter-options`
2. Fetches latest metadata from 5 OSDR API endpoints
3. Processes and merges the data
4. Generates output files in your current directory

## Output Files

After running, three files are created in your **current working directory**:

1. **filter-options-new.json** - Complete regenerated JSON with preserved + new values
2. **additions-report.txt** - List of all new values added from API
3. **unmapped-report.txt** - Items that need manual categorization

## What the Script Does

1. **Downloads** current filter-options.json from OSDR
2. **Makes 5 API calls** to fetch latest metadata:
   - Assay Technology Types
   - Factors  
   - Organisms
   - Material Types
   - Missions (new!)
3. **Preserves ALL** existing values
4. **Adds new** values found in API
5. **Creates** new Mission grouping with 10 categories
6. **Verifies** no data loss
7. **Generates** comprehensive reports

## Data Sources

### Current Filter Options
- **URL:** `https://osdr.nasa.gov/geode-py/ws/repo/filter-options`
- Downloaded automatically at runtime

### API Endpoints (JSON Split Format)

1. **Assay Technology Types**  
   `https://visualization.osdr.nasa.gov/biodata/api/v2/query/assays/?investigation.study%20assays.study%20assay%20technology%20type=//&format=json.split`

2. **Factors**  
   `https://visualization.osdr.nasa.gov/biodata/api/v2/query/assays/?investigation.study%20assays.study%20assay%20technology%20type&assay.factor%20value&study.factor%20value&schema&format=json.split`

3. **Organisms**  
   `https://visualization.osdr.nasa.gov/biodata/api/v2/query/assays/?investigation.study%20assays.study%20assay%20technology%20type=//&study.characteristics.organism=//&format=json.split`

4. **Material Types**  
   `https://visualization.osdr.nasa.gov/biodata/api/v2/query/assays/?investigation.study%20assays.study%20assay%20technology%20type=//&study.characteristics.material%20type=//&format=json.split`

5. **Missions**  
   `https://visualization.osdr.nasa.gov/biodata/api/v2/query/assays/?investigation.study%20assays.study%20assay%20technology%20type=//&investigation.study.comment.Project%20Identifier=//&format=json.split`

## Example Output

```bash
$ python3 osdr_generator.py
================================================================================
NASA OSDR Dashboard JSON Generator (Real-time API)
================================================================================

Downloading current filter-options from OSDR...
  URL: https://osdr.nasa.gov/geode-py/ws/repo/filter-options
  ✓ Successfully downloaded current filter-options

Fetching data from OSDR API...
  Fetching Assay Technology Types...
    URL: https://visualization.osdr.nasa.gov/biodata/api/v2/query/assays/?investigation.study%20assays.study%20assay%20technology%20type=//&format=json.split
    ✓ Received 3 columns, 763 rows
  Fetching Factors...
    ✓ Received 134 columns, 4 rows
  Fetching Organisms...
    ✓ Received 4 columns, 931 rows
  Fetching Material Types...
    ✓ Received 4 columns, 882 rows
  Fetching Missions...
    ✓ Received 4 columns, 763 rows

Extracting existing structure from current JSON...
  Project Type: 8 values in 3 categories
  Assay technology type: 48 values in 29 categories
  Factor: 126 values in 108 categories
  Organism: 170 values in 169 categories
  Material type: 146 values in 132 categories

Processing API data to find additions...
  Checking assay types...
  Checking factors...
  Checking organisms...
  Checking material types...
  Processing missions (new grouping)...

================================================================================
VERIFICATION: Checking completeness
================================================================================

Original values: 492
New values (excl. Mission): 708
Values added from API: 261
Missing from new: 0

✅ SUCCESS: All original values preserved!
✅ PLUS: 261 new values added from API

📊 NEW MISSION GROUPING: 147 missions in 10 categories
📊 TOTAL OSD IDs COVERED: 577

================================================================================
Saving outputs
================================================================================

✓ New JSON: /current/directory/filter-options-new.json
✓ Additions report: /current/directory/additions-report.txt
✓ Unmapped report: /current/directory/unmapped-report.txt

================================================================================
✅ COMPLETE: All original values preserved + new values added
================================================================================
```

## Mission Categories

The script creates these 10 mission categories:

| Category | Criteria |
|----------|----------|
| **ISS Expeditions** | Contains "expedition", "increment", or "iss" |
| **Space Shuttle** | Contains "sts-", "shuttle", or "sls-" |
| **Rodent Research** | Starts with "RR-" or contains "rodent research" |
| **Bion/Cosmos** | Contains "bion" or "cosmos" |
| **Payload Investigations** | Contains "bric-", "apex-", "veg-", "ffl", "cbtm", "cerise" |
| **Ground Control** | Contains "ground", "bsl", or "baseline" |
| **Radiation Studies** | Contains radiation-related terms |
| **Simulated Conditions** | Contains simulation-related terms |
| **Commercial Spaceflight** | Contains "inspiration4", "axiom", "ax-", "spacex" |
| **Other Missions** | Doesn't match any above criteria |

## Error Handling

### Download Error
```
✗ Failed to download filter-options: Connection timeout
```
**Solution:** Check internet connection. Ensure access to `osdr.nasa.gov`

### API Connection Error
```
✗ Failed to fetch Assay Technology Types: Connection timeout
```
**Solution:** Check internet connection. Ensure access to `visualization.osdr.nasa.gov`

### Verification Failure
```
❌ ERROR: 10 original values are MISSING from new JSON!
```
**Solution:** This indicates a bug - contact the developer

## Exit Codes

- **0**: Success - all original values preserved and new values added
- **1**: Error - download failed, API connection failed, missing values, etc.

## Network Requirements

Requires internet access to:
- `osdr.nasa.gov` (to download current filter-options)
- `visualization.osdr.nasa.gov` (OSDR Biological Data API)

If you're behind a firewall or proxy, ensure these domains are accessible.

## Automation & Scheduling

Since the script requires no input files, it's perfect for automation:

### Cron Job (Linux/Mac)
```bash
# Run daily at 2 AM
0 2 * * * cd /path/to/output/dir && python3 /path/to/osdr_generator.py
```

### Task Scheduler (Windows)
Create a scheduled task that runs:
```
python3 C:\path\to\osdr_generator.py
```

### GitHub Actions
```yaml
name: Update OSDR Filter Options
on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM
jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: pip install requests
      - name: Run generator
        run: python3 osdr_generator.py
      - name: Commit results
        run: |
          git config --local user.email "action@github.com"
          git config --local user.name "GitHub Action"
          git add filter-options-new.json additions-report.txt unmapped-report.txt
          git commit -m "Update filter options" || exit 0
          git push
```

## Notes

- **No setup required** - Just install `requests` and run
- **Outputs saved to current directory** - Change directory before running if needed
- **Idempotent** - Running multiple times produces same output (if OSDR data unchanged)
- **API calls take 30-60 seconds** depending on network speed
- **Category names preserved** from original OSDR filter-options
- **Always uses latest data** from OSDR

## Troubleshooting

**Connection timeout?**  
OSDR servers may be temporarily down. Wait and retry.

**Failed to download/fetch errors?**  
Check internet connection and ensure you can access `https://osdr.nasa.gov` and `https://visualization.osdr.nasa.gov` in a web browser.

**Outputs in wrong location?**  
Outputs are always in your current working directory (`pwd`). Change directory before running:
```bash
cd /desired/output/directory
python3 /path/to/osdr_generator.py
```

## Advantages

✅ **Zero setup** - No files to download or manage  
✅ **Always current** - Gets latest data directly from OSDR  
✅ **Simple workflow** - Just run the script  
✅ **Perfect for automation** - No manual steps required  
✅ **Self-contained** - Everything fetched automatically  

## Version

**Version:** 3.0 (Standalone with Auto-download)  
**Last Updated:** January 2026  
**API Documentation:** https://visualization.osdr.nasa.gov/biodata/api/  
**Filter Options:** https://osdr.nasa.gov/geode-py/ws/repo/filter-options
