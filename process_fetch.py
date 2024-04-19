import os
import requests
from bs4 import BeautifulSoup
import pandas as pd
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
            products.append({
                "week_date": week_date,
                "category": category,
                "brand": (parts := [desc.strip() for desc in (description_tag := product.find("div", class_="box--description--header")).contents if isinstance(desc, str) and desc.strip()])[0] if parts else '',
                "description": parts[1] if len(parts) > 1 else '',
                "price": (price_value_tag := product.find("span", class_="box--value")).get_text(strip=True) if price_value_tag else '' + 
                         (price_decimal_tag := product.find("span", class_="box--decimal")).get_text(strip=True) if price_decimal_tag else '' + 
                         (product.find("span", class_="box--asterisk")).get_text(strip=True) if price_value_tag else '',
                "image": (image_tag := product.find("img"))['src'] if image_tag else None,
                "link": "https://www.aldi.us" + product.get('href')
            })
    return products

def main():
    current_finds_url = "https://www.aldi.us/weekly-specials/this-weeks-aldi-finds"
    upcoming_finds_url = "https://www.aldi.us/weekly-specials/upcoming-aldi-finds/"
    
    current_week_soup = fetch_data(current_finds_url)
    upcoming_week_soup = fetch_data(upcoming_finds_url)
    
    # Assuming the first <h2> tag on the page contains the week date string
    week_date_current = current_week_soup.find("h2").get_text(strip=True)
    week_date_upcoming = upcoming_week_soup.find("h2").get_text(strip=True)
    
    products_current = parse_products(current_week_soup, week_date_current)
    products_upcoming = parse_products(upcoming_week_soup, week_date_upcoming)
    
    df_current = pd.DataFrame(products_current)
    df_upcoming = pd.DataFrame(products_upcoming)
    
    df = pd.concat([df_current, df_upcoming]).drop_duplicates()
    df['week_start'] = pd.to_datetime(df['week_date'].str.split(' - ', expand=True)[0]).astype(str)
    df['week_end'] = pd.to_datetime(df['week_date'].str.split(' - ', expand=True)[1]).astype(str)
    df['price_clean'] = df['price'].str.replace('*', '').str.replace('$', '').astype(float)
    
    # Saving to CSV
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False)
    
    # Upload to S3
    s3_resource = boto3.resource('s3')
    s3_resource.Object('stilesdata.com', f'aldi/{datetime.now().strftime("%Y-%m-%d")}_aldi_finds.csv').put(Body=csv_buffer.getvalue())

    print("Upload completed successfully.")

if __name__ == "__main__":
    main()