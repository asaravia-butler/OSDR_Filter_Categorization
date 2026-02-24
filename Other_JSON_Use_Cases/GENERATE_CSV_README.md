# OSDR Measurement Technology CSV Generator

Generate a complete OSDR Measurement Technology Types CSV file directly from a filter-options JSON file.

## Overview

This script automates the entire process of creating a Measurement-Technology CSV:

1. **Reads** a filter-options JSON file (e.g., `filter-options-new-manual_20260205.json`)
2. **Extracts** all measurement and technology type combinations from the "Assay technology type" section
3. **Generates** properly formatted API calls for each combination
4. **Makes API calls** to retrieve Dataset_n and Sample_n counts
5. **Outputs** a complete CSV file with all columns populated

## Requirements

- Python 3.7+
- `requests` library

### Installing Requirements

```bash
pip install requests
```

Or if you have permission issues:

```bash
pip install requests --user
```

## Usage

### Basic Usage

```bash
python3 generate_measurement_tech_csv.py <input.json> <output.csv>
```

### Examples

**Example 1: Standard usage**
```bash
python3 generate_measurement_tech_csv.py filter-options-new-manual_20260205.json OSDR_Measurement_Technology_Types.csv
```

**Example 2: With full paths**
```bash
python3 generate_measurement_tech_csv.py /path/to/filter-options.json /path/to/output.csv
```

**Example 3: Current directory**
```bash
python3 generate_measurement_tech_csv.py my-filter-options.json results.csv
```

### Get Help

```bash
python3 generate_measurement_tech_csv.py --help
```

## Command-Line Arguments

### Required Arguments

1. **`input.json`** - Path to filter-options JSON file
   - Must contain "Assay technology type" section
   - Format: Same as filter-options files from OSDR

2. **`output.csv`** - Path to output CSV file
   - Will be created or overwritten
   - Format: CSV with 6 columns

## What It Does

### Step 1: Extract Measurement-Technology Pairs

The script reads the JSON file and extracts all measurement-technology combinations from the "Assay technology type" section.

**JSON Structure Expected:**
```json
{
  "Assay technology type": {
    "transcription profiling": ["transcription profiling"],
    "transcription profiling|RNA Sequencing (RNA-Seq)": ["RNA Sequencing (RNA-Seq)"],
    "transcription profiling|RNA Sequencing (RNA-Seq)|Illumina": ["Illumina"]
  }
}
```

The script identifies level-2 categories (measurement|technology) and extracts:
- Measurement type: "transcription profiling"
- Technology type: "RNA Sequencing (RNA-Seq)"

### Step 2: Handle Case Variations

If the JSON contains multiple capitalizations of the same measurement-technology pair (e.g., "DNA Microarray" and "DNA microarray"), the script:
- Groups them together (case-insensitive)
- Uses the **alphabetically-first** capitalization in the output
- Creates only **one** API call and CSV row per unique pair

### Step 3: Generate API Calls

For each measurement-technology pair, the script generates two API URLs:

**Dataset API:**
```
https://visualization.osdr.nasa.gov/biodata/api/v2/query/assays/?investigation.study%20assays.study%20assay%20measurement%20type=<MEASUREMENT>&investigation.study%20assays.study%20assay%20technology%20type=<TECHNOLOGY>&format=browser
```

**Sample API:**
```
https://visualization.osdr.nasa.gov/biodata/api/v2/query/assays/?investigation.study%20assays.study%20assay%20measurement%20type=<MEASUREMENT>&investigation.study%20assays.study%20assay%20technology%20type=<TECHNOLOGY>&id.sample%20name&format=browser
```

### Step 4: Make API Calls

For each pair:
1. Calls Dataset API and counts returned rows → Dataset_n
2. Waits 0.5 seconds (rate limiting)
3. Calls Sample API and counts returned rows → Sample_n
4. Waits 0.5 seconds (rate limiting)

### Step 5: Generate CSV

Creates a CSV file with all columns populated:

| Measurement_Type | Technology_Type | Dataset_n | Sample_n | Dataset_API_call | Sample_API_call |
|-----------------|-----------------|-----------|----------|------------------|-----------------|
| Amplicon Sequencing | 16S | 26 | 2393 | https://... | https://... |
| transcription profiling | RNA Sequencing (RNA-Seq) | 145 | 18234 | https://... | https://... |

## Expected Runtime

- **Number of API calls**: 2 × (number of measurement-technology pairs)
- **Rate limiting**: 0.5 seconds between calls
- **Typical JSON**: ~96 pairs = 192 API calls
- **Estimated time**: 5-10 minutes

