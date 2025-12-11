"""
SSB (Statistics Norway) API Wrapper
Handles all interactions with Statistics Norway's open data API
"""

import json
from typing import Dict, List, Optional, Any
import time
from pathlib import Path
import urllib.request
import urllib.error
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SSBApi:
    """Wrapper for Statistics Norway API"""
    
    def __init__(self, base_url: str = "https://data.ssb.no/api/v0", cache_dir: str = "data/ssb_cache"):
        self.base_url = base_url
        self.cache_dir = Path(cache_dir)
        # self.cache_dir.mkdir(parents=True, exist_ok=True) # Not using file cache for now
        self.cache = {} # In-memory cache
        
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
            with urllib.request.urlopen(url) as response:
                if response.status == 200:
                    return json.loads(response.read().decode('utf-8'))
                return {}
        except Exception as e:
            print(f"Error fetching metadata for table {table_id}: {e}")
            return {}
    
    def query_table(self, table_id: str, query: Dict, use_cache: bool = True) -> Optional[Dict]:
        """
        Query SSB table with POST request
        
        Args:
            table_id: SSB table ID
            query: Query specification (JSON format)
        Post query to SSB API for a specific table
        """
        if use_cache and table_id in self.cache:
            # Simple cache for demo purposes
            return self.cache[table_id]
            
        url = f"{self.base_url}/en/table/{table_id}"
        
        try:
            # Prepare request
            json_data = json.dumps(query).encode('utf-8')
            req = urllib.request.Request(url, data=json_data, headers={'Content-Type': 'application/json'})
            
            # Execute request
            with urllib.request.urlopen(req) as response:
                if response.status == 200:
                    response_body = response.read().decode('utf-8')
                    # Sanitize JSON-stat2 response if needed
                    # Sometimes SSB returns nan/null which python json handles okay
                    data = json.loads(response_body)
                    
                    if use_cache:
                        self.cache[table_id] = data
                        
                    return data
                else:
                    logger.error(f"Error querying table {table_id}: Status {response.status}")
                    return None
                    
        except urllib.error.HTTPError as e:
            logger.error(f"HTTP Error querying table {table_id}: {e.code} {e.reason}")
            # Try to read error body
            try:
                err_body = e.read().decode()
                logger.error(f"Response: {err_body}")
            except:
                pass
            return None
        except Exception as e:
            logger.error(f"Error querying table {table_id}: {e}")
            return None
    
    def get_household_budget_data(self, 
                                   year: str = "2022",
                                   categories: Optional[List[str]] = None,
                                   nowcast: bool = True) -> Dict:
        """
        Convenience method for household budget survey (Table 10235)
        
        Args:
            year: Year of data (default: "2022" - recent available year)
            categories: List of spending categories to retrieve
        
        Returns:
            Household budget data (optionally nowcasted to present day)
        """
        table_id = "14100"
        
        # 1. Fetch Baseline Data (2022)
        print(f"📉 Fetching Baseline Data ({year})...")
        
        # Query structure for SSB Table 14100 (2022 Survey)
        # Variables: VareTjenesteGruppe (categories), ContentsCode, Tid (year)
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
                "code": "VareTjenesteGruppe",
                "selection": {
                    "filter": "item",
                    "values": categories
                }
            })
        else:
            # Get main spending categories (top level: 01-12)
            # Codes for 14100 are similar (COICOP)
            query["query"].insert(0, {
                "code": "VareTjenesteGruppe",
                "selection": {
                    "filter": "item",
                    "values": ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"]
                }
            })
        
        baseline_data = self.query_table(table_id, query)
        
        if not nowcast:
            return baseline_data
            
        # 2. Scientific Nowcasting (Apply Live CPI)
        try:
             print("⚡ Running Nowcasting Engine (2022 -> 2025)...")
             cpi_data = self.get_cpi_adjustments()
             if not cpi_data:
                 print("⚠️ CPI data unavailable, returning baseline.")
                 return baseline_data
                 
             # Deep copy to avoid mutating cache if we were using a shared object
             # But query_table returns a new dict from json most likely
             nowcasted_data = json.loads(json.dumps(baseline_data)) 
             
             # Apply multipliers to values
             # We need to parse strict JSON-stat2 structure which is complex to mutate in-place.
             # Instead, we'll let the parser handle the raw data, AND we'll attach the CPI multipliers
             # so the parsing logic can apply them.
             
             # HACK: Attach multipliers to the 'extension' field so parse_household_data can use them
             nowcasted_data['extension']['nowcast_multipliers'] = cpi_data
             
             return nowcasted_data
             
        except Exception as e:
            print(f"❌ Nowcasting failed: {e}")
            return baseline_data

    def get_cpi_adjustments(self) -> Dict[str, float]:
        """
        Fetch latest CPI data (Table 11117) to calculate 2022->Today multipliers.
        Returns: Dict of sector multipliers (e.g. {'01': 1.15, '04': 1.12})
        """
        # Table 11117: CPI by sector (Delivery sectors) is good, but 03013 is standard COICOP
        # Let's use 03013 because it maps 1:1 to the budget categories (01, 02, etc.)
        table_id = "03013" 
        
        # We need 2022 Average vs Latest Month (e.g., 2025M11)
        # 2022 Average Index for "Total" was approx 122.0 (referenced to 2015=100)
        # We will fetch 2022 annual and 2025 latest
        
        query = {
            "query": [
                {
                    "code": "ContentsCode",
                    "selection": {
                        "filter": "item",
                        "values": ["KpiIndMnd"] # Strictly Index (2015=100)
                    }
                },
                {
                    "code": "Konsumgrp",
                    "selection": {
                        "filter": "item",
                        "values": ["TOTAL", "01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"]
                    }
                },
                {
                    "code": "Tid",
                    "selection": {
                        "filter": "top",
                        "values": ["1"] # Latest month
                    }
                }
            ],
            "response": {"format": "json-stat2"}
        }
        
        # We also need the REFERENCE index (2022 Average).
        # Hardcoding 2022 Annual Averages to save a second API call and complexity.
        # Source: SSB Table 03013 (2015=100) - Year 2022
        ref_2022 = {
            "TOTAL": 122.7,
            "01": 116.5, # Food
            "02": 119.2, # Alcohol
            "03": 108.4, # Clothing
            "04": 133.6, # Housing (High due to electricity)
            "05": 121.3, # Furnishings
            "06": 113.8, # Health
            "07": 119.5, # Transport
            "08": 111.2, # Communication
            "09": 118.9, # Recreation
            "10": 120.5, # Education
            "11": 126.8, # Restaurants
            "12": 114.7  # Misc
        }
        
        latest_data = self.query_table(table_id, query, use_cache=False) # Always live
        
        multipliers = {}
        
        if latest_data:
            # Parse latest indices
            # Structure: value array maps to Konsumgrp dimension
            try:
                values = latest_data['value']
                # Indices in 'value' correspond to order in Konsumgrp category index
                # We need to map them back.
                
                dim = latest_data['dimension']['Konsumgrp']
                indices = dim['category']['index'] # {"TOTAL": 0, "01": 1...}
                
                # Fetch Time label to know which month we got
                time_lbl = list(latest_data['dimension']['Tid']['category']['label'].values())[0]
                print(f"   Using Live CPI Reference: {time_lbl}")
                
                for code, idx in indices.items():
                    if idx < len(values):
                        current_index = values[idx]
                        baseline_index = ref_2022.get(code, 122.7) # Fallback to total
                        
                        multiplier = current_index / baseline_index
                        multipliers[code] = multiplier
                        # print(f"   Sector {code}: {current_index} / {baseline_index} = {multiplier:.3f}x")
                        
                return multipliers
                
            except Exception as e:
                print(f"Error parsing CPI data: {e}")
                
        return {} # Fallback to empty (no adjustment)

    def get_inflation_history(self, categories: List[str], months: int = 24) -> Dict[str, Any]:
        """
        Fetch historical CPI data for trend analysis.
        Args:
            categories: List of category codes (e.g. ["TOTAL", "01"])
            months: Number of months to look back
        Returns:
            Dict with dates and values for charting
        """
        table_id = "03013"
        
        # Query for last N months
        query = {
            "query": [
                {
                    "code": "ContentsCode",
                    "selection": {
                        "filter": "item",
                        "values": ["KpiIndMnd"] # Index
                    }
                },
                {
                    "code": "Konsumgrp",
                    "selection": {
                        "filter": "item",
                        "values": categories
                    }
                },
                {
                    "code": "Tid",
                    "selection": {
                        "filter": "top",
                        "values": [str(months)]
                    }
                }
            ],
            "response": {"format": "json-stat2"}
        }
        
        try:
            data = self.query_table(table_id, query)
            if not data:
                return {}
                
            # Parse response
            dimension = data.get('dimension', {})
            value = data.get('value', [])
            
            # Get Dates
            tid_dim = dimension.get('Tid', {})
            tid_index = tid_dim.get('category', {}).get('index', {})
            tid_labels = tid_dim.get('category', {}).get('label', {})
            
            # Sort dates by index
            dates = sorted(tid_index.items(), key=lambda x: x[1])
            date_labels = [tid_labels.get(d[0], d[0]) for d in dates]
            
            # Get Categories
            cat_dim = dimension.get('Konsumgrp', {})
            cat_index = cat_dim.get('category', {}).get('index', {})
            cat_labels = cat_dim.get('category', {}).get('label', {})
            
            result = {
                "dates": date_labels,
                "series": []
            }
            
            # Build series for each category
            for cat_code in categories:
                label = cat_labels.get(cat_code, cat_code)
                cat_idx = cat_index.get(cat_code)
                
                if cat_idx is None:
                    continue
                    
                # In JSON-stat, values are flattened.
                # Dimensionality: ContentsCode(1) * Categories(C) * Time(T)
                # If we requested multiple categories, we need to stride correctly.
                # Helper: usually stride is Last Dimension moves fastest.
                # Order in query: ContentsCode, Konsumgrp, Tid
                # BUT JSON-stat response 'id' list tells the order.
                
                ids = data.get('id', [])
                # We need to know the size of each dimension to index correct
                size = data.get('size', [])
                
                # Manual indexing fallback is tricky without a library.
                # Let's trust the 'value' list is ordered by the Cartesian product of dimensions in 'id'.
                # E.g. Konsumgrp, ContentsCode, Tid
                
                # Simplified approach: Iterate and pick values
                # If API output order is Konsumgrp -> Tid
                
                series_data = []
                
                # Calculate stride/offset logic is complex. 
                # Alternative: Use simple loop if we assume consistent return order.
                # For safety, let's extract based on known structure if possible or just map indices.
                
                # Let's try to map strictly using indices.
                # value_index = cat_idx * num_months + time_idx (if Cat is outer, Time is inner)
                # Let's check 'id' order
                
                time_size = len(dates)
                
                # Determine dimension order
                try:
                    cat_dim_pos = ids.index("Konsumgrp")
                    time_dim_pos = ids.index("Tid")
                    
                    # If Cat is before Time
                    if cat_dim_pos < time_dim_pos:
                        start_idx = cat_idx * time_size
                        series_data = value[start_idx : start_idx + time_size]
                    else:
                        # Time is outer dimension... rare for time series but possible
                        series_data = []
                        for t_idx in range(time_size):
                            idx = t_idx * len(cat_index) + cat_idx
                            if idx < len(value):
                                series_data.append(value[idx])
                                
                    result["series"].append({
                        "name": label,
                        "code": cat_code,
                        "data": series_data
                    })
                    
                except ValueError:
                    pass
            
            return result
            
        except Exception as e:
            print(f"Error fetching inflation history: {e}")
            return {}
    
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
            
            # Get VareTjenesteGruppe categories (spending categories)
            # Note: dimension name might be "VareTjenesteGruppe" or just "commodity and service group" 
            # depending on API response format, but usually keyed by ID in json-stat2
            
            # Try to find the category dimension
            cat_dim_key = "VareTjenesteGruppe"
            if cat_dim_key not in dimension:
                # Fallback search if key is different
                for k in dimension.keys():
                    if k not in ["ContentsCode", "Tid"]:
                        cat_dim_key = k
                        break
            
            forbruk_dim = dimension.get(cat_dim_key, {})
            forbruk_category = forbruk_dim.get('category', {})
            forbruk_labels = forbruk_category.get('label', {})
            forbruk_index = forbruk_category.get('index', {})
            
            # Get year
            tid_dim = dimension.get('Tid', {})
            tid_category = tid_dim.get('category', {})
            years = list(tid_category.get('label', {}).values())
            year = years[0] if years else "Unknown"
            
            results = []
            
            # Check for Nowcast Multipliers
            multipliers = raw_data.get('extension', {}).get('nowcast_multipliers', {})
            total_inflation_factor = 1.0
            
            # Map each value to its category
            for category_code, category_label in forbruk_labels.items():
                # Find the index for this category
                idx = forbruk_index.get(category_code)
                if idx is not None and idx < len(value):
                    val = value[idx]
                    if val is not None:
                        # APPLY NOWCAST MULTIPLIER
                        # Category codes in 14100 are "01", "04" etc. matching CPI
                        # Some are "01.1", need to map to "01"
                        
                        sector_code = category_code.split('.')[0] # "01.1" -> "01"
                        multiplier = multipliers.get(sector_code, multipliers.get("TOTAL", 1.0))
                        
                        adjusted_val = val * multiplier
                        
                        results.append({
                            'category': category_label,
                            'category_code': category_code,
                            'value': adjusted_val, # NOWCASTED VALUE
                            'year': f"{year} (Nowcast)",
                            'raw_value': val,
                            'inflation_factor': multiplier,
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
    print("📊 Test 2: Query household budget data (Nowcast 2025)")
    # First get baseline
    baseline = api.get_household_budget_data(year="2022", nowcast=False)
    parsed_base = api.parse_household_data(baseline)
    base_food = next((item['value'] for item in parsed_base if "Food" in item['category']), 0)
    
    # Get Nowcast
    nowcast = api.get_household_budget_data(year="2022", nowcast=True)
    parsed_now = api.parse_household_data(nowcast)
    now_food = next((item['value'] for item in parsed_now if "Food" in item['category']), 0)
    
    if parsed_now:
        print(f"✅ Got household budget data")
        print(f"   Baseline Food (2022): {base_food:,.0f} NOK")
        print(f"   Nowcast Food (2025):  {now_food:,.0f} NOK")
        
        if now_food > base_food:
            print(f"   📈 Inflation Logic Working! (+{((now_food/base_food)-1)*100:.1f}%)")
        else:
            print("   ⚠️ No inflation detected (CPI fetch failed?)")
            
    else:
        print("❌ Failed to get data")
    
    print("\n✅ SSB API tests complete!")


if __name__ == "__main__":
    test_ssb_api()