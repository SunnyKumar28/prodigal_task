import json
import csv
import sys

def json_to_csv(json_file, csv_file):
    try:
        # Read JSON data
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Check if data has the expected structure
        if 'listings' in data and isinstance(data['listings'], list):
            # Get all unique fieldnames from the listings
            fieldnames = set()
            for item in data['listings']:
                fieldnames.update(item.keys())
            
            # Write to CSV
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data['listings'])
            
            print(f"Successfully converted {json_file} to {csv_file}")
            print(f"Found {len(data['listings'])} records with {len(fieldnames)} columns")
        else:
            print("JSON structure not supported. Expected object with 'listings' array.")
    
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python json_to_csv.py <input.json> <output.csv>")
    else:
        json_to_csv(sys.argv[1], sys.argv[2])