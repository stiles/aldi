#!/usr/bin/env python
# coding: utf-8

"""
Aldi 'finds' over time
Fetch historical data from the Wayback Machine
"""

import time
import boto3
import random
import requests
import pandas as pd
from tqdm import tqdm
from io import StringIO
from bs4 import BeautifulSoup
from datetime import datetime

# Headers for requests to the Wayback Machine
headers = {
    "accept": "application/json",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
}

# JSON endpoint that points to 'finds' snapshot files via the Internet Archive
url = "https://web.archive.org/cdx/search/cdx?url=https://www.aldi.us/weekly-specials/this-weeks-aldi-finds/&output=json&filter=statuscode:200&collapse=digest"

# Request the metadata file in JSON format
response = requests.get(url, headers=headers)
response.raise_for_status()
snapshots = response.json()

# Process the metadata to form a list of URLs
archive_df = pd.DataFrame(snapshots[1:], columns=snapshots[0])
archive_df['datetime'] = pd.to_datetime(archive_df['timestamp'], format='%Y%m%d%H%M%S')
archive_df = archive_df.sort_values('datetime', ascending=True).drop_duplicates('datetime', keep='last')

archive_df['url'] = "https://web.archive.org/web/" + archive_df['timestamp'] + "id_/" + archive_df['original']

# List of URLs to process
archive_urls = archive_df['url'].tolist()

def fetch_data(url):
    """Fetch and parse content from a single archived URL."""
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    response.raise_for_status()
    return BeautifulSoup(response.content, 'html.parser')

def parse_products(soup):
    """Parse product entries from a given BeautifulSoup object and return a list of data."""
    products = []
    week_date = soup.find("h2").get_text(strip=True) if soup.find("h2") else "Unknown Date"
    category_sections = soup.find_all("div", class_="tx-aldi-products")
    
    for section in category_sections:
        category_header = section.find_previous("h2", class_="subheader-blue")
        category = category_header.get_text(strip=True) if category_header else "No Category"
        
        for product in section.find_all("a", class_="box--wrapper ym-gl ym-g25"):
            description_tag = product.find("div", class_="box--description--header")
            parts = [desc.strip() for desc in description_tag.contents if isinstance(desc, str) and desc.strip()] if description_tag else [None, None]
            product_brand, product_description = parts if len(parts) == 2 else (None, None)
            
            price_value_tag = product.find("span", class_="box--value")
            price_decimal_tag = product.find("span", class_="box--decimal")
            asterisk_tag = product.find("span", class_="box--asterisk")
            product_price = "".join(filter(None, [
                price_value_tag.get_text(strip=True) if price_value_tag else "",
                price_decimal_tag.get_text(strip=True) if price_decimal_tag else "",
                asterisk_tag.get_text(strip=True) if asterisk_tag else ""
            ]))
            
            image_tag = product.find("img")
            product_image = image_tag['src'] if image_tag else None
            
            products.append({
                "week_date": week_date,
                "category": category,
                "brand": product_brand,
                "description": product_description,
                "price": product_price,
                "image": product_image,
                "link": "https://www.aldi.us" + product.get('href')
            })
    return products

def main():
    s3_resource = boto3.resource('s3')
    bucket_name = 'stilesdata.com'
    archive_key = 'aldi/aldi_finds_archive_wayback_machine.csv'

    all_products = []

    for url in tqdm(archive_urls, desc="Processing URLs"):
        soup = fetch_data(url)
        products = parse_products(soup)
        all_products.extend(products)
    
        # Be kind
        time_to_sleep = random.uniform(7, 12)
        time.sleep(time_to_sleep)

    # Convert list of dicts to DataFrame
    df = pd.DataFrame(all_products)
    df['price_clean'] = df['price'].str.extract(r'(\d+\.\d+)').astype(float)
    
    # Saving to CSV
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False)
    
    # Upload to S3
    s3_resource.Object(bucket_name, archive_key).put(Body=csv_buffer.getvalue())
    print("Upload completed successfully.")

if __name__ == "__main__":
    main()