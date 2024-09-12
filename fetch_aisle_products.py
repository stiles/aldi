import requests
from bs4 import BeautifulSoup
import pandas as pd
from io import StringIO
import boto3
from datetime import datetime

def fetch_data(url):
    response = requests.get(url)
    response.raise_for_status()  # Raises an error for bad responses
    return BeautifulSoup(response.text, 'html.parser')

def parse_products(soup, week_date):
    products = []
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
            product_price = (price_value_tag.get_text(strip=True) if price_value_tag else "") + \
                            (price_decimal_tag.get_text(strip=True) if price_decimal_tag else "") + \
                            (asterisk_tag.get_text(strip=True) if asterisk_tag else "")
            
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
    archive_key = 'aldi/aldi_finds_latest.csv'

    # Try to load the existing archive
    try:
        obj = s3_resource.Object(bucket_name, archive_key)
        archive_data = obj.get()['Body'].read().decode('utf-8')
        df_archive = pd.read_csv(StringIO(archive_data))
    except s3_resource.meta.client.exceptions.NoSuchKey:
        df_archive = pd.DataFrame()

    current_finds_url = "https://www.aldi.us/weekly-specials/this-weeks-aldi-finds"
    upcoming_finds_url = "https://www.aldi.us/weekly-specials/upcoming-aldi-finds/"
    
    current_week_soup = fetch_data(current_finds_url)
    upcoming_week_soup = fetch_data(upcoming_finds_url)
    
    week_date_current = current_week_soup.find("h2").get_text(strip=True)
    week_date_upcoming = upcoming_week_soup.find("h2").get_text(strip=True)
    
    products_current = parse_products(current_week_soup, week_date_current)
    products_upcoming = parse_products(upcoming_week_soup, week_date_upcoming)
    
    df_current = pd.DataFrame(products_current)
    df_upcoming = pd.DataFrame(products_upcoming)
    
    df_new = pd.concat([df_current, df_upcoming]).drop_duplicates()
    df_new['week_start'] = df_new['week_date'].str.split(' - ', expand=True)[0]
    df_new['week_end'] = df_new['week_date'].str.split(' - ', expand=True)[1]
    df_new['price_clean'] = pd.to_numeric(df_new['price'].str.replace('*', '').str.replace('$', ''), errors='coerce')

    # Combine with archive
    df_combined = pd.concat([df_archive, df_new]).drop_duplicates(subset=['week_date', 'link'])

    # Saving to CSV and JSON
    csv_buffer_new = StringIO()
    json_buffer_new = StringIO()
    csv_buffer_archive = StringIO()
    json_buffer_archive = StringIO()
    df_new.to_csv(csv_buffer_new, index=False)
    df_new.to_json(json_buffer_new, orient='records', lines=True)
    df_combined.to_csv(csv_buffer_archive, index=False)
    df_combined.to_json(json_buffer_archive, orient='records', lines=True)
    
    # Upload to S3
    new_csv_key = f'aldi/{datetime.now().strftime("%Y-%m-%d")}_aldi_finds.csv'
    new_json_key = f'aldi/{datetime.now().strftime("%Y-%m-%d")}_aldi_finds.json'
    archive_csv_key = 'aldi/aldi_finds_latest.csv'
    archive_json_key = 'aldi/aldi_finds_latest.json'
    
    s3_resource.Object(bucket_name, new_csv_key).put(Body=csv_buffer_new.getvalue())
    s3_resource.Object(bucket_name, new_json_key).put(Body=json_buffer_new.getvalue())
    s3_resource.Object(bucket_name, archive_csv_key).put(Body=csv_buffer_archive.getvalue())
    s3_resource.Object(bucket_name, archive_json_key).put(Body=json_buffer_archive.getvalue())

    print("Upload completed successfully.")

if __name__ == "__main__":
    main()
