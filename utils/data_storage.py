import os
import json
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any
import shutil

class DataStorage:
    def __init__(self, base_path: str = 'storage'):
        self.base_path = base_path
        self.setup_directories()
        
    def setup_directories(self):
        """Create storage directory structure"""
        directories = [
            'raw_data',
            'processed_data', 
            'arc_returns',
            'annual_reports',
            'regulatory_data',
            'companies_house_data',
            'social_media_data',
            'website_data'
        ]
        
        for directory in directories:
            os.makedirs(os.path.join(self.base_path, directory), exist_ok=True)
    
    def save_raw_discovery_data(self, associations: List[Dict], source: str) -> str:
        """Save raw discovery data"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"raw_discovery_{source}_{timestamp}.json"
        filepath = os.path.join(self.base_path, 'raw_data', filename)
        
        with open(filepath, 'w') as f:
            json.dump(associations, f, indent=2, default=str)
        
        print(f"Raw discovery data saved: {filepath}")
        return filepath
    
    def save_companies_house_data(self, company_number: str, data: Dict) -> str:
        """Save individual Companies House data"""
        filename = f"{company_number}.json"
        filepath = os.path.join(self.base_path, 'companies_house_data', filename)
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        return filepath
    
    def save_arc_return(self, company_number: str, arc_data: Dict) -> str:
        """Save ARC return data"""
        filename = f"{company_number}_arc.json"
        filepath = os.path.join(self.base_path, 'arc_returns', filename)
        
        with open(filepath, 'w') as f:
            json.dump(arc_data, f, indent=2, default=str)
        
        return filepath
    
    def save_annual_report(self, company_number: str, report_url: str, report_data: bytes = None) -> str:
        """Save annual report"""
        if report_data:
            # Save actual report file
            filename = f"{company_number}_annual_report.pdf"
            filepath = os.path.join(self.base_path, 'annual_reports', filename)
            
            with open(filepath, 'wb') as f:
                f.write(report_data)
        else:
            # Save just the URL reference
            filename = f"{company_number}_annual_report_url.txt"
            filepath = os.path.join(self.base_path, 'annual_reports', filename)
            
            with open(filepath, 'w') as f:
                f.write(report_url)
        
        return filepath
    
    def save_regulatory_data(self, company_number: str, regulator: str, data: Dict) -> str:
        """Save regulatory data"""
        filename = f"{company_number}_{regulator}.json"
        filepath = os.path.join(self.base_path, 'regulatory_data', filename)
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        return filepath
    
    def save_processed_dataset(self, associations: List[Dict], dataset_name: str) -> str:
        """Save final processed dataset"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save as JSON
        json_filename = f"{dataset_name}_{timestamp}.json"
        json_filepath = os.path.join(self.base_path, 'processed_data', json_filename)
        
        with open(json_filepath, 'w') as f:
            json.dump(associations, f, indent=2, default=str)
        
        # Save as CSV
        csv_filename = f"{dataset_name}_{timestamp}.csv"
        csv_filepath = os.path.join(self.base_path, 'processed_data', csv_filename)
        
        df = pd.DataFrame(associations)
        df.to_csv(csv_filepath, index=False)
        
        print(f"Processed dataset saved: {json_filepath} and {csv_filepath}")
        return json_filepath
    
    def load_latest_dataset(self, dataset_name: str) -> List[Dict]:
        """Load the latest processed dataset"""
        processed_dir = os.path.join(self.base_path, 'processed_data')
        
        # Find latest file matching pattern
        matching_files = [f for f in os.listdir(processed_dir) if f.startswith(dataset_name) and f.endswith('.json')]
        
        if not matching_files:
            return []
        
        latest_file = sorted(matching_files)[-1]  # Get most recent
        filepath = os.path.join(processed_dir, latest_file)
        
        with open(filepath, 'r') as f:
            return json.load(f)
    
    def get_storage_summary(self) -> Dict:
        """Get summary of stored data"""
        summary = {}
        
        for directory in os.listdir(self.base_path):
            dir_path = os.path.join(self.base_path, directory)
            if os.path.isdir(dir_path):
                file_count = len([f for f in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, f))])
                summary[directory] = file_count
        
        return summary