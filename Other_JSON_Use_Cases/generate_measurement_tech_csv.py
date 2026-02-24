#!/usr/bin/env python3
"""
Generate OSDR Measurement Technology Types CSV from JSON file

This script:
1. Reads a filter-options JSON file (like filter-options-new-manual_20260205.json)
2. Extracts all measurement and technology type combinations
3. Generates API calls for each combination
4. Makes API calls to get Dataset_n and Sample_n counts
5. Saves complete CSV with all columns populated

Usage:
    python3 generate_measurement_tech_csv.py <input.json> <output.csv>

Arguments:
    input.json    : Required. Path to filter-options JSON file
    output.csv    : Required. Path to output CSV file

Examples:
    python3 generate_measurement_tech_csv.py filter-options-new-manual_20260205.json results.csv
    python3 generate_measurement_tech_csv.py /path/to/input.json /path/to/output.csv

Requirements:
    pip install requests
"""

import json
import csv
import requests
import time
import sys
import os
import urllib.parse
from collections import defaultdict
from typing import Dict, List, Tuple


def normalize(s: str) -> str:
    """Normalize string for comparison (lowercase, stripped)"""
    return s.strip().lower() if s else ""


def extract_measurement_technology_pairs(json_file: str) -> List[Tuple[str, str]]:
    """
    Extract all measurement-technology pairs from the JSON file.
    
    Args:
        json_file: Path to the filter-options JSON file
        
    Returns:
        List of (measurement, technology) tuples, sorted alphabetically
    """
    print(f"\nReading JSON file: {json_file}")
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"✗ Error: File not found: {json_file}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"✗ Error: Invalid JSON file: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Error reading file: {e}")
        sys.exit(1)
    
    # Get Assay technology type section
    assay_data = data.get('Assay technology type', {})
    
    if not assay_data:
        print("✗ Error: 'Assay technology type' section not found in JSON")
        sys.exit(1)
    
    # Extract measurement|technology pairs (level 2 categories)
    # Group by case-insensitive measurement|technology to handle variations
    grouped = defaultdict(lambda: {'measurements': set(), 'technologies': set()})
    
    for category, values in assay_data.items():
        if '|' not in category:
            continue  # Skip level 1 (measurement only)
        
        parts = category.split('|')
        
        if len(parts) == 2:
            # This is measurement|technology (level 2)
            measurement_cat = parts[0]
            technology_cat = parts[1]
            
            # Group by normalized key
            key = f"{normalize(measurement_cat)}|{normalize(technology_cat)}"
            grouped[key]['measurements'].add(measurement_cat)
            grouped[key]['technologies'].add(technology_cat)
    
    print(f"✓ Found {len(grouped)} unique measurement-technology combinations")
    
    # Create list of pairs using alphabetically-first variation
    pairs = []
    for key, variants in grouped.items():
        measurements = sorted(list(variants['measurements']))
        technologies = sorted(list(variants['technologies']))
        
        measurement = measurements[0]  # Use first alphabetically
        technology = technologies[0]    # Use first alphabetically
        
        pairs.append((measurement, technology))
    
    # Sort pairs alphabetically (case-insensitive) by measurement, then technology
    pairs.sort(key=lambda x: (normalize(x[0]), normalize(x[1])))
    
    return pairs


def generate_api_url(measurement: str, technology: str, api_type: str) -> str:
    """
    Generate API URL for a measurement-technology pair.
    
    Args:
        measurement: Measurement type
        technology: Technology type
        api_type: 'dataset' or 'sample'
        
    Returns:
        Full API URL
    """
    base_url = "https://visualization.osdr.nasa.gov/biodata/api/v2/query/assays/?"
    
    # URL encode parameters
    measurement_encoded = urllib.parse.quote(measurement)
    technology_encoded = urllib.parse.quote(technology)
    
    # Build query parameters
    params = f"investigation.study%20assays.study%20assay%20measurement%20type={measurement_encoded}"
    params += f"&investigation.study%20assays.study%20assay%20technology%20type={technology_encoded}"
    
    if api_type == 'sample':
        params += "&id.sample%20name"
    
    params += "&format=browser"
    
    return base_url + params


def count_csv_rows(api_url: str) -> int:
    """
    Make API call and count the number of data rows returned.
    
    Args:
        api_url: Full API URL with format=browser
        
    Returns:
        Number of data rows (excluding header), or -1 if error
    """
    # Convert browser format to csv format for easier parsing
    csv_url = api_url.replace('format=browser', 'format=csv')
    
    try:
        response = requests.get(csv_url, timeout=30)
        
        if response.status_code != 200:
            print(f"    ✗ HTTP {response.status_code}")
            return -1
        
        # Count lines, subtract 1 for header
        lines = response.text.strip().split('\n')
        row_count = len(lines) - 1 if len(lines) > 1 else 0
        
        return row_count
        
    except requests.exceptions.Timeout:
        print(f"    ✗ Timeout")
        return -1
    except requests.exceptions.RequestException as e:
        print(f"    ✗ Error: {str(e)[:50]}")
        return -1
    except Exception as e:
        print(f"    ✗ Unexpected error: {str(e)[:50]}")
        return -1


