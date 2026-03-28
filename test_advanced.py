#!/usr/bin/env python
"""Test advanced tools directly"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent / "src"))

from tools.advanced_tools import analyze_budget_health, get_norwegian_averages

print("🧪 Testing Advanced Tools\n")

# Test 1: Get Norwegian averages
print("📊 Test 1: Norwegian Averages (with Nowcast)")
averages = get_norwegian_averages()
if averages:
    print(f"✅ Got averages for {len(averages)} categories")
    for cat, amount in list(averages.items())[:5]:
        print(f"   {cat}: {amount:,.0f} NOK/month")
else:
    print("❌ Failed to get averages")
print()

# Test 2: Budget health analysis
print("💊 Test 2: Budget Health Analysis")
test_income = 45000
test_expenses = {
    'housing': 15000,
    'food': 8000,
    'transport': 6000,
    'entertainment': 3000,
    'other': 5000
}

try:
    result = analyze_budget_health(
        monthly_income=test_income,
        housing=test_expenses['housing'],
        food=test_expenses['food'],
        transport=test_expenses['transport'],
        entertainment=test_expenses['entertainment'],
        other=test_expenses['other']
    )
    print("✅ Budget analysis completed")
    print(f"Result type: {type(result)}")
    if isinstance(result, dict):
        print(f"Keys: {result.keys()}")
        if 'health_score' in result:
            print(f"Health Score: {result['health_score']}/100")
        if 'health_category' in result:
            print(f"Category: {result['health_category']}")
    else:
        print(f"Result: {str(result)[:200]}")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n✅ Advanced tools test complete!")
