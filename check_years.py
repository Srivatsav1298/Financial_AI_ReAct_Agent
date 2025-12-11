from src.utils.ssb_api import SSBApi
import json

def check_years():
    api = SSBApi()
    # Table 10235 is "Household budget survey, by consumption group"
    # We want to see available values for the "Tid" (Time) variable.
    metadata = api.get_table_metadata("10235")
    
    if metadata:
        variables = metadata.get('variables', [])
        for var in variables:
            if var.get('code') == 'Tid':
                print(f"Available Years: {var.get('values')}")
                return
    print("Could not find Time variable in metadata")

if __name__ == "__main__":
    check_years()
