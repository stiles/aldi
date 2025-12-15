import warnings
import re

# Suppress urllib3 SSL warnings before importing
warnings.filterwarnings('ignore', message='.*OpenSSL.*')
warnings.filterwarnings('ignore', category=DeprecationWarning)

import requests
import urllib3

# Disable all urllib3 warnings
urllib3.disable_warnings()

def get_api_key():
    """
    Extract the API key from Target's website.
    The key appears in the page's JavaScript configuration.
    """
    fallback_key = '9f36aeafbe60771e321a7cc95a78140772ab3e96'
    
    try:
        # Load a product page to get the key from the page source
        response = requests.get(
            'https://www.target.com/p/-/A-12945916',
            headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'},
            verify=False,
            timeout=10
        )
        
        # Look for the API key - it's embedded in the page's JavaScript
        # Common patterns where the key appears
        patterns = [
            r'apiKey["\']?\s*:\s*["\']([a-f0-9]{40})["\']',  # apiKey: "xxx"
            r'"key"\s*:\s*"([a-f0-9]{40})"',                  # "key": "xxx"
            r'key:\s*["\']([a-f0-9]{40})["\']',               # key: 'xxx'
            r'API_KEY["\']?\s*[:=]\s*["\']([a-f0-9]{40})["\']', # API_KEY = "xxx"
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, response.text, re.IGNORECASE)
            if matches:
                extracted_key = matches[0]
                if extracted_key == fallback_key:
                    print("✓ API key extracted from page (matches known key)")
                else:
                    print("✓ API key extracted from page (new key found)")
                return extracted_key
        
        # If no pattern matches, search for any 40-char hex string near "key" or "api"
        context_pattern = r'(?:key|api)[^a-f0-9]{0,50}([a-f0-9]{40})'
        matches = re.findall(context_pattern, response.text, re.IGNORECASE)
        if matches:
            extracted_key = matches[0]
            if extracted_key == fallback_key:
                print("✓ API key extracted from page (matches known key)")
            else:
                print("✓ API key extracted from page (new key found)")
            return extracted_key
        
        # Fallback to known working key
        print("⚠ Warning: Could not extract API key from page, using fallback")
        return fallback_key
        
    except Exception as e:
        print(f"⚠ Error extracting API key: {e}, using fallback")
        return fallback_key

# Headers
headers = {
    'accept': 'application/json',
    'accept-language': 'en-US,en;q=0.9',
    'origin': 'https://www.target.com',
    'priority': 'u=1, i',
    'referer': 'https://www.target.com/p/oscar-mayer-turkey-bacon-12oz/-/A-12945916',
    'sec-ch-ua': '"Google Chrome";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-site',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36',
}

# Get API key dynamically
print("Fetching API key...")
api_key = get_api_key()
print(f"Using API key: {api_key[:20]}...\n")

# Parameters
params = {
    'key': api_key,
    'tcin': '16636689',
    'is_bot': 'false',
    'store_id': '3251',
    'pricing_store_id': '3251',
    'has_pricing_store_id': 'true',
    'has_financing_options': 'true',
    'include_obsolete': 'true',
    'skip_personalized': 'true',
    'skip_variation_hierarchy': 'true',
    'channel': 'WEB',
    'page': '/p/A-16636689',
}

# Make request
response = requests.get(
    'https://redsky.target.com/redsky_aggregations/v1/web/pdp_client_v1',
    params=params,
    headers=headers,
    verify=False,
)

print(f"Status code: {response.status_code}\n")

if response.status_code == 200:
    data = response.json()
    
    if 'data' in data and 'product' in data['data']:
        product = data['data']['product']
        item = product.get('item', {})
        price_data = product.get('price', {})
        nutrition = item.get('enrichment', {}).get('nutrition_facts', {})
        
        # Build product data object
        product_data = {
            # Basic product info
            'tcin': product.get('tcin'),
            'title': item.get('product_description', {}).get('title'),
            'brand': item.get('primary_brand', {}).get('name'),
            'barcode': item.get('primary_barcode'),
            'dpci': item.get('dpci'),
            
            # Price info
            'current_price': price_data.get('formatted_current_price'),
            'reg_price': price_data.get('formatted_comparison_price'),
            'price_type': price_data.get('formatted_current_price_type'),
            'unit_price': price_data.get('formatted_unit_price'),
            'save_amount': price_data.get('save_dollar'),
            'save_percent': price_data.get('save_percent'),
            
            # Category
            'category': product.get('category', {}).get('name'),
            'department': item.get('merchandise_classification', {}).get('department_name'),
            
            # Product details
            'description': item.get('product_description', {}).get('downstream_description'),
            'is_grocery': item.get('is_fresh_grocery'),
            
            # Nutrition facts
            'nutrition': {}
        }
        
        # Extract nutrition information
        if nutrition:
            product_data['nutrition']['ingredients'] = nutrition.get('ingredients')
            product_data['nutrition']['warning'] = nutrition.get('warning')
            
            # Get nutrient details from first prepared value
            prepared_list = nutrition.get('value_prepared_list', [])
            if prepared_list:
                prep = prepared_list[0]
                product_data['nutrition']['serving_size'] = f"{prep.get('serving_size')} {prep.get('serving_size_unit_of_measurement')}"
                product_data['nutrition']['servings_per_container'] = prep.get('servings_per_container')
                
                # Extract individual nutrients
                nutrients = {}
                for nutrient in prep.get('nutrients', []):
                    name = nutrient['name']
                    quantity = nutrient.get('quantity')
                    unit = nutrient.get('unit_of_measurement', '')
                    percentage = nutrient.get('percentage')
                    
                    nutrients[name] = {
                        'quantity': quantity,
                        'unit': unit,
                        'daily_value_pct': percentage
                    }
                
                product_data['nutrition']['nutrients'] = nutrients
        
        # Print formatted output
        print("=" * 60)
        print("PRODUCT INFORMATION")
        print("=" * 60)
        print(f"Title: {product_data['title']}")
        print(f"Brand: {product_data['brand']}")
        print(f"TCIN: {product_data['tcin']}")
        print(f"Barcode: {product_data['barcode']}")
        print(f"Category: {product_data['category']} / {product_data['department']}")
        
        print(f"\n{'PRICE':}")
        print(f"Current: {product_data['current_price']} ({product_data['price_type']})")
        print(f"Regular: {product_data['reg_price']}")
        if product_data['save_amount']:
            print(f"Savings: ${product_data['save_amount']:.2f} ({product_data['save_percent']:.0f}% off)")
        print(f"Unit Price: {product_data['unit_price']}")
        
        if product_data['nutrition']:
            print(f"\n{'NUTRITION FACTS':}")
            print(f"Serving Size: {product_data['nutrition'].get('serving_size', 'N/A')}")
            print(f"Servings: {product_data['nutrition'].get('servings_per_container', 'N/A')}")
            
            if 'nutrients' in product_data['nutrition']:
                print(f"\nNutrients per serving:")
                for name, info in product_data['nutrition']['nutrients'].items():
                    value = f"{info['quantity']}{info['unit']}"
                    if info['daily_value_pct']:
                        value += f" ({info['daily_value_pct']}% DV)"
                    print(f"  {name}: {value}")
            
            if product_data['nutrition'].get('warning'):
                print(f"\nAllergy Warning: {product_data['nutrition']['warning']}")
        
        print("\n" + "=" * 60)
        
        # Return the data object
        import json
        print("\nData object (JSON):")
        print(json.dumps(product_data, indent=2))
        
    else:
        print("No product data found in response")
else:
    print(f"Error: {response.json()}")
