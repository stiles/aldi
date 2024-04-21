# ALDI product data collection

This project automates the scraping and storing at regular intervals of grocery product information from ALDI's website, including the full inventory and items included in the supermarket chain's ["Aisle of Shame" or "finds"](https://www.aldi.us/weekly-specials/this-weeks-aldi-finds/) category. It was inspired by Parija Kavilanz's [CNN story](https://www.cnn.com/2024/04/19/business/aldi-aisle-of-shame-fans/index.html). 

*The project — and its documentation — are still a work in progress.*

## Project overview

The project utilizes two scripts: `fetch_all_products.py` for capturing the full product catalog using the supermarket's API and `fetch_aisle_products.py` for weekly updates from the "[finds](https://www.aldi.us/weekly-specials/this-weeks-aldi-finds/)" pages. It's updated weekly and snapshots of past files are stored on AWS S3. 

### How to run the scripts

1. **Prerequisites**:
   - Python 3.8+ installed on your machine.
   - Necessary Python packages: `requests`, `pandas`, `tqdm` for full catalog collection; `beautifulsoup4`, `boto3` for weekly specials.

2. **Setup**:
   ```bash
   pip install requests pandas tqdm beautifulsoup4 boto3
   ```

3. **Execution**:
   ```bash
   python fetch_all_products.py  # For full catalog collection
   python fetch_aisle_products.py       # For weekly "finds" updates
   ```

These scripts can be executed automatically via GitHub Actions, ensuring regular data updates without manual intervention.

## Outputs

The data is stored in CSV and JSON files with configuration for upload to AWS S3 or other specified services. The outputs include:

- **Full catalog output** (via `fetch_all_products.py`): [JSON](https://stilesdata.com/aldi/aldi_products_detailed.json) | [CSV](https://stilesdata.com/aldi/aldi_products_detailed.csv)

| Field Name        | Description                                             | Example                                               |
|-------------------|---------------------------------------------------------|-------------------------------------------------------|
| `sku`             | Stock Keeping Unit identifier                           | "0000000000000005"                                    |
| `name`            | Product name                                            | "Original Kettle Chips, 8 oz"                         |
| `brand_name`      | Product brand name                                      | "Clancy's"                                            |
| `price_unit`      | Product price unit                                      | "oz"                                                  |
| `price`           | Product price                                           | "$7.99"                                               |
| `description`     | Description of the product                              | "Complete a tasty lunch with a handful ..."           |
| `categories`      | Product categories (parent, children)                   | "Snacks, Chips, Crackers & Popcorn"                   |
| `country_origin`  | Product origin country                                  | "USA and Imported"                                    |
| `snap_eligible`   | Supplemental Nutrition Assistance Program eligible      | "True"                                                |
| `formatted_price` | Formatted price with currency symbol                    | "$2.15"                                               |
| `slug`            | Slug for product URL                                    | "clancy-s-original-kettle-chips-8-oz"                 |
| `image_url`       | URL for product image                                   | "https://dm.cms.aldi.cx/is/image/...{slug}"           |
| `warning_code`    | Health warnings in CA                                   | "ca_prop_65"                                          |
| `warning_desc`    | Description of health warning                           | "Consuming this product can expose you to ..."        |


- **Weekly finds output** (via `fetch_aisle_products.py`): [JSON](https://stilesdata.com/aldi/aldi_finds_latest.json) | [CSV](https://stilesdata.com/aldi/aldi_finds_latest.csv)

  | Field Name     | Description                                       | Example                            |
  |----------------|---------------------------------------------------|------------------------------------|
  | `week_date`    | The date range for which the products are listed  | "04/17/24 - 04/23/24"              |
  | `category`     | Category of the product                           | "Home Goods"                       |
  | `brand`        | Brand of the product                              | "Huntington Home"                  |
  | `description`  | Description of the product                        | "Luxury 2 Wick Candle"             |
  | `price`        | Price of the product                              | "$4.99*"                           |
  | `image`        | URL of the product image                          | "https://www.aldi.us/.../candle.jpg" |
  | `link`         | URL to the product detail page                    | "https://www.aldi.us/.../candle/"   |
  | `week_start`   | Start date of the week for the product listing    | "04/17/24"                         |
  | `week_end`     | End date of the week for the product listing      | "04/23/24"                         |
  | `price_clean`  | Numeric price of the product                      | 4.99                               |

## Automated workflow with GitHub Actions

The GitHub Actions workflows (`fetch_all_products.yml` for the full catalog and `fetch_aisle_products.yml` for the weekly finds) automate the execution of the scraping scripts on a regular basis (overnight on Sundays). 

These workflows include steps to set up Python, install dependencies, execute the scripts and handle data storage.

### Workflow steps

1. **Set up Python**: Installs Python and the required packages.
2. **Run scraper**: Executes the Python scripts to fetch data and generate the output files.
3. **Upload data**: The CSV files are uploaded to an AWS S3 bucket or another configured storage service.

## Contributing

Contributions to this project are welcome, especially in the following areas:

- **Code enhancements**: Suggestions for improving the scraping efficiency or expanding data collection features.
- **Documentation**: Updates to README or additional guidelines for users.
- **Feature requests**: Ideas for new features or data points to collect or ways to visualize what's been collected.

## License

This project is released under the MIT License. See the [LICENSE](LICENSE) file for more details.