def generate_csv(json_file: str, output_file: str, delay: float = 0.5):
    """
    Generate complete CSV with all columns populated.
    
    Args:
        json_file: Path to input JSON file
        output_file: Path to output CSV file
        delay: Delay in seconds between API calls (for rate limiting)
    """
    print("="*80)
    print("OSDR Measurement Technology Types - CSV Generation from JSON")
    print("="*80)
    
    # Extract measurement-technology pairs
    pairs = extract_measurement_technology_pairs(json_file)
    
    print(f"\nGenerating API calls and fetching data...")
    print(f"This will make {len(pairs) * 2} API calls and may take 5-10 minutes...\n")
    
    # Create CSV rows
    csv_rows = []
    successful_dataset = 0
    successful_sample = 0
    failed_dataset = 0
    failed_sample = 0
    
    for i, (measurement, technology) in enumerate(pairs, 1):
        print(f"[{i}/{len(pairs)}] {measurement} | {technology}")
        
        # Generate API URLs
        dataset_api = generate_api_url(measurement, technology, 'dataset')
        sample_api = generate_api_url(measurement, technology, 'sample')
        
        row = {
            'Measurement_Type': measurement,
            'Technology_Type': technology,
            'Dataset_n': '',
            'Sample_n': '',
            'Dataset_API_call': dataset_api,
            'Sample_API_call': sample_api
        }
        
        # Get Dataset_n
        print(f"  Dataset API call...")
        dataset_n = count_csv_rows(dataset_api)
        
        if dataset_n >= 0:
            row['Dataset_n'] = str(dataset_n)
            print(f"    ✓ Dataset_n: {dataset_n}")
            successful_dataset += 1
        else:
            failed_dataset += 1
        
        time.sleep(delay)  # Rate limiting
        
        # Get Sample_n
        print(f"  Sample API call...")
        sample_n = count_csv_rows(sample_api)
        
        if sample_n >= 0:
            row['Sample_n'] = str(sample_n)
            print(f"    ✓ Sample_n: {sample_n}")
            successful_sample += 1
        else:
            failed_sample += 1
        
        time.sleep(delay)  # Rate limiting
        
        csv_rows.append(row)
        print()
    
    # Write CSV
    print("="*80)
    print("Saving CSV...")
    
    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['Measurement_Type', 'Technology_Type', 'Dataset_n', 'Sample_n',
                         'Dataset_API_call', 'Sample_API_call']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            writer.writeheader()
            writer.writerows(csv_rows)
        
        print(f"✓ Saved to: {output_file}")
        
    except Exception as e:
        print(f"✗ Error writing file: {e}")
        sys.exit(1)
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Total rows processed: {len(csv_rows)}")
    print(f"\nDataset_n:")
    print(f"  Successful: {successful_dataset}")
    print(f"  Failed: {failed_dataset}")
    print(f"\nSample_n:")
    print(f"  Successful: {successful_sample}")
    print(f"  Failed: {failed_sample}")
    
    if failed_dataset > 0 or failed_sample > 0:
        print(f"\n⚠ {failed_dataset + failed_sample} API calls failed")
        print(f"Empty cells in output indicate failed API calls")
    
    if successful_dataset == len(csv_rows) and successful_sample == len(csv_rows):
        print(f"\n✅ SUCCESS: All API calls completed successfully!")
    else:
        print(f"\n⚠ PARTIAL: Some API calls failed (see empty cells in output)")
    
    print("="*80)


def print_usage():
    """Print usage information"""
    print("Usage:")
    print("  python3 generate_measurement_tech_csv.py <input.json> <output.csv>")
    print()
    print("Arguments:")
    print("  input.json    Required. Path to filter-options JSON file")
    print("  output.csv    Required. Path to output CSV file")
    print()
    print("Examples:")
    print("  python3 generate_measurement_tech_csv.py filter-options-new-manual_20260205.json results.csv")
    print("  python3 generate_measurement_tech_csv.py /path/to/input.json /path/to/output.csv")
    print()
    print("Requirements:")
    print("  pip install requests")


def main():
    """Main function"""
    
    # Check for help first
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help', 'help']:
        print_usage()
        sys.exit(0)
    
    # Check command-line arguments
    if len(sys.argv) < 3:
        print("✗ Error: Missing required arguments")
        print()
        print_usage()
        sys.exit(1)
    
    # Get arguments
    json_file = sys.argv[1]
    output_file = sys.argv[2]
    
    # Check if JSON file exists
    if not os.path.exists(json_file):
        print(f"✗ Error: Input file not found: {json_file}")
        print()
        print("Please check the file path and try again.")
        sys.exit(1)
    
    # Generate CSV
    generate_csv(json_file, output_file, delay=0.5)


if __name__ == '__main__':
    main()