## Example Output

```
================================================================================
OSDR Measurement Technology Types - CSV Generation from JSON
================================================================================

Reading JSON file: filter-options-new-manual_20260205.json
✓ Found 96 unique measurement-technology combinations

Generating API calls and fetching data...
This will make 192 API calls and may take 5-10 minutes...

[1/96] Amplicon Sequencing | 16S
  Dataset API call...
    ✓ Dataset_n: 26
  Sample API call...
    ✓ Sample_n: 2393

[2/96] Amplicon Sequencing | 16S and ITS
  Dataset API call...
    ✓ Dataset_n: 2
  Sample API call...
    ✓ Sample_n: 63

...

================================================================================
Saving CSV...
✓ Saved to: OSDR_Measurement_Technology_Types.csv

================================================================================
SUMMARY
================================================================================
Total rows processed: 96

Dataset_n:
  Successful: 96
  Failed: 0

Sample_n:
  Successful: 96
  Failed: 0

✅ SUCCESS: All API calls completed successfully!
================================================================================
```

## Output CSV Format

The generated CSV contains exactly 6 columns:

1. **Measurement_Type** - The measurement type (e.g., "transcription profiling")
2. **Technology_Type** - The technology type (e.g., "RNA Sequencing (RNA-Seq)")
3. **Dataset_n** - Number of datasets (studies) for this combination
4. **Sample_n** - Number of samples for this combination
5. **Dataset_API_call** - Full API URL to get datasets
6. **Sample_API_call** - Full API URL to get samples

**Sorting:**
- Rows are sorted alphabetically (case-insensitive) by:
  1. Measurement_Type
  2. Technology_Type

## Error Handling

### JSON File Errors

**File not found:**
```
✗ Error: Input file not found: myfile.json
```
Solution: Check file path, use absolute path if needed

**Invalid JSON:**
```
✗ Error: Invalid JSON file: ...
```
Solution: Verify JSON is valid, check for syntax errors

**Missing section:**
```
✗ Error: 'Assay technology type' section not found in JSON
```
Solution: Ensure JSON has the "Assay technology type" section

### API Call Errors

**Timeout:**
```
✗ Timeout
```
- The n column will be left empty
- Script continues with next row

**HTTP Error:**
```
✗ HTTP 403
```
- The n column will be left empty
- Check network/firewall settings

**Network Error:**
```
✗ Error: HTTPSConnectionPool...
```
- Check internet connection
- Verify access to `visualization.osdr.nasa.gov`

### Partial Failures

If some API calls fail:
- Script continues and completes what it can
- Failed calls leave n columns empty
- Summary shows success/failure counts

## Troubleshooting

### Missing Required Arguments

```
✗ Error: Missing required arguments
```

**Solution**: Provide both JSON and CSV file paths:
```bash
python3 generate_measurement_tech_csv.py input.json output.csv
```

### Script Takes Too Long

Default 0.5s delay can be reduced (but may trigger rate limits).

**Edit line 281 in script:**
```python
# Original:
generate_csv(json_file, output_file, delay=0.5)

# Faster (may trigger rate limits):
generate_csv(json_file, output_file, delay=0.1)

# Slower (more conservative):
generate_csv(json_file, output_file, delay=1.0)
```

### Connection Errors

```
✗ Error: HTTPSConnectionPool...
```

**Solution:**
- Check internet connection
- Ensure `visualization.osdr.nasa.gov` is accessible
- Check firewall/proxy settings
- Try from different network

## Network Requirements

Requires internet access to:
- `visualization.osdr.nasa.gov` (OSDR Biological Data API)

If behind a firewall or proxy, ensure this domain is accessible.

## Advantages

✅ **Fully automated** - One command does everything  
✅ **No manual CSV creation** - Generates from source JSON  
✅ **Accurate** - Extracts directly from authoritative JSON  
✅ **Complete** - Populates all columns including n values  
✅ **Sorted** - Output is properly sorted alphabetically  
✅ **Handles variations** - Merges case differences automatically  
✅ **Error resilient** - Continues on partial failures  


## Exit Codes

- **0**: Success - CSV generated successfully
- **1**: Error - Missing arguments, file not found, invalid JSON, or critical error

## Notes

- Script automatically handles case variations in the JSON
- Empty n columns indicate failed API calls
- Progress shown in real-time
- Safe to run multiple times (overwrites output)
- Preserves exact measurement/technology names from JSON
- Uses first alphabetical variation when multiple cases exist

