"""
SSB (Statistics Norway) API Wrapper
Handles all interactions with Statistics Norway's open data API
"""

import requests
import json
from typing import Dict, List, Optional, Any
import time
from pathlib import Path

class SSBApi:
    """Wrapper for Statistics Norway API"""
    
    def __init__(self, base_url: str = "https://data.ssb.no/api/v0", cache_dir: str = "data/ssb_cache"):
        self.base_url = base_url
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
    def _get_cache_path(self, table_id: str, query_hash: str) -> Path:
        """Generate cache file path"""
        return self.cache_dir / f"{table_id}_{query_hash}.json"
    
    def _load_from_cache(self, cache_path: Path) -> Optional[Dict]:
        """Load data from cache if exists"""
        if cache_path.exists():
            with open(cache_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    
    def _save_to_cache(self, cache_path: Path, data: Dict):
        """Save data to cache"""
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def get_table_metadata(self, table_id: str) -> Dict:
        """
        Get metadata about a table
        
        Args:
            table_id: SSB table ID (e.g., "10235" for household budget)
        
        Returns:
            Dictionary with table metadata
        """
        url = f"{self.base_url}/en/table/{table_id}"
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error fetching metadata for table {table_id}: {e}")
            return {}
    
    def query_table(self, table_id: str, query: Dict, use_cache: bool = True) -> Optional[Dict]:
        """
        Query SSB table with POST request
        
        Args:
            table_id: SSB table ID
            query: Query specification (JSON format)
            use_cache: Whether to use cached results
        
        Returns:
            Query results as dictionary
        """
        # Generate cache key
        query_str = json.dumps(query, sort_keys=True)
        query_hash = str(hash(query_str))
        cache_path = self._get_cache_path(table_id, query_hash)
        
        # Check cache first
        if use_cache:
            cached_data = self._load_from_cache(cache_path)
            if cached_data:
                print(f"✅ Loaded from cache: {table_id}")
                return cached_data
        
        # Make API request
        url = f"{self.base_url}/en/table/{table_id}"
        headers = {'Content-Type': 'application/json'}
        
        try:
            print(f"🔍 Querying SSB table {table_id}...")
            response = requests.post(url, json=query, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            
            # Save to cache
            if use_cache:
                self._save_to_cache(cache_path, data)
                print(f"💾 Saved to cache: {table_id}")
            
            return data
            
        except requests.RequestException as e:
            print(f"❌ Error querying table {table_id}: {e}")
            return None
    
    def get_household_budget_data(self, 
                                   year: str = "2012",
                                   categories: Optional[List[str]] = None) -> Dict:
        """
        Convenience method for household budget survey (Table 10235)
        
        Args:
            year: Year of data (default: "2012" - recent available year)
            categories: List of spending categories to retrieve
        
        Returns:
            Household budget data
        """
        table_id = "10235"
        
        # Query structure for SSB Table 10235
        # Variables: Forbruksundersok (categories), ContentsCode, Tid (year)
        query = {
            "query": [
                {
                    "code": "ContentsCode",
                    "selection": {
                        "filter": "item",
                        "values": ["Utgift"]  # Expenditure in NOK
                    }
                },
                {
                    "code": "Tid",
                    "selection": {
                        "filter": "item",
                        "values": [year]
                    }
                }
            ],
            "response": {
                "format": "json-stat2"
            }
        }
        
        # Add category filter if specified, otherwise get main categories
        if categories:
            query["query"].insert(0, {
                "code": "Forbruksundersok",
                "selection": {
                    "filter": "item",
                    "values": categories
                }
            })
        else:
            # Get main spending categories (top level: 01-12)
            query["query"].insert(0, {
                "code": "Forbruksundersok",
                "selection": {
                    "filter": "item",
                    "values": ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"]
                }
            })
        
        return self.query_table(table_id, query)
    
    def parse_household_data(self, raw_data: Dict) -> List[Dict[str, Any]]:
        """
        Parse JSON-stat format household data into simple list
        
        Args:
            raw_data: Raw data from SSB API
        
        Returns:
            List of dictionaries with category, value, etc.
        """
        if not raw_data:
            return []
        
        try:
            # JSON-stat2 format structure
            dimension = raw_data.get('dimension', {})
            value = raw_data.get('value', [])
            
            # Get Forbruksundersok categories (spending categories)
            forbruk_dim = dimension.get('Forbruksundersok', {})
            forbruk_category = forbruk_dim.get('category', {})
            forbruk_labels = forbruk_category.get('label', {})
            forbruk_index = forbruk_category.get('index', {})
            
            # Get year
            tid_dim = dimension.get('Tid', {})
            tid_category = tid_dim.get('category', {})
            years = list(tid_category.get('label', {}).values())
            year = years[0] if years else "Unknown"
            
            results = []
            
            # Map each value to its category
            for category_code, category_label in forbruk_labels.items():
                # Find the index for this category
                idx = forbruk_index.get(category_code)
                if idx is not None and idx < len(value):
                    val = value[idx]
                    if val is not None:
                        results.append({
                            'category': category_label,
                            'category_code': category_code,
                            'value': val,
                            'year': year,
                            'unit': 'NOK per year'
                        })
            
            return results
            
        except Exception as e:
            print(f"❌ Error parsing data: {e}")
            import traceback
            traceback.print_exc()
            return []


# Example usage function
def test_ssb_api():
    """Test the SSB API wrapper"""
    print("🧪 Testing SSB API Wrapper\n")
    
    api = SSBApi()
    
    # Test 1: Get table metadata
    print("📋 Test 1: Get table metadata")
    metadata = api.get_table_metadata("10235")
    if metadata:
        print(f"✅ Got metadata for table 10235")
        print(f"   Title: {metadata.get('title', 'N/A')}\n")
    
    # Test 2: Query household budget data
    print("📊 Test 2: Query household budget data")
    data = api.get_household_budget_data(year="2012")  # Use 2012 (recent available)
    if data:
        print(f"✅ Got household budget data")
        
        # Parse and display
        parsed = api.parse_household_data(data)
        print(f"   Found {len(parsed)} categories")
        
        # Show first 5 categories
        print("\n   Sample data:")
        for item in parsed[:5]:
            # Convert to monthly for easier reading
            monthly = item['value'] / 12
            print(f"   - {item['category']}: {monthly:,.0f} NOK/month ({item['value']:,.0f} NOK/year)")
    else:
        print("❌ Failed to get data")
    
    print("\n✅ SSB API tests complete!")


if __name__ == "__main__":
    test_ssb_api()