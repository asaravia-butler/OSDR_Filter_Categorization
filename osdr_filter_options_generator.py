#!/usr/bin/env python3
"""
NASA OSDR Dashboard JSON Generator - Final Version
===================================================
Generates filter-options.json from OSDR API with intelligent categorization.

Key Features:
- New Assay structure: Measurement Type -> Technology Type -> Platform
- Smart material categorization (laterality, tissue specificity)
- Taxonomic organism classification (bacteria, plants, fungi, wasps)
- Case-insensitive matching throughout
- Preserves all existing values

Usage:
    python3 osdr_generator.py
"""

import json
import sys
import os
import requests
import re
from collections import defaultdict


class SmartCategorizer:
    """Intelligent categorization helper"""
    
    # Taxonomic databases
    BACTERIA_GENERA = {
        'Agrobacterium', 'Bacillus', 'Escherichia', 'Pseudomonas',
        'Salmonella', 'Staphylococcus', 'Streptococcus', 'Enterobacter',
        'Klebsiella', 'Serratia', 'Vibrio', 'Paraburkholderia',
        'Burkholderia', 'Rhizobium', 'Sinorhizobium'
    }
    
    FUNGUS_GENERA = {
        'Aspergillus', 'Candida', 'Fusarium', 'Penicillium',
        'Saccharomyces', 'Neurospora'
    }
    
    PLANT_GENERA = {
        'Arabidopsis', 'Brassica', 'Capsicum', 'Citrus', 'Daucus',
        'Glycine', 'Lactuca', 'Lolium', 'Marchantia', 'Oryza',
        'Raphanus', 'Solanum', 'Triticum', 'Zea'
    }
    
    WASP_GENERA = {
        'Leptopilina', 'Nasonia'
    }
    
    @staticmethod
    def normalize(s):
        """Normalize string for comparison"""
        if not s or not isinstance(s, str):
            return ""
        return s.strip().lower()
    
    @staticmethod
    def get_taxonomy_category(organism_name):
        """
        Classify organism by taxonomy.
        Returns (type, full_category) or None.
        """
        if not organism_name:
            return None
        
        parts = organism_name.split()
        if not parts:
            return None
        
        genus = parts[0]
        
        if genus in SmartCategorizer.BACTERIA_GENERA:
            return ('bacteria', f'bacteria|{organism_name}')
        if genus in SmartCategorizer.FUNGUS_GENERA:
            return ('fungus', f'fungus|{organism_name}')
        if genus in SmartCategorizer.PLANT_GENERA:
            return ('plant', f'plant|{organism_name}')
        if genus in SmartCategorizer.WASP_GENERA:
            return ('wasp', f'wasp|{organism_name}')
        
        return None
    
    @staticmethod
    def match_material_to_existing(value, existing_categories):
        """
        Match material to existing categories using smart patterns.
        Handles: laterality, case differences, anatomical keywords
        Special: 3-tier hierarchy for muscles (muscle|muscle_name|laterality)
        """
        norm_val = SmartCategorizer.normalize(value)
        
        # Define muscle types that get 3-tier hierarchy
        muscle_types = [
            'gastrocnemius', 'soleus', 'tibialis anterior', 'quadriceps femoris', 
            'extensor digitorum longus', 'quadriceps', 'vastus lateralis', 'calf muscle'
        ]
        
        # First: Try exact match (case-insensitive)
        for category in existing_categories:
            cat_values = existing_categories[category]
            for existing_val in cat_values:
                if SmartCategorizer.normalize(existing_val) == norm_val:
                    return category
        
        # Second: Laterality patterns (left/right/both + term)
        laterality_match = re.match(r'^(left|right|both)\s+(.+)$', norm_val)
        if laterality_match:
            laterality = laterality_match.group(1)
            base_term = laterality_match.group(2).strip()
            
            # Check if this is a muscle (3-tier hierarchy)
            matched_muscle = None
            for muscle in muscle_types:
                if muscle in base_term:
                    matched_muscle = muscle
                    break
            
            if matched_muscle:
                # Create 3-tier: muscle|muscle_name|laterality muscle_name
                return f"muscle|{matched_muscle}|{laterality} {matched_muscle}"
            
            # For non-muscles, create 2-tier hierarchy
            # Look for parent category with base term
            for category in existing_categories:
                cat_norm = SmartCategorizer.normalize(category)
                
                # Check if category contains base term
                if '|' in category:
                    cat_parts = [SmartCategorizer.normalize(p) for p in category.split('|')]
                    if base_term in cat_parts or any(base_term in p or p in base_term for p in cat_parts):
                        # Create laterality subcategory
                        parent = category.split('|')[0]
                        return f"{parent}|{laterality} {base_term}"
                else:
                    if base_term == cat_norm or base_term in cat_norm or cat_norm in base_term:
                        return f"{category}|{laterality} {base_term}"
        
        # Third: Substring matching with existing values
        for category in existing_categories:
            cat_values = existing_categories[category]
            for existing_val in cat_values:
                existing_norm = SmartCategorizer.normalize(existing_val)
                
                # Check if either contains the other
                if existing_norm in norm_val or norm_val in existing_norm:
                    return category
        
        # Fourth: Anatomical keyword mapping
        anatomical_keywords = {
            'cerebellum': 'brain|cerebellum',
            'cerebrum': 'brain|cerebrum',
            'cerebral cortex': 'brain|cerebrum',
            'hippocampus': 'brain|hippocampus',
            'frontal cortex': 'brain|frontal cortex',
            'parietal cortex': 'brain|parietal cortex',
            'cortex': 'brain|cortex',
            'ventricle': 'heart',
            'gastrocnemius': 'muscle|gastrocnemius',
            'soleus': 'muscle|soleus',
            'tibialis anterior': 'muscle|tibialis anterior',
            'quadriceps': 'muscle|quadriceps femoris',
            'extensor digitorum longus': 'muscle|extensor digitorum longus',
        }
        
        for keyword, target_cat in anatomical_keywords.items():
            if keyword in norm_val:
                # Check if target category exists
                for existing_cat in existing_categories:
                    if SmartCategorizer.normalize(existing_cat) == SmartCategorizer.normalize(target_cat):
                        return existing_cat
                # If not, try to match the parent
                if '|' in target_cat:
                    parent = target_cat.split('|')[0]
                    for existing_cat in existing_categories:
                        if SmartCategorizer.normalize(existing_cat) == SmartCategorizer.normalize(parent):
                            return target_cat
        
        return None


class OSDRFilterGenerator:
    def __init__(self):
        """Initialize and fetch all data"""
        print("="*80)
        print("NASA OSDR Filter Options Generator - Final Version")
        print("="*80)
        
        self.base_url = "https://visualization.osdr.nasa.gov/biodata/api/v2"
        self.filter_options_url = "https://osdr.nasa.gov/geode-py/ws/repo/filter-options"
        self.session = requests.Session()
        self.categorizer = SmartCategorizer()
        
        print(f"\nDownloading current filter-options...")
        self.current_json = self.download_current_json()
        
        print("\nFetching API data...")
        self.assay_data = self.fetch_assay_data()
        self.factor_data = self.fetch_factor_data()
        self.organism_data = self.fetch_organism_data()
        self.material_data = self.fetch_material_data()
        self.mission_data = self.fetch_mission_data()
        
        self.existing_structure = self.extract_existing_structure()
        self.new_json = self.initialize_from_existing()
        
        self.additions = []
        self.unmapped = []
        self.all_osd_ids = set()
    
    def download_current_json(self):
        """Download current filter-options from OSDR"""
        try:
            response = self.session.get(self.filter_options_url, timeout=30)
            response.raise_for_status()
            data = response.json()
            print(f"  ✓ Downloaded successfully")
            return data
        except Exception as e:
            print(f"  ✗ Failed: {e}")
            raise
    
    def fetch_api_data(self, endpoint, description):
        """Fetch from API"""
        url = f"{self.base_url}/query/assays/{endpoint}"
        print(f"  Fetching {description}...")
        
        try:
            response = self.session.get(url, timeout=60)
            response.raise_for_status()
            data = response.json()
            
            if 'columns' not in data or 'data' not in data:
                raise ValueError(f"Invalid format for {description}")
            
            print(f"    ✓ {len(data['columns'])} columns, {len(data['data'])} rows")
            return data
        except Exception as e:
            print(f"    ✗ Failed: {e}")
            raise
    
    def fetch_assay_data(self):
        """Fetch assay data with measurement, technology, and platform"""
        return self.fetch_api_data(
            "?investigation.study%20assays.study%20assay%20measurement%20type=//&investigation.study%20assays.study%20assay%20technology%20type=//&investigation.study%20assays.study%20assay%20technology%20platform=//&format=json.split",
            "Assay Measurement/Technology/Platform"
        )
    
    def fetch_factor_data(self):
        return self.fetch_api_data(
            "?investigation.study%20assays.study%20assay%20technology%20type&assay.factor%20value&study.factor%20value&schema&format=json.split",
            "Factors"
        )
    
    def fetch_organism_data(self):
        return self.fetch_api_data(
            "?investigation.study%20assays.study%20assay%20technology%20type=//&study.characteristics.organism=//&format=json.split",
            "Organisms"
        )
    
    def fetch_material_data(self):
        return self.fetch_api_data(
            "?investigation.study%20assays.study%20assay%20technology%20type=//&study.characteristics.material%20type=//&format=json.split",
            "Material Types"
        )
    
    def fetch_mission_data(self):
        return self.fetch_api_data(
            "?investigation.study%20assays.study%20assay%20technology%20type=//&investigation.study.comment.Project%20Identifier=//&format=json.split",
            "Missions"
        )
    
    def norm(self, s):
        return self.categorizer.normalize(s)
    
    def extract_existing_structure(self):
        """Extract existing structure from current JSON (handles both old and new formats)"""
        print("\nExtracting existing structure...")
        
        structure = {
            'Project Type': {},
            'Assay technology type': {},
            'Factor': {},
            'Organism': {},
            'Material type': {}
        }
        
        # Check if this is the NEW flat format or OLD nested format
        if 'Assay technology type' in self.current_json:
            # NEW FORMAT: Direct section keys with flat dictionaries
            print("  Detected NEW format (flat sections)")
            for grouping in structure.keys():
                if grouping in self.current_json:
                    for category, values in self.current_json[grouping].items():
                        if category not in structure[grouping]:
                            structure[grouping][category] = set()
                        for val in values:
                            if val:
                                structure[grouping][category].add(val)
        else:
            # OLD FORMAT: Nested 'study' array
            print("  Detected OLD format (nested 'study' array)")
            study_section = self.current_json.get('study', [])
            
            for item in study_section:
                display = item.get('displayValue', '')
                values = item.get('values', [])
                
                grouping = None
                if 'Project Type' in values:
                    grouping = 'Project Type'
                elif 'Assay Type' in display or 'Study Assay Technology Type' in values:
                    grouping = 'Assay technology type'
                elif 'organism' in values:
                    grouping = 'Organism'
                elif 'Tissue' in display or 'material type' in ' '.join(values).lower():
                    grouping = 'Material type'
                elif 'Factor' in display or 'Study Factor Name' in values:
                    grouping = 'Factor'
                
                if not grouping:
                    continue
                
                for child in item.get('children', []):
                    category = child.get('displayValue', child.get('values', [''])[0] if child.get('values') else '')
                    
                    if not category:
                        category = 'Uncategorized'
                    
                    if category not in structure[grouping]:
                        structure[grouping][category] = set()
                    
                    for val in child.get('values', []):
                        if val:
                            structure[grouping][category].add(val)
                    
                    for subchild in child.get('children', []):
                        subcategory = subchild.get('displayValue', subchild.get('values', [''])[0] if subchild.get('values') else '')
                        full_category = f"{category}|{subcategory}"
                        
                        if full_category not in structure[grouping]:
                            structure[grouping][full_category] = set()
                        
                        for val in subchild.get('values', []):
                            if val:
                                structure[grouping][full_category].add(val)
        
        for grouping, categories in structure.items():
            total = sum(len(v) for v in categories.values())
            print(f"  {grouping}: {total} values in {len(categories)} categories")
        
        return structure
    
    def initialize_from_existing(self):
        """Start with all existing values"""
        new_json = {
            'Project Type': defaultdict(set),
            'Assay technology type': defaultdict(set),
            'Factor': defaultdict(set),
            'Organism': defaultdict(set),
            'Material type': defaultdict(set),
            'Mission': defaultdict(set)
        }
        
        for grouping, categories in self.existing_structure.items():
            for category, values in categories.items():
                new_json[grouping][category] = set(values)
        
        return new_json
    
    def process_api_data(self):
        """Process all API data with smart categorization"""
        print("\nProcessing API data...")
        
        # ASSAYS - 3-level hierarchical structure with full capitalization normalization
        print("  Processing assays (measurement -> technology -> platform)...")
        measurement_idx = self.assay_data['columns'].index('investigation.study assays.study assay measurement type')
        technology_idx = self.assay_data['columns'].index('investigation.study assays.study assay technology type')
        platform_idx = self.assay_data['columns'].index('investigation.study assays.study assay technology platform')
        
        # Build canonical mappings for all levels (case-insensitive, first occurrence wins)
        measurement_canonical = {}
        tech_canonical = {}
        platform_canonical = {}
        
        for row in self.assay_data['data']:
            osd_id = row[0]
            measurement = row[measurement_idx]
            technology = row[technology_idx]
            platform = row[platform_idx]
            
            if not measurement or not technology:
                continue
            
            self.all_osd_ids.add(osd_id)
            
            # Determine canonical names (case-insensitive matching)
            # Level 1: Measurement
            if self.norm(measurement) not in measurement_canonical:
                measurement_canonical[self.norm(measurement)] = measurement
            canonical_measurement = measurement_canonical[self.norm(measurement)]
            
            # Level 2: Technology (within this measurement context)
            tech_key = f"{self.norm(canonical_measurement)}|{self.norm(technology)}"
            if tech_key not in tech_canonical:
                tech_canonical[tech_key] = technology
            canonical_tech = tech_canonical[tech_key]
            
            # Level 3: Platform (within this measurement|technology context)
            if platform:
                platform_key = f"{self.norm(canonical_measurement)}|{self.norm(canonical_tech)}|{self.norm(platform)}"
                if platform_key not in platform_canonical:
                    platform_canonical[platform_key] = platform
                canonical_platform = platform_canonical[platform_key]
            
            # Now add using canonical names for categories
            # Level 1: Measurement type
            if measurement not in self.new_json['Assay technology type'][canonical_measurement]:
                self.new_json['Assay technology type'][canonical_measurement].add(measurement)
                self.additions.append(('Assay technology type', canonical_measurement, measurement))
            
            # Level 2: Measurement|Technology (use canonical names)
            measurement_tech_cat = f"{canonical_measurement}|{canonical_tech}"
            if technology not in self.new_json['Assay technology type'][measurement_tech_cat]:
                self.new_json['Assay technology type'][measurement_tech_cat].add(technology)
                self.additions.append(('Assay technology type', measurement_tech_cat, technology))
            
            # Level 3: Measurement|Technology|Platform (use canonical names)
            if platform:
                measurement_tech_platform_cat = f"{canonical_measurement}|{canonical_tech}|{canonical_platform}"
                if platform not in self.new_json['Assay technology type'][measurement_tech_platform_cat]:
                    self.new_json['Assay technology type'][measurement_tech_platform_cat].add(platform)
                    self.additions.append(('Assay technology type', measurement_tech_platform_cat, platform))
        
        # FACTORS - Create hierarchical structure
        print("  Processing factors...")
        factor_cols = [col for col in self.factor_data['columns'] if 'factor value' in col.lower()]
        
        # Define parent-child mappings based on manual JSON analysis
        factor_hierarchies = {
            'age': ['age at sample collection', 'age at sample harvest', 'age at start of experiment', 'donor age'],
            'duration': ['exposure duration', 'hindlimb reloading duration', 'hindlimb unloading duration', 'treatment duration'],
            'ionizing radiation': ['absorbed radiation dose', 'dose', 'ionizing radiation device or source', 
                                   'number of radiation doses', 'particle charge', 'radiation distance', 'time post-irradiation'],
            'preservation method': ['carcass preservation method', 'freezing', 'freezing profile', 
                                   'order of preservation', 'sample preservation method', 
                                   'tissue homogenate preservation time at -80c in rlt buffer', 'tissue preservation method'],
            'time': ['assay time post-irradiation', 'dissection timeline', 'growth time', 'post radiation timepoint',
                    'sample storage time', 'sampling time', 'time of sample collection after euthanasia',
                    'time of sample collection after irradiation', 'time of sample collection after treatment',
                    'time post-irradiation', 'tissue homogenate preservation time at -80c in rlt buffer'],
            'tissue': ['tissue type', 'tissue segment'],
            'treatment': ['bleomycin treatment', 'infection'],
            'weightlessness simulation': ['hindlimb unloading', 'partial weight bearing'],
        }
        
        for col in factor_cols:
            factor_name = col.split('.')[-1]
            
            # First check if it exists in current structure (exact match)
            found = False
            if 'Factor' in self.existing_structure:
                for category, values in self.existing_structure['Factor'].items():
                    for val in values:
                        if self.norm(val) == self.norm(factor_name):
                            if factor_name not in self.new_json['Factor'][category]:
                                self.new_json['Factor'][category].add(factor_name)
                                self.additions.append(('Factor', category, factor_name))
                            found = True
                            break
                    if found:
                        break
            
            if not found:
                # Check if this factor should be a child of a parent
                parent_found = False
                for parent, children in factor_hierarchies.items():
                    if self.norm(factor_name) in [self.norm(c) for c in children]:
                        # Create hierarchical category: parent|child
                        hierarchical_cat = f"{parent}|{factor_name}"
                        if factor_name not in self.new_json['Factor'][hierarchical_cat]:
                            self.new_json['Factor'][hierarchical_cat].add(factor_name)
                            self.additions.append(('Factor', hierarchical_cat, factor_name))
                        
                        # Also add parent as standalone if not present
                        if parent not in self.new_json['Factor'][parent]:
                            self.new_json['Factor'][parent].add(parent)
                        
                        parent_found = True
                        break
                
                if not parent_found:
                    # Put in other|factor_name
                    other_cat = f"other|{factor_name}"
                    if factor_name not in self.new_json['Factor'][other_cat]:
                        self.new_json['Factor'][other_cat].add(factor_name)
                        self.unmapped.append(('Factor', factor_name, 'schema'))
        
        # ORGANISMS
        print("  Processing organisms...")
        col_idx = self.organism_data['columns'].index('study.characteristics.organism')
        for row in self.organism_data['data']:
            osd_id = row[0]
            organism = row[col_idx]
            
            if not organism:
                continue
            
            self.all_osd_ids.add(osd_id)
            
            # Try exact match first
            found = False
            if 'Organism' in self.existing_structure:
                for category, values in self.existing_structure['Organism'].items():
                    for val in values:
                        if self.norm(val) == self.norm(organism):
                            if organism not in self.new_json['Organism'][category]:
                                self.new_json['Organism'][category].add(organism)
                                self.additions.append(('Organism', category, organism))
                            found = True
                            break
                    if found:
                        break
            
            # Try taxonomic classification
            if not found:
                taxonomy = self.categorizer.get_taxonomy_category(organism)
                if taxonomy:
                    _, full_category = taxonomy
                    if organism not in self.new_json['Organism'][full_category]:
                        self.new_json['Organism'][full_category].add(organism)
                        self.additions.append(('Organism', full_category, organism))
                else:
                    if organism not in self.new_json['Organism']['Other Organisms']:
                        self.new_json['Organism']['Other Organisms'].add(organism)
                        self.unmapped.append(('Organism', organism, osd_id))
        
        # MATERIALS
        print("  Processing materials...")
        col_idx = self.material_data['columns'].index('study.characteristics.material type')
        
        for row in self.material_data['data']:
            osd_id = row[0]
            material = row[col_idx]
            
            if not material:
                continue
            
            self.all_osd_ids.add(osd_id)
            
            # Try smart matching
            matched_cat = self.categorizer.match_material_to_existing(material, self.existing_structure.get('Material type', {}))
            
            if matched_cat:
                # Check if this is a 3-tier muscle category
                if matched_cat.count('|') == 2 and matched_cat.startswith('muscle|'):
                    # This is muscle|muscle_name|laterality
                    # Add to tier 3
                    if material not in self.new_json['Material type'][matched_cat]:
                        self.new_json['Material type'][matched_cat].add(material)
                        self.additions.append(('Material type', matched_cat, material))
                    
                    # Extract muscle name and ensure tier 2 exists with base name only
                    parts = matched_cat.split('|')
                    muscle_name = parts[1]
                    tier2_cat = f"muscle|{muscle_name}"
                    
                    # Add base muscle name to tier 2 (lowercase version)
                    if muscle_name not in self.new_json['Material type'][tier2_cat]:
                        self.new_json['Material type'][tier2_cat].add(muscle_name)
                    
                    # Add capitalized version if present in existing data
                    capitalized = muscle_name.title()
                    if capitalized != muscle_name:
                        # Check if capitalized version exists in original
                        for cat_vals in self.existing_structure.get('Material type', {}).values():
                            if capitalized in cat_vals:
                                if capitalized not in self.new_json['Material type'][tier2_cat]:
                                    self.new_json['Material type'][tier2_cat].add(capitalized)
                                break
                else:
                    # Regular category
                    if material not in self.new_json['Material type'][matched_cat]:
                        self.new_json['Material type'][matched_cat].add(material)
                        self.additions.append(('Material type', matched_cat, material))
            else:
                if material not in self.new_json['Material type']['Other Materials']:
                    self.new_json['Material type']['Other Materials'].add(material)
                    self.unmapped.append(('Material type', material, osd_id))
        
        # MISSIONS
        print("  Processing missions...")
        col_idx = self.mission_data['columns'].index('investigation.study.comment.project identifier')
        for row in self.mission_data['data']:
            osd_id = row[0]
            missions_str = row[col_idx]
            
            if not missions_str:
                continue
            
            self.all_osd_ids.add(osd_id)
            missions = [m.strip() for m in missions_str.split(',')]
            
            for mission in missions:
                if not mission:
                    continue
                
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
        """Verify all original values preserved"""
        print("\n" + "="*80)
        print("VERIFICATION")
        print("="*80)
        
        original_values = set()
        for grouping, categories in self.existing_structure.items():
            for category, values in categories.items():
                for val in values:
                    original_values.add(self.norm(val))
        
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
        print(f"Values added: {len(self.additions)}")
        print(f"Missing: {len(missing)}")
        
        if missing:
            print(f"\n❌ ERROR: {len(missing)} values missing!")
            for val in sorted(missing)[:20]:
                print(f"  - {val}")
            return False
        else:
            print(f"\n✅ SUCCESS: All preserved + {len(self.additions)} added")
            mission_total = sum(len(v) for v in self.new_json['Mission'].values())
            print(f"📊 Missions: {mission_total} in {len(self.new_json['Mission'])} categories")
            print(f"📊 OSD IDs: {len(self.all_osd_ids)}")
            return True
    
    def generate_output_json(self):
        """Generate final JSON"""
        output = {}
        
        for grouping in ['Project Type', 'Assay technology type', 'Factor', 'Organism', 'Material type', 'Mission']:
            if grouping not in self.new_json:
                continue
            output[grouping] = {}
            for category, values in sorted(self.new_json[grouping].items()):
                output[grouping][category] = sorted(list(values))
        
        return output
    
    def save_outputs(self):
        """Save output files"""
        print("\n" + "="*80)
        print("Saving outputs")
        print("="*80)
        
        output_json = self.generate_output_json()
        
        # Save JSON
        output_path = os.path.join(os.getcwd(), 'filter-options-new.json')
        with open(output_path, 'w') as f:
            json.dump(output_json, f, indent=2)
        print(f"\n✓ JSON: {output_path}")
        
        # Save additions report
        additions_path = os.path.join(os.getcwd(), 'additions-report.txt')
        with open(additions_path, 'w') as f:
            f.write(f"ADDITIONS REPORT\n{'='*80}\n\nTotal: {len(self.additions)}\n{'='*80}\n\n")
            
            if self.additions:
                by_group = defaultdict(lambda: defaultdict(list))
                for grouping, category, value in self.additions:
                    by_group[grouping][category].append(value)
                
                for grouping in sorted(by_group.keys()):
                    f.write(f"\n{grouping}:\n{'-'*80}\n")
                    for category in sorted(by_group[grouping].keys()):
                        f.write(f"\n  {category}:\n")
                        for val in sorted(by_group[grouping][category]):
                            f.write(f"    + {val}\n")
        print(f"✓ Additions: {additions_path}")
        
        # Save unmapped report
        unmapped_path = os.path.join(os.getcwd(), 'unmapped-report.txt')
        with open(unmapped_path, 'w') as f:
            f.write(f"UNMAPPED REPORT\n{'='*80}\n\n")
            
            if self.unmapped:
                by_group = defaultdict(list)
                for grouping, value, osd_id in self.unmapped:
                    by_group[grouping].append((value, osd_id))
                
                for grouping in sorted(by_group.keys()):
                    f.write(f"\n{grouping}:\n{'-'*80}\n")
                    unique = {}
                    for val, osd_id in by_group[grouping]:
                        if val not in unique:
                            unique[val] = []
                        unique[val].append(osd_id)
                    
                    for val in sorted(unique.keys()):
                        osd_list = ', '.join(unique[val][:5])
                        more = len(unique[val]) - 5
                        f.write(f"\n  {val}\n    In: {osd_list}")
                        if more > 0:
                            f.write(f" +{more} more")
                        f.write("\n")
        print(f"✓ Unmapped: {unmapped_path}")
    
    def run(self):
        """Main execution"""
        self.process_api_data()
        is_complete = self.verify_completeness()
        self.save_outputs()
        
        print("\n" + "="*80)
        if is_complete:
            print("✅ COMPLETE")
        else:
            print("❌ INCOMPLETE")
        print("="*80)
        
        return is_complete


def main():
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
