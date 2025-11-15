"""
LangChain tools for interacting with SSB (Statistics Norway) data
"""

from langchain.tools import tool
from typing import Dict, List, Optional
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))
from utils.ssb_api import SSBApi

# Initialize SSB API
ssb = SSBApi()

# Most recent available year in SSB data
DEFAULT_YEAR = "2012"


@tool
def get_average_spending_by_category(category: str, year: str = DEFAULT_YEAR) -> str:
    """
    Get average Norwegian household spending for a specific category.
    
    Args:
        category: Spending category (e.g., "housing", "food", "transport", "entertainment")
        year: Year of data (default: "2012")
    
    Returns:
        String describing the average spending amount
    
    Example:
        get_average_spending_by_category("housing", "2012")
        Returns: "Norwegian households spend an average of 11,332 NOK per month on housing"
    """
    
    # Mapping of common terms to SSB Forbruksundersok category codes
    # Based on actual SSB Table 10235 structure
    category_mapping = {
        "food": ["01"],  # Food and non-alcoholic beverages
        "alcohol": ["02"],  # Alcoholic beverages and tobacco
        "tobacco": ["02"],
        "clothing": ["03"],  # Clothing and footwear
        "clothes": ["03"],
        "housing": ["04"],  # Housing, water, electricity, gas and other fuels
        "home": ["04"],
        "furnishings": ["05"],  # Furnishings, household equipment
        "furniture": ["05"],
        "health": ["06"],  # Health
        "medical": ["06"],
        "transport": ["07"],  # Transport
        "transportation": ["07"],
        "communication": ["08"],  # Communication
        "phone": ["08"],
        "entertainment": ["09"],  # Recreation and culture
        "recreation": ["09"],
        "culture": ["09"],
        "education": ["10"],  # Education
        "school": ["10"],
        "restaurants": ["11"],  # Restaurants and hotels
        "hotels": ["11"],
        "dining": ["11"],
        "other": ["12"],  # Miscellaneous goods and services
        "miscellaneous": ["12"],
    }
    
    # Normalize category input
    category_lower = category.lower()
    
    # Find matching category
    ssb_codes = category_mapping.get(category_lower)
    
    if not ssb_codes:
        available = ', '.join(sorted(set(category_mapping.keys())))
        return f"Category '{category}' not recognized. Available categories: {available}"
    
    try:
        # Query SSB
        data = ssb.get_household_budget_data(year=year, categories=ssb_codes)
        
        if not data:
            return f"No data available for {category} in {year}"
        
        # Parse data
        parsed = ssb.parse_household_data(data)
        
        if not parsed:
            return f"Could not parse data for {category}"
        
        # Sum up all values in this category
        total_annual = sum(item['value'] for item in parsed if item['value'] is not None)
        total_monthly = total_annual / 12
        
        # Get category name from results
        category_name = parsed[0]['category'] if parsed else category
        
        # Format response
        return (f"Norwegian households spend an average of {total_monthly:,.0f} NOK per month "
                f"on {category_name} ({total_annual:,.0f} NOK per year). "
                f"Source: Statistics Norway Household Budget Survey {year}, Table 10235. "
                f"URL: https://www.ssb.no/statbank/table/10235")
    
    except Exception as e:
        return f"Error retrieving data: {str(e)}"


@tool
def compare_spending_categories(category1: str, category2: str, year: str = DEFAULT_YEAR) -> str:
    """
    Compare spending between two categories.
    
    Args:
        category1: First spending category
        category2: Second spending category
        year: Year of data (default: "2012")
    
    Returns:
        String comparing the two categories
    
    Example:
        compare_spending_categories("housing", "food", "2012")
    """
    
    # Get data for both categories directly
    category_mapping = {
        "food": "01", "alcohol": "02", "tobacco": "02", "clothing": "03", 
        "clothes": "03", "housing": "04", "home": "04", "furnishings": "05",
        "furniture": "05", "health": "06", "medical": "06", "transport": "07",
        "transportation": "07", "communication": "08", "phone": "08",
        "entertainment": "09", "recreation": "09", "culture": "09",
        "education": "10", "school": "10", "restaurants": "11", "hotels": "11",
        "dining": "11", "other": "12", "miscellaneous": "12"
    }
    
    code1 = category_mapping.get(category1.lower())
    code2 = category_mapping.get(category2.lower())
    
    if not code1 or not code2:
        return f"One or both categories not recognized: {category1}, {category2}"
    
    try:
        # Get both datasets
        data = ssb.get_household_budget_data(year=year, categories=[code1, code2])
        
        if not data:
            return f"No data available for comparison in {year}"
        
        parsed = ssb.parse_household_data(data)
        
        if len(parsed) < 2:
            return "Could not get data for both categories"
        
        # Extract amounts
        amounts = {}
        for item in parsed:
            code = item['category_code']
            monthly = item['value'] / 12
            amounts[code] = {
                'amount': monthly,
                'annual': item['value'],
                'name': item['category']
            }
        
        amt1 = amounts.get(code1)
        amt2 = amounts.get(code2)
        
        if not amt1 or not amt2:
            return "Could not parse amounts for comparison"
        
        # Calculate ratio
        if amt2['amount'] > 0:
            ratio = amt1['amount'] / amt2['amount']
            
            if ratio > 1:
                return (f"{amt1['name']} ({amt1['amount']:,.0f} NOK/month) costs "
                       f"{ratio:.1f}x more than {amt2['name']} ({amt2['amount']:,.0f} NOK/month). "
                       f"Source: SSB Table 10235 ({year})")
            else:
                ratio = amt2['amount'] / amt1['amount']
                return (f"{amt2['name']} ({amt2['amount']:,.0f} NOK/month) costs "
                       f"{ratio:.1f}x more than {amt1['name']} ({amt1['amount']:,.0f} NOK/month). "
                       f"Source: SSB Table 10235 ({year})")
        else:
            return "Could not compare - one category has zero spending"
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"Error comparing categories: {str(e)}"


@tool
def get_total_household_spending(year: str = DEFAULT_YEAR) -> str:
    """
    Get total average household spending across all categories.
    
    Args:
        year: Year of data (default: "2012")
    
    Returns:
        String with total spending information
    """
    
    try:
        # Query all main categories
        data = ssb.get_household_budget_data(year=year)
        
        if not data:
            return f"No data available for {year}"
        
        # Parse data
        parsed = ssb.parse_household_data(data)
        
        if not parsed:
            return "Could not parse household data"
        
        # Calculate total
        total_annual = sum(item['value'] for item in parsed if item['value'] is not None)
        total_monthly = total_annual / 12
        
        # Count categories
        num_categories = len(parsed)
        
        return (f"Norwegian households spend an average of {total_monthly:,.0f} NOK per month "
                f"({total_annual:,.0f} NOK per year) across {num_categories} main spending categories. "
                f"Source: Statistics Norway Household Budget Survey {year}, Table 10235")
    
    except Exception as e:
        return f"Error calculating total spending: {str(e)}"


# List of all tools for easy import
ssb_tools = [
    get_average_spending_by_category,
    compare_spending_categories,
    get_total_household_spending
]


def test_tools():
    """Test the SSB tools"""
    print("🧪 Testing SSB Tools\n")
    
    print("📊 Test 1: Get housing spending")
    result = get_average_spending_by_category.invoke({"category": "housing", "year": "2012"})
    print(f"Result: {result}\n")
    
    print("📊 Test 2: Get food spending")
    result = get_average_spending_by_category.invoke({"category": "food", "year": "2012"})
    print(f"Result: {result}\n")
    
    print("📊 Test 3: Compare housing and food")
    result = compare_spending_categories.invoke({
        "category1": "housing", 
        "category2": "food",
        "year": "2012"
    })
    print(f"Result: {result}\n")
    
    print("📊 Test 4: Get total spending")
    result = get_total_household_spending.invoke({"year": "2012"})
    print(f"Result: {result}\n")
    
    print("✅ All tool tests complete!")


if __name__ == "__main__":
    test_tools()