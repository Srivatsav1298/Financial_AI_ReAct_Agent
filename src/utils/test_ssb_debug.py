import requests
import json

# Get table metadata to see what it wants
url = "https://data.ssb.no/api/v0/en/table/10235"
response = requests.get(url)

if response.status_code == 200:
    data = response.json()
    
    print("📊 Table 10235 Structure:\n")
    
    # Print each variable/dimension
    for var in data.get('variables', []):
        print(f"Variable: {var['code']}")
        print(f"  Name: {var['text']}")
        print(f"  Values: {var['values'][:10]}")  # First 10
        print(f"  Value texts: {var['valueTexts'][:10]}\n")
    
    # Save full metadata for inspection
    with open('table_10235_metadata.json', 'w') as f:
        json.dump(data, f, indent=2)
    
    print("✅ Saved full metadata to 'table_10235_metadata.json'")
else:
    print(f"❌ Error: {response.status_code}")