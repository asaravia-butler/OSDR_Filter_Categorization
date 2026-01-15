#!/usr/bin/env python3
"""
NASA OSDR Dashboard JSON Generator (with Real-time API)
=======================================================
Regenerates filter-options.json from OSDR API data while preserving all existing values.

Usage:
    python3 osdr_generator.py

The script will:
1. Download the current filter-options JSON from OSDR
2. Make real-time API calls to OSDR to fetch latest data
3. Preserve ALL existing values
4. Add new values discovered from API
5. Create new Mission grouping
6. Generate verification reports
"""

import json
import sys
import os
import requests
from collections import defaultdict


class OSDRFilterGenerator:
    def __init__(self):
        """
        Initialize generator and download current filter-options from OSDR.
        """
        print("="*80)
        print("NASA OSDR Dashboard JSON Generator (Real-time API)")
        print("="*80)
        
        # API configuration
        self.base_url = "https://visualization.osdr.nasa.gov/biodata/api/v2"
        self.filter_options_url = "https://osdr.nasa.gov/geode-py/ws/repo/filter-options"
        self.session = requests.Session()
        
        # Download current filter-options JSON
        print(f"\nDownloading current filter-options from OSDR...")
        print(f"  URL: {self.filter_options_url}")
        self.current_json = self.download_current_json()
        
        # Fetch API data
        print("\nFetching data from OSDR API...")
        self.assay_data = self.fetch_assay_data()
        self.factor_data = self.fetch_factor_data()
        self.organism_data = self.fetch_organism_data()
        self.material_data = self.fetch_material_data()
        self.mission_data = self.fetch_mission_data()
        
        # Extract existing structure - PRESERVE EVERYTHING
        self.existing_structure = self.extract_existing_structure()
        
        # Build new JSON starting from existing
        self.new_json = self.initialize_from_existing()
        
        # Tracking
        self.additions = []
        self.unmapped = []
        self.all_osd_ids = set()
    
    def download_current_json(self):
        """Download current filter-options JSON from OSDR"""
        try:
            response = self.session.get(self.filter_options_url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            print(f"  ✓ Successfully downloaded current filter-options")
            return data
            
        except requests.exceptions.RequestException as e:
            print(f"  ✗ Failed to download filter-options: {e}")
            raise
        except json.JSONDecodeError as e:
            print(f"  ✗ Invalid JSON response: {e}")
            raise
    
    def fetch_api_data(self, endpoint, description):
        """
        Fetch data from OSDR API endpoint.
        
        Args:
            endpoint: API endpoint path (e.g., "?investigation.study...")
            description: Description for logging
            
        Returns:
            dict: JSON response with 'columns' and 'data' keys
        """
        url = f"{self.base_url}/query/assays/{endpoint}"
        print(f"  Fetching {description}...")
        print(f"    URL: {url}")
        
        try:
            response = self.session.get(url, timeout=60)
            response.raise_for_status()
            
            data = response.json()
            
            # Validate response format
            if not isinstance(data, dict) or 'columns' not in data or 'data' not in data:
                raise ValueError(f"Unexpected API response format for {description}")
            
            print(f"    ✓ Received {len(data['columns'])} columns, {len(data['data'])} rows")
            return data
            
        except requests.exceptions.RequestException as e:
            print(f"    ✗ Failed to fetch {description}: {e}")
            raise
        except json.JSONDecodeError as e:
            print(f"    ✗ Invalid JSON response for {description}: {e}")
            raise
    
    def fetch_assay_data(self):
        """Fetch assay technology type data from API"""
        return self.fetch_api_data(
            "?investigation.study%20assays.study%20assay%20technology%20type=//&format=json.split",
            "Assay Technology Types"
        )
    
    def fetch_factor_data(self):
        """Fetch factor data from API"""
        return self.fetch_api_data(
            "?investigation.study%20assays.study%20assay%20technology%20type&assay.factor%20value&study.factor%20value&schema&format=json.split",
            "Factors"
        )
    
    def fetch_organism_data(self):
        """Fetch organism data from API"""
        return self.fetch_api_data(
            "?investigation.study%20assays.study%20assay%20technology%20type=//&study.characteristics.organism=//&format=json.split",
            "Organisms"
        )
    
    def fetch_material_data(self):
        """Fetch material type data from API"""
        return self.fetch_api_data(
            "?investigation.study%20assays.study%20assay%20technology%20type=//&study.characteristics.material%20type=//&format=json.split",
            "Material Types"
        )
    
    def fetch_mission_data(self):
        """Fetch mission/project identifier data from API"""
        return self.fetch_api_data(
            "?investigation.study%20assays.study%20assay%20technology%20type=//&investigation.study.comment.Project%20Identifier=//&format=json.split",
            "Missions"
        )
    
    def norm(self, s):
        """Normalize string for comparison"""
        if not s or not isinstance(s, str):
            return ""
        return s.strip().lower()
    
    def extract_existing_structure(self):
        """Extract complete existing structure preserving everything"""
        print("\nExtracting existing structure from current JSON...")
        
        structure = {
            'Project Type': {},
            'Assay technology type': {},
            'Factor': {},
            'Organism': {},
            'Material type': {}
        }
        
        study_section = self.current_json.get('study', [])
        
        for item in study_section:
            display = item.get('displayValue', '')
            values = item.get('values', [])
            
            # Identify grouping
            grouping = None
            if 'Project Type' in values:
                grouping = 'Project Type'
            elif 'Assay Type' in display or 'Study Assay Technology Type' in values:
                grouping = 'Assay technology type'
            elif 'organism' in values:
                grouping = 'Organism'
            elif 'Tissue' in display or 'material type' in values:
                grouping = 'Material type'
            elif 'Factor' in display or 'Study Factor Name' in values:
                grouping = 'Factor'
            
            if not grouping:
                continue
            
            # Process children - store complete hierarchy
            for child in item.get('children', []):
                category = child.get('displayValue', child.get('values', [''])[0] if child.get('values') else '')
                
                if not category:
                    category = 'Uncategorized'
                
                if category not in structure[grouping]:
                    structure[grouping][category] = set()
                
                # Add all child values
                for val in child.get('values', []):
                    if val:
                        structure[grouping][category].add(val)
                
                # Handle nested children
                for subchild in child.get('children', []):
                    subcategory = subchild.get('displayValue', subchild.get('values', [''])[0] if subchild.get('values') else '')
                    full_category = f"{category}|{subcategory}"
                    
                    if full_category not in structure[grouping]:
                        structure[grouping][full_category] = set()
                    
                    for val in subchild.get('values', []):
                        if val:
                            structure[grouping][full_category].add(val)
        
        # Print summary
        for grouping, categories in structure.items():
            total_values = sum(len(v) for v in categories.values())
            print(f"  {grouping}: {total_values} values in {len(categories)} categories")
        
        return structure
    
    def initialize_from_existing(self):
        """Initialize new JSON with ALL existing values"""
        new_json = {
            'Project Type': defaultdict(set),
            'Assay technology type': defaultdict(set),
            'Factor': defaultdict(set),
            'Organism': defaultdict(set),
            'Material type': defaultdict(set),
            'Mission': defaultdict(set)
        }
        
        # Copy everything from existing
        for grouping, categories in self.existing_structure.items():
            for category, values in categories.items():
                new_json[grouping][category] = set(values)
        
        return new_json
    
    def find_category_for_value(self, value, grouping):
        """Find which category a value belongs to"""
        norm_val = self.norm(value)
        
        # Check existing structure first
        if grouping not in self.existing_structure:
            return None
        
        for category, values in self.existing_structure[grouping].items():
            for existing_val in values:
                if self.norm(existing_val) == norm_val:
                    return category
        
        return None
    
    def process_api_data(self):
        """Add new values from API data"""
        print("\nProcessing API data to find additions...")
        
        # Process Assays
        print("  Checking assay types...")
        col_idx = self.assay_data['columns'].index('investigation.study assays.study assay technology type')
        for row in self.assay_data['data']:
            osd_id = row[0]
            assay_type = row[col_idx]
            
            if not assay_type:
                continue
            
            self.all_osd_ids.add(osd_id)
            
            category = self.find_category_for_value(assay_type, 'Assay technology type')
            if category:
                # Check if this is actually new
                if assay_type not in self.new_json['Assay technology type'][category]:
                    self.new_json['Assay technology type'][category].add(assay_type)
                    self.additions.append(('Assay technology type', category, assay_type))
            else:
                # Unmapped - add to "Other" category
                if assay_type not in self.new_json['Assay technology type']['Other Assay Types']:
                    self.new_json['Assay technology type']['Other Assay Types'].add(assay_type)
                    self.unmapped.append(('Assay technology type', assay_type, osd_id))
        
        # Process Factors
        print("  Checking factors...")
        factor_cols = [col for col in self.factor_data['columns'] if 'factor value' in col.lower()]
        for col in factor_cols:
            factor_name = col.split('.')[-1]
            
            category = self.find_category_for_value(factor_name, 'Factor')
            if category:
                if factor_name not in self.new_json['Factor'][category]:
                    self.new_json['Factor'][category].add(factor_name)
                    self.additions.append(('Factor', category, factor_name))
            else:
                if factor_name not in self.new_json['Factor']['other']:
                    self.new_json['Factor']['other'].add(factor_name)
                    self.unmapped.append(('Factor', factor_name, 'schema'))
        
        # Process Organisms
        print("  Checking organisms...")
        col_idx = self.organism_data['columns'].index('study.characteristics.organism')
        for row in self.organism_data['data']:
            osd_id = row[0]
            organism = row[col_idx]
            
            if not organism:
                continue
            
            self.all_osd_ids.add(osd_id)
            
            category = self.find_category_for_value(organism, 'Organism')
            if category:
                if organism not in self.new_json['Organism'][category]:
                    self.new_json['Organism'][category].add(organism)
                    self.additions.append(('Organism', category, organism))
            else:
                if organism not in self.new_json['Organism']['Other Organisms']:
                    self.new_json['Organism']['Other Organisms'].add(organism)
                    self.unmapped.append(('Organism', organism, osd_id))
        
        # Process Materials
        print("  Checking material types...")
        col_idx = self.material_data['columns'].index('study.characteristics.material type')
        for row in self.material_data['data']:
            osd_id = row[0]
            material = row[col_idx]
            
            if not material:
                continue
            
            self.all_osd_ids.add(osd_id)
            
            category = self.find_category_for_value(material, 'Material type')
            if category:
                if material not in self.new_json['Material type'][category]:
                    self.new_json['Material type'][category].add(material)
                    self.additions.append(('Material type', category, material))
            else:
                if material not in self.new_json['Material type']['Other Materials']:
                    self.new_json['Material type']['Other Materials'].add(material)
                    self.unmapped.append(('Material type', material, osd_id))
        
        # Process Missions (NEW grouping)
        print("  Processing missions (new grouping)...")
        col_idx = self.mission_data['columns'].index('investigation.study.comment.project identifier')
        for row in self.mission_data['data']:
            osd_id = row[0]
            missions_str = row[col_idx]
            
            if not missions_str:
                continue
            
            self.all_osd_ids.add(osd_id)
            
            # Split by comma (some entries have multiple missions)
            missions = [m.strip() for m in missions_str.split(',')]
            
            for mission in missions:
                if not mission:
                    continue
                
                # Categorize mission
                mission_lower = self.norm(mission)
                
                if any(x in mission_lower for x in ['expedition', 'increment', 'iss']):
                    category = 'ISS Expeditions'
                elif any(x in mission_lower for x in ['sts-', 'sts ', 'shuttle', 'sls-']):
                    category = 'Space Shuttle'
                elif mission.startswith('RR-') or 'rodent research' in mission_lower:
                    category = 'Rodent Research'
                elif any(x in mission_lower for x in ['bion', 'cosmos']):
                    category = 'Bion/Cosmos'
                elif any(x in mission_lower for x in ['bric-', 'apex-', 'veg-', 'ffl', 'cbtm', 'cerise']):
                    category = 'Payload Investigations'
                elif any(x in mission_lower for x in ['ground', 'bsl', 'baseline']):
                    category = 'Ground Control'
                elif any(x in mission_lower for x in ['gamma_irradiation', 'heavy_ion', 'hze', 'proton_irradiation', 
                                                      'x-ray_irradiation', 'irradiation', 'radiation']):
                    category = 'Radiation Studies'
                elif any(x in mission_lower for x in ['hindlimb_unloading', 'simulated_microgravity', 
                                                       'simulated_hypergravity', 'simulated_environmental']):
                    category = 'Simulated Conditions'
                elif any(x in mission_lower for x in ['inspiration4', 'axiom', 'ax-', 'spacex']):
                    category = 'Commercial Spaceflight'
                else:
                    category = 'Other Missions'
                
                if mission not in self.new_json['Mission'][category]:
                    self.new_json['Mission'][category].add(mission)
                    if category == 'Other Missions':
                        self.unmapped.append(('Mission', mission, osd_id))
    
    def verify_completeness(self):
        """Verify all original values are present in new JSON"""
        print("\n" + "="*80)
        print("VERIFICATION: Checking completeness")
        print("="*80)
        
        # Extract all values from original
        original_values = set()
        for grouping, categories in self.existing_structure.items():
            for category, values in categories.items():
                for val in values:
                    original_values.add(self.norm(val))
        
        # Extract all values from new (excluding Mission which is new)
        new_values = set()
        for grouping in ['Project Type', 'Assay technology type', 'Factor', 'Organism', 'Material type']:
            if grouping not in self.new_json:
                continue
            for category, values in self.new_json[grouping].items():
                for val in values:
                    new_values.add(self.norm(val))
        
        missing = original_values - new_values
        
        print(f"\nOriginal values: {len(original_values)}")
        print(f"New values (excl. Mission): {len(new_values)}")
        print(f"Values added from API: {len(self.additions)}")
        print(f"Missing from new: {len(missing)}")
        
        if missing:
            print(f"\n❌ ERROR: {len(missing)} original values are MISSING from new JSON!")
            print("\nMissing values:")
            for val in sorted(missing)[:20]:
                print(f"  - {val}")
            if len(missing) > 20:
                print(f"  ... and {len(missing) - 20} more")
            return False
        else:
            print(f"\n✅ SUCCESS: All original values preserved!")
            print(f"✅ PLUS: {len(self.additions)} new values added from API")
            
            # Show Mission summary
            mission_total = sum(len(v) for v in self.new_json['Mission'].values())
            print(f"\n📊 NEW MISSION GROUPING: {mission_total} missions in {len(self.new_json['Mission'])} categories")
            print(f"📊 TOTAL OSD IDs COVERED: {len(self.all_osd_ids)}")
            
            return True
    
    def generate_output_json(self):
        """Generate final JSON structure"""
        output = {}
        
        # Order the groupings
        grouping_order = ['Project Type', 'Assay technology type', 'Factor', 'Organism', 'Material type', 'Mission']
        
        for grouping in grouping_order:
            if grouping not in self.new_json:
                continue
            output[grouping] = {}
            for category, values in sorted(self.new_json[grouping].items()):
                output[grouping][category] = sorted(list(values))
        
        return output
    
    def save_outputs(self, output_dir=None):
        """Save all output files"""
        print("\n" + "="*80)
        print("Saving outputs")
        print("="*80)
        
        if output_dir is None:
            # Default to current working directory (which should be writable)
            output_dir = os.getcwd()
        
        # Generate output JSON
        output_json = self.generate_output_json()
        
        # Save new filter-options JSON
        output_path = os.path.join(output_dir, 'filter-options-new.json')
        with open(output_path, 'w') as f:
            json.dump(output_json, f, indent=2)
        print(f"\n✓ New JSON: {output_path}")
        
        # Save additions report
        additions_path = os.path.join(output_dir, 'additions-report.txt')
        with open(additions_path, 'w') as f:
            f.write("ADDITIONS REPORT\n")
            f.write("="*80 + "\n")
            f.write(f"\nTotal new values added: {len(self.additions)}\n")
            f.write("="*80 + "\n\n")
            
            if self.additions:
                by_group = defaultdict(lambda: defaultdict(list))
                for grouping, category, value in self.additions:
                    by_group[grouping][category].append(value)
                
                for grouping in sorted(by_group.keys()):
                    f.write(f"\n{grouping}:\n")
                    f.write("-"*80 + "\n")
                    for category in sorted(by_group[grouping].keys()):
                        f.write(f"\n  {category}:\n")
                        for val in sorted(by_group[grouping][category]):
                            f.write(f"    + {val}\n")
            else:
                f.write("No new values added.\n")
        print(f"✓ Additions report: {additions_path}")
        
        # Save unmapped report
        unmapped_path = os.path.join(output_dir, 'unmapped-report.txt')
        with open(unmapped_path, 'w') as f:
            f.write("UNMAPPED ITEMS REPORT\n")
            f.write("="*80 + "\n")
            f.write("\nThese items from the API do not fit into existing categories.\n")
            f.write("They have been placed in 'Other' categories and may need\n")
            f.write("manual review to determine appropriate subcategories.\n")
            f.write("="*80 + "\n\n")
            
            if self.unmapped:
                by_group = defaultdict(list)
                for grouping, value, osd_id in self.unmapped:
                    by_group[grouping].append((value, osd_id))
                
                for grouping in sorted(by_group.keys()):
                    f.write(f"\n{grouping}:\n")
                    f.write("-"*80 + "\n")
                    
                    # Group by unique value
                    unique_unmapped = {}
                    for val, osd_id in by_group[grouping]:
                        if val not in unique_unmapped:
                            unique_unmapped[val] = []
                        unique_unmapped[val].append(osd_id)
                    
                    for val in sorted(unique_unmapped.keys()):
                        osd_list = ', '.join(unique_unmapped[val][:5])
                        more = len(unique_unmapped[val]) - 5
                        f.write(f"\n  {val}\n")
                        f.write(f"    Found in: {osd_list}")
                        if more > 0:
                            f.write(f" and {more} more")
                        f.write("\n")
            else:
                f.write("All items successfully categorized.\n")
        print(f"✓ Unmapped report: {unmapped_path}")
        
        return output_path, additions_path, unmapped_path
    
    def run(self):
        """Main execution"""
        # Process API data
        self.process_api_data()
        
        # Verify completeness
        is_complete = self.verify_completeness()
        
        # Save outputs
        output_files = self.save_outputs()
        
        print("\n" + "="*80)
        if is_complete:
            print("✅ COMPLETE: All original values preserved + new values added")
        else:
            print("❌ INCOMPLETE: Some original values are missing!")
            print("   Please review the output and check the verification section.")
        print("="*80)
        
        return is_complete


def main():
    """Main entry point"""
    if len(sys.argv) > 1:
        print("Note: This script no longer requires input files.")
        print("It will automatically download the current filter-options from OSDR.")
        print("\nUsage: python3 osdr_generator.py")
        print("\nProceeding with automatic download...\n")
    
    try:
        generator = OSDRFilterGenerator()
        success = generator.run()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
