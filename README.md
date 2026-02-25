# OSDR Filter Categories JSON Generator

A Python script that regenerates the OSDR (Open Science Data Repository) filter-options JSON file by fetching all data in real-time from the OSDR API. **No input files required!**

<br>

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Requirements](#requirements)
  - [Installing Requirements](#installing-requirements)
- [Usage](#usage)
  - [Download the Python Script](#download-the-python-script)
  - [Run the Script](#run-the-script)
  - [What Happens](#what-happens)
- [Output Files](#output-files)
- [What the Script Does](#what-the-script-does)
- [Smart Categorization Features](#smart-categorization-features)
  - [Assay Technology Type (3-Level Hierarchy)](#assay-technology-type-3-level-hierarchy)
  - [Factor (Hierarchical Structure)](#factor-hierarchical-structure)
  - [Material Type (3-Tier Muscle Hierarchy)](#material-type-3-tier-muscle-hierarchy)
  - [Organism (Taxonomic Classification)](#organism-taxonomic-classification)
  - [Mission (10 Categories)](#mission-10-categories)
- [Data Sources](#data-sources)
  - [Current Filter Options](#current-filter-options)
  - [API Endpoints (JSON Split Format)](#api-endpoints-json-split-format)
- [Example Output](#example-output)
- [Input Format Support](#input-format-support)
- [Capitalization Handling](#capitalization-handling)
- [Error Handling](#error-handling)
- [Exit Codes](#exit-codes)
- [Network Requirements](#network-requirements)
- [Automation & Scheduling](#automation--scheduling)
- [Notes](#notes)
- [Troubleshooting](#troubleshooting)
- [Advantages](#advantages)
- [Version](#version)

<br>

## Overview

This script:
- ✅ **Fully automated** - Downloads current filter-options from OSDR or uses your custom file
- ✅ **Flexible input** - Use live OSDR data (default) or specify a local JSON file
- ✅ **No input files required** - Works standalone by downloading from OSDR
- ✅ Preserves **ALL** existing values from the input filter-options
- ✅ Adds new metadata values discovered from the API
- ✅ **Smart categorization** with taxonomic classification and anatomical matching
- ✅ **3-level Assay hierarchy** (Measurement → Technology → Platform)
- ✅ **Hierarchical Factor structure** (Parent → Parent|Child)
- ✅ **3-tier muscle hierarchy** for Material types (muscle → muscle|name → muscle|name|laterality)
- ✅ **Capitalization normalization** at all levels
- ✅ Creates a new **Mission** grouping with 10 categories
- ✅ Handles misspellings and capitalization differences
- ✅ Generates verification and tracking reports
- ✅ Validates that no original data is lost

<br>

## Key Features

### 🎯 Smart Categorization
- **Taxonomic classification** for organisms (bacteria, plants, fungi, wasps)
- **Comprehensive anatomical matching** for material types with 95+ keywords
- **Organ systems**: liver, kidney, spleen, lung, heart, thymus, reproductive organs
- **Skeletal system**: femur, tibia, vertebrae, calvariae, bone marrow
- **Digestive system**: intestine, colon, stomach, esophagus
- **Body fluids**: plasma, serum, saliva, urine, feces
- **Plant tissues**: root, shoot, leaf, cotyledon, hypocotyl, seed
- **3-level Assay hierarchy** with proper measurement → technology → platform structure
- **Hierarchical Factors** with parent|child relationships including "altered gravity"
- **3-tier muscle categorization** with laterality support (left/right)

### 🔄 Dual Format Support
- Automatically detects **OLD format** (nested 'study' array) or **NEW format** (flat sections)
- Works seamlessly with both live API downloads and manually curated files

### 📊 Capitalization Normalization
- Handles case variations automatically (e.g., "DNA microarray" + "DNA Microarray" → single category)
- Applied at ALL levels for ALL sections
- Preserves all capitalization variants as values

### ✨ Production Ready
- **1,462 total values** properly categorized
- **372 Assay categories** with 3-level hierarchy
- **198 Material categories** with comprehensive anatomical matching
- **95+ anatomical keywords** for organ systems, bones, fluids, and plant tissues
- **190 Organism categories** with taxonomic classification
- **153 Factor categories** with parent|child structure + "altered gravity" handling
- **10 Mission categories** with pattern-based grouping
- **38 cell type keywords** for automatic cell categorization

<br>

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

<br>

## Usage

### Download the Python Script

```bash
curl -LO https://raw.githubusercontent.com/asaravia-butler/OSDR_Filter_Categorization/refs/heads/main/osdr_filter_options_generator.py
```

### Run the Script

**Default (downloads from OSDR):**
```bash
python3 osdr_filter_options_generator.py
```

**With custom input file:**
```bash
python3 osdr_filter_options_generator.py your-filter-options.json
```

**Get help:**
```bash
python3 osdr_filter_options_generator.py --help
```

### Command-Line Arguments

- **No arguments**: Downloads filter-options from `https://osdr.nasa.gov/geode-py/ws/repo/filter-options`
- **One argument**: Uses the specified JSON file as input
  - Example: `python3 osdr_filter_options_generator.py filter-options-custom.json`

This allows you to use either:
1. The live OSDR filter-options (default)
2. A manually curated or previous version of the JSON file

### What Happens

The script automatically:
1. **Loads input data**:
   - If no arguments: Downloads current filter-options from `https://osdr.nasa.gov/geode-py/ws/repo/filter-options`
   - If JSON file provided: Reads from the specified file
2. Detects input format (OLD nested or NEW flat)
3. Fetches latest metadata from 5 OSDR API endpoints
4. Applies smart categorization with normalization
5. Generates output files in your current directory

<br>

## Output Files

After running, three files are created in your **current working directory**:

1. **filter-options-new.json** - Complete regenerated JSON with preserved + new values
2. **additions-report.txt** - List of all new values added from API
3. **unmapped-report.txt** - Items that need manual categorization

Example output files are available in the [Example_Outputs](Example_Outputs) directory.

<br>

## What the Script Does

1. **Downloads** current filter-options.json from OSDR (or uses provided file)
2. **Detects format** (OLD nested or NEW flat structure)
3. **Makes 5 API calls** to fetch latest metadata:
   - Assay Measurement/Technology/Platform (3-level hierarchy)
   - Factors (with parent|child hierarchy)
   - Organisms (with taxonomic classification)
   - Material Types (with 3-tier muscle hierarchy)
   - Missions (with 10 categories)
4. **Applies smart categorization**:
   - Taxonomic classification (bacteria|species, plant|species, etc.)
   - Anatomical matching (brain|hippocampus, muscle|gastrocnemius, etc.)
   - Laterality handling (muscle|gastrocnemius|left gastrocnemius)
   - Capitalization normalization
5. **Preserves ALL** existing values
6. **Adds new** values found in API
7. **Verifies** no data loss
8. **Generates** comprehensive reports

<br>

## Smart Categorization Features

### Assay Technology Type (3-Level Hierarchy)

The script creates a proper 3-level hierarchy with capitalization normalization:

```json
{
  "transcription profiling": [
    "transcription profiling",
    "Transcription Profiling"
  ],
  "transcription profiling|RNA Sequencing (RNA-Seq)": [
    "RNA Sequencing (RNA-Seq)"
  ],
  "transcription profiling|RNA Sequencing (RNA-Seq)|Illumina": [
    "Illumina"
  ],
  "transcription profiling|RNA Sequencing (RNA-Seq)|Illumina HiSeq 4000": [
    "Illumina HiSeq 4000"
  ]
}
```

**Features:**
- Level 1: Measurement type (e.g., "transcription profiling")
- Level 2: Technology type (e.g., "RNA Sequencing (RNA-Seq)")
- Level 3: Platform (e.g., "Illumina HiSeq 4000")
- All capitalization variants preserved within categories

### Factor (Hierarchical Structure)

Creates parent|child relationships for related factors:

```json
{
  "age": ["age"],
  "age|age at sample collection": ["age at sample collection"],
  "age|donor age": ["donor age"],
  "time": ["time"],
  "time|dissection timeline": ["dissection timeline"],
  "time|sample storage time": ["sample storage time"]
}
```

**Hierarchical groupings:**
- `age` → age at sample collection, age at start of experiment, donor age
- `altered gravity` → altered gravity duration, altered gravity simulator, and any factor containing "altered gravity"
- `duration` → exposure duration, hindlimb unloading duration, treatment duration
- `ionizing radiation` → absorbed radiation dose, particle charge, radiation distance
- `time` → dissection timeline, sample storage time, collection times
- And 5 more parent categories

**Special handling:**
- Any factor containing "altered gravity" automatically creates a sub-category under the "altered gravity" parent
- Example: New factor "altered gravity experiment X" → `altered gravity|altered gravity experiment X`

### Material Type (3-Tier Muscle Hierarchy)

Special handling for muscles with laterality:

```json
{
  "muscle|gastrocnemius": [
    "Gastrocnemius",
    "gastrocnemius"
  ],
  "muscle|gastrocnemius|left gastrocnemius": [
    "Left gastrocnemius"
  ],
  "muscle|gastrocnemius|right gastrocnemius": [
    "Right gastrocnemius"
  ]
}
```

**Features:**
- Tier 1: `muscle` (parent)
- Tier 2: `muscle|gastrocnemius` (specific muscle)
- Tier 3: `muscle|gastrocnemius|left gastrocnemius` (lateralized)
- Supports: gastrocnemius, soleus, tibialis anterior, quadriceps, and more
- Preserves tibia vs tibialis anterior distinction

**Cell type categorization:**

Automatic categorization for cells using 38 keywords:

```json
{
  "cells|T cells": [
    "T cells",
    "Primary T Cells"
  ],
  "blood|peripheral blood mononuclear cell": [
    "Peripheral Blood Mononuclear Cell",
    "PBMC"
  ],
  "cells|3D cells": [
    "3D Cells",
    "3D cell culture"
  ],
  "cells|cardiomyocytes": [
    "human induced pluripotent stem cell-derived cardiomyocytes"
  ]
}
```

**Cell categories covered:**
- ✅ General cells: T cells, myoblasts, microglia, primary cells, skeletal stem cells
- ✅ Blood cells: RBCs, PBMCs, peripheral blood, blood cells
- ✅ Epithelial cells: Bronchial epithelial, mammary epithelial
- ✅ Cardiac cells: Cardiomyocytes, cardiovascular progenitor cells
- ✅ Fibroblasts: Lung fibroblasts, lymphoblastoid cells
- ✅ Cell cultures: 3D cells, HARV culture, OPM chamber culture
- ✅ Cell lines: Human Fibroblasts AG01522
- ✅ Abbreviations: PBMC, RBC automatically recognized

**Comprehensive anatomical keyword matching:**
- **Brain regions**: hippocampus, cerebellum, cortex, forebrain, subdural space
- **Muscles**: gastrocnemius, soleus, tibialis anterior, quadriceps (with laterality)
- **Major organs**: liver, kidney, spleen, lung, heart, thymus, pancreas, thyroid, pituitary
- **Reproductive organs**: testis, ovary, uterus, prostate, mammary gland
- **Digestive system**: intestine, colon, stomach, esophagus, duodenum, jejunum, ileum
- **Skeletal system**: femur, tibia, humerus, vertebrae, calvariae, skull, bone marrow
- **Body fluids**: plasma, serum, saliva, urine, feces
- **Adipose tissue**: brown, white, gonadal, mesenteric, subcutaneous adipose tissue
- **Skin**: epidermis, dermis, hair follicle
- **Eye**: retina, lens, cornea (with laterality)
- **Plant tissues**: root, shoot, leaf, cotyledon, hypocotyl, seed, callus
- **Microbiology**: biofilms, bioaerosol, swabs
- **Cell types**: T cells, myoblasts, fibroblasts, cardiomyocytes, etc.
- **Cell cultures**: 3D cells, HARV culture, cell lines
- Handles laterality patterns (left, right, both)
- Case-insensitive throughout
- **95+ total anatomical keywords**

**Material categorization logic (order of operations):**
1. **Exact match** - Case-insensitive match to existing values
2. **Laterality patterns** - Detects "left/right/both" + tissue name
3. **Anatomical keyword matching** - Checks 95+ keywords for organs, tissues, cells
4. **Substring matching** - Falls back to partial string matches
5. **Other Materials** - Uncategorized items go here

This order ensures specific keyword mappings (like "gonadal adipose tissue" → "adipose tissue|gonadal adipose tissue") are applied before generic substring matches.

### Organism (Taxonomic Classification)

Automatically classifies organisms by taxonomy:

```json
{
  "bacteria|Escherichia coli": ["Escherichia coli"],
  "bacteria|Klebsiella pneumoniae": ["Klebsiella pneumoniae"],
  "plant|Arabidopsis thaliana": ["Arabidopsis thaliana"],
  "plant|Lactuca sativa": ["Lactuca sativa"],
  "fungus|Saccharomyces cerevisiae": ["Saccharomyces cerevisiae"],
  "wasp|Leptopilina boulardi": ["Leptopilina boulardi"]
}
```

**Taxonomic databases:**
- **Bacteria**: 15+ genera (Escherichia, Klebsiella, Pseudomonas, Bacillus, etc.)
- **Plants**: 14 genera (Arabidopsis, Brassica, Triticum, Zea, etc.)
- **Fungi**: 6 genera (Aspergillus, Candida, Saccharomyces, etc.)
- **Wasps**: 2 genera (Leptopilina, Nasonia)

### Mission (10 Categories)

Pattern-based categorization of missions:

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

<br>

## Data Sources

### Current Filter Options
- **URL:** `https://osdr.nasa.gov/geode-py/ws/repo/filter-options`
- Downloaded automatically at runtime
- **Supports both formats:**
  - OLD: Nested 'study' array (from live API)
  - NEW: Flat sections (from manually curated files)

### API Endpoints (JSON Split Format)

1. **Assay Measurement/Technology/Platform**  
   `https://visualization.osdr.nasa.gov/biodata/api/v2/query/assays/?investigation.study%20assays.study%20assay%20measurement%20type&investigation.study%20assays.study%20assay%20technology%20type&investigation.study%20assays.study%20assay%20technology%20platform&format=json.split`

2. **Factors**  
   `https://visualization.osdr.nasa.gov/biodata/api/v2/query/assays/?investigation.study%20assays.study%20assay%20technology%20type&assay.factor%20value&study.factor%20value&schema&format=json.split`

3. **Organisms**  
   `https://visualization.osdr.nasa.gov/biodata/api/v2/query/assays/?investigation.study%20assays.study%20assay%20technology%20type&study.characteristics.organism&format=json.split`

4. **Material Types**  
   `https://visualization.osdr.nasa.gov/biodata/api/v2/query/assays/?investigation.study%20assays.study%20assay%20technology%20type&study.characteristics.material%20type&format=json.split`

5. **Missions**  
   `https://visualization.osdr.nasa.gov/biodata/api/v2/query/assays/?investigation.study%20assays.study%20assay%20technology%20type&investigation.study.comment.Project%20Identifier&format=json.split`

<br>

## Example Output

```bash
$ python3 osdr_filter_options_generator.py
================================================================================
NASA OSDR Filter Options Generator - Final Version
================================================================================

Downloading current filter-options...
  ✓ Downloaded successfully

Fetching API data...
  Fetching Assay Measurement/Technology/Platform...
    ✓ 5 columns, 791 rows
  Fetching Factors...
    ✓ 137 columns, 4 rows
  Fetching Organisms...
    ✓ 4 columns, 959 rows
  Fetching Material Types...
    ✓ 4 columns, 913 rows
  Fetching Missions...
    ✓ 4 columns, 791 rows

Extracting existing structure...
  Detected NEW format (flat sections)
  Project Type: 8 values in 3 categories
  Assay technology type: 382 values in 372 categories
  Factor: 171 values in 153 categories
  Organism: 348 values in 190 categories
  Material type: 404 values in 198 categories

Processing API data...
  Processing assays (measurement -> technology -> platform)...
  Processing factors...
  Processing organisms...
  Processing materials...
  Processing missions...

================================================================================
VERIFICATION
================================================================================

Original values (excl. Assay): 987
New values (excl. Assay & Mission): 987
Values added: 0
Missing: 0

✅ SUCCESS: All preserved + 0 added
📊 ASSAY: 382 values in 372 categories
📊 Missions: 149 in 10 categories
📊 OSD IDs: 598

================================================================================
Saving outputs
================================================================================

✓ JSON: /current/directory/filter-options-new.json
✓ Additions: /current/directory/additions-report.txt
✓ Unmapped: /current/directory/unmapped-report.txt

================================================================================
✅ COMPLETE
================================================================================
```

<br>

## Input Format Support

The script automatically detects and handles both formats:

### OLD Format (Nested 'study' array)
```json
{
  "general": {...},
  "study": [
    {
      "displayValue": "Assay Type",
      "children": [...]
    }
  ]
}
```

### NEW Format (Flat sections)
```json
{
  "Assay technology type": {
    "transcription profiling": ["transcription profiling"]
  },
  "Material type": {
    "muscle|gastrocnemius": ["gastrocnemius"]
  }
}
```

**Detection is automatic** - no flags or configuration needed!

<br>

## Capitalization Handling

The script normalizes capitalization at ALL levels for ALL sections:

### How It Works
1. **First occurrence wins** - First capitalization seen becomes the canonical form
2. **Category names** use canonical version
3. **All variants preserved** as values within the category

### Example
```json
{
  "transcription profiling": [
    "transcription profiling",
    "Transcription Profiling"
  ],
  "transcription profiling|DNA microarray": [
    "DNA microarray",
    "DNA Microarray"
  ]
}
```

**Benefits:**
- No duplicate categories due to capitalization
- All data variants preserved
- Consistent category naming

<br>

## Error Handling

### Download Error
```
✗ Failed: Connection timeout
```
**Solution:** Check internet connection. Ensure access to `osdr.nasa.gov`

### API Connection Error
```
✗ Failed to fetch: Connection timeout
```
**Solution:** Check internet connection. Ensure access to `visualization.osdr.nasa.gov`

### Verification Failure
```
❌ ERROR: 10 values missing!
```
**Solution:** This indicates a bug - please report the issue

<br>

## Exit Codes

- **0**: Success - all original values preserved
- **1**: Error - download failed, API connection failed, or verification failed

<br>

## Network Requirements

Requires internet access to:
- `osdr.nasa.gov` (to download current filter-options)
- `visualization.osdr.nasa.gov` (OSDR Biological Data API)

If you're behind a firewall or proxy, ensure these domains are accessible.

<br>

## Automation & Scheduling

Since the script requires no input files, it's perfect for automation:

### Cron Job (Linux/Mac)
```bash
# Run daily at 2 AM
0 2 * * * cd /path/to/output/dir && python3 /path/to/osdr_filter_options_generator.py
```

### Task Scheduler (Windows)
Create a scheduled task that runs:
```
python3 C:\path\to\osdr_filter_options_generator.py
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
        run: python3 osdr_filter_options_generator.py
      - name: Commit results
        run: |
          git config --local user.email "action@github.com"
          git config --local user.name "GitHub Action"
          git add filter-options-new.json additions-report.txt unmapped-report.txt
          git commit -m "Update filter options" || exit 0
          git push
```

<br>

## Notes

- **No setup required** - Just install `requests` and run
- **Outputs saved to current directory** - Change directory before running if needed
- **Idempotent** - Running multiple times produces same output (if OSDR data unchanged)
- **API calls take 30-60 seconds** depending on network speed
- **Dual format support** - Works with both OLD and NEW input formats
- **Smart categorization** - Automatic taxonomic classification and anatomical matching
- **Capitalization normalized** - No duplicate categories from case differences
- **Always uses latest data** from OSDR

<br>

## Troubleshooting

**Connection timeout?**  
OSDR servers may be temporarily down. Wait and retry.

**Failed to download/fetch errors?**  
Check internet connection and ensure you can access `https://osdr.nasa.gov` and `https://visualization.osdr.nasa.gov` in a web browser.

**Outputs in wrong location?**  
Outputs are always in your current working directory (`pwd`). Change directory before running:
```bash
cd /desired/output/directory
python3 /path/to/osdr_filter_options_generator.py
```

**Values going to "Other" categories?**  
Check the `unmapped-report.txt` file to see which values need manual categorization. These are items that the smart categorization couldn't classify automatically.

<br>

## Advantages

✅ **Zero setup** - No files to download or manage  
✅ **Always current** - Gets latest data directly from OSDR  
✅ **Smart categorization** - Automatic taxonomic and anatomical matching  
✅ **Cell type recognition** - 38 keywords for cells, blood cells, and cell cultures  
✅ **Dual format support** - Works with OLD and NEW formats seamlessly  
✅ **Capitalization normalized** - Handles case variations automatically  
✅ **3-level Assay hierarchy** - Proper measurement → technology → platform structure  
✅ **Hierarchical Factors** - Parent|child relationships preserved  
✅ **3-tier muscle hierarchy** - Proper laterality support  
✅ **Simple workflow** - Just run the script  
✅ **Perfect for automation** - No manual steps required  
✅ **Self-contained** - Everything fetched automatically  
✅ **Production ready** - 1,462 values properly categorized  

<br>

## Version

**Version:** 2.1  
**Last Updated:** February 2026  
**API Documentation:** https://visualization.osdr.nasa.gov/biodata/api/  
**Filter Options:** https://osdr.nasa.gov/geode-py/ws/repo/filter-options

### Version 2.1 Features (February 2026)
- ✅ **95+ anatomical keywords** for comprehensive organ system categorization
- ✅ **Major organs**: liver, kidney, spleen, lung, heart, thymus, reproductive organs
- ✅ **Skeletal system**: femur, tibia, vertebrae, calvariae, bone marrow  
- ✅ **Digestive system**: intestine, colon, stomach, esophagus
- ✅ **Body fluids**: plasma, serum, saliva, urine, feces
- ✅ **Plant tissues**: root, shoot, leaf, cotyledon, hypocotyl, seed
- ✅ **"Altered gravity" factor handling**: Auto-categorizes all variants
- ✅ Significantly reduced "Other Materials" category

### Version 2.0 Features
- ✅ 3-level Assay hierarchy (Measurement → Technology → Platform)
- ✅ Hierarchical Factor structure (Parent → Parent|Child)
- ✅ 3-tier muscle hierarchy with laterality support
- ✅ Taxonomic organism classification
- ✅ Dual input format support (OLD nested + NEW flat)
- ✅ Capitalization normalization at all levels
- ✅ Smart anatomical matching for materials
- ✅ **38 cell type keywords** for automatic cell categorization
- ✅ **Blood cell recognition** (RBCs, PBMCs, peripheral blood)
- ✅ **Cell line and culture identification** (3D cells, HARV, cell lines)
- ✅ 1,462 total values properly categorized
