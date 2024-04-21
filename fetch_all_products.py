import os
import logging
import requests
import pandas as pd
import boto3
from tqdm.auto import tqdm
from botocore.exceptions import NoCredentialsError, ClientError

today = pd.Timestamp("today").strftime("%Y_%m_%d")

def create_s3_client(profile_name=None):
    """ Create an S3 client instance with the specified profile or default environment credentials. """
    if profile_name:
        session = boto3.Session(profile_name=profile_name)
    else:
        session = boto3.Session()
    s3_client = session.client('s3')
    return s3_client

def fetch_all_products():
    """ Fetches all products from the ALDI API with pagination handling. """
    headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'en-US,en;q=0.9',
        'origin': 'https://new.aldi.us',
        'sec-ch-ua': '"Google Chrome";v="123", "Not:A-Brand";v="8", "Chromium";v="123"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    }
    base_url = 'https://api.aldi.us/v1/catalog-search-product-offers'
    params = {
        'currency': 'USD',
        'serviceType': 'pickup',
        'page[limit]': 48,
        'page[offset]': 0,
        'sort': 'relevance',
        'merchantReference': '479-022'
    }

    response = requests.get(base_url, headers=headers, params=params)
    response.raise_for_status()
    data = response.json()

    pagination = data['data'][0]['attributes']['pagination']
    max_page = pagination['maxPage']
    products = []

    for page in tqdm(range(1, max_page + 1), desc="Fetching products"):
        params['page[offset]'] = (page - 1) * 48
        response = requests.get(base_url, headers=headers, params=params)
        page_data = response.json()

        for product in page_data['data'][0]['attributes']['catalogSearchProductOfferResults']:
            products.append({
                'sku': product['productConcreteSku'],
                'name': product['name'],
                'brand_name': product['brandName'],
                'price_unit': product['comparisonPriceUnit'],
                'slug': product['urlSlugText'],
                'formatted_price': product.get('prices', [{}])[0].get('formattedPrice', 'N/A'),
                'snap_eligible': product['usaSnapEligible']
            })

    return pd.DataFrame(products)

def fetch_product_details(sku):
    """ Fetch detailed product information based on SKU. """
    headers = {
        'sec-ch-ua': '"Google Chrome";v="123", "Not:A-Brand";v="8", "Chromium";v="123"',
        'Accept': 'application/json, text/plain, */*',
        'Referer': '',
        'sec-ch-ua-mobile': '?0',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
        'sec-ch-ua-platform': '"macOS"',
    }
    product_details_url = f'https://api.aldi.us/v1/products/{sku}'
    product_params = {
        'servicePoint': '479-022',
        'serviceType': 'pickup',
    }
    
    response = requests.get(product_details_url, headers=headers, params=product_params)
    response.raise_for_status()
    product_data = response.json()['data']

    return {
        'sku': product_data['sku'],
        'description': product_data['description'],
        'categories': ', '.join([cat['name'] for cat in product_data['categories']]),
        'country_origin': product_data['countryOrigin'],
        'image_url': product_data['assets'][0]['url'] if product_data['assets'] else None,
        'warning_code': product_data['warnings'][0]['key'] if product_data['warnings'] else None,
        'warning_desc': product_data['warnings'][0]['message'] if product_data['warnings'] else None
    }

def upload_file_to_s3(file_name, bucket, object_name, profile_name=None):
    """ Uploads a file to an S3 bucket using the specified profile or environment credentials. """
    s3_client = create_s3_client(profile_name)
    try:
        s3_client.upload_file(file_name, bucket, object_name)
    except NoCredentialsError:
        logging.error("Credentials not available")
        return False
    except ClientError as e:
        logging.error(e)
        return False
    return True

def main():
    profile_name = "haekeo" if 'AWS_ACCESS_KEY_ID' not in os.environ else None
    
    all_products_df = fetch_all_products()
    detailed_info = []
    for sku in tqdm(all_products_df['sku'], desc="Hydrating products"):
        details = fetch_product_details(sku)
        detailed_info.append(details)

    detailed_df = pd.DataFrame(detailed_info)
    full_df = all_products_df.merge(detailed_df, on='sku', how='left')

    csv_file = f'aldi_products_detailed_{today}.csv'
    json_file = f'aldi_products_detailed_{today}.json'

    full_df.to_csv(csv_file, index=False)
    full_df.to_json(json_file, indent=4, orient='records')

    # Upload to S3
    upload_file_to_s3(csv_file, 'stilesdata.com', 'aldi/aldi_products_detailed_latest.csv', profile_name=profile_name)
    upload_file_to_s3(json_file, 'stilesdata.com', 'aldi/aldi_products_detailed_latest.json', profile_name=profile_name)

    print("Data saved and uploaded to S3. Process completed.")

if __name__ == "__main__":
    main()