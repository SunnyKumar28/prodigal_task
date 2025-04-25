import json

def extract_slugs(json_file_path):
    slugs = []
    try:
        with open(json_file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        
        # Data is a list of objects
        for obj in data:
            # Navigate to hits.items
            items = obj.get('data', {}).get('hits', {}).get('items', [])
            for item in items:
                slug = item.get('fields', {}).get('slug')
                if slug:
                    slugs.append(slug)
                
        return slugs
    
    except FileNotFoundError:
        print(f"Error: File '{json_file_path}' not found")
        return []
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in '{json_file_path}'")
        return []
    except UnicodeDecodeError:
        print(f"Error: Could not decode file with UTF-8 encoding. Trying alternative encoding...")
        try:
            with open(json_file_path, 'r', encoding='latin-1') as file:
                data = json.load(file)
            for obj in data:
                items = obj.get('data', {}).get('hits', {}).get('items', [])
                for item in items:
                    slug = item.get('fields', {}).get('slug')
                    if slug:
                        slugs.append(slug)
            return slugs
        except Exception as e:
            print(f"Error extracting slugs with alternative encoding: {str(e)}")
            return []
    except Exception as e:
        print(f"Error extracting slugs: {str(e)}")
        return []

def generate_urls(slugs):
    base_url = "https://www.myscheme.gov.in/schemes/"
    return [base_url + slug for slug in slugs]

if __name__ == "__main__":
    json_file_path = r"C:\Users\nites\OneDrive\Desktop\Scrapping\Sunny\all2.json"
    
    slugs = extract_slugs(json_file_path)
    
    if slugs:
        print("Extracted slugs:")
        for slug in slugs:
            print(slug)
        
        print("\nGenerated URLs:")
        urls = generate_urls(slugs)
        for url in urls:
            print(url)
    else:
        print("No slugs extracted")