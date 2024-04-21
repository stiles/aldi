# ALDI product data collection

This project automates the scraping of product information from ALDI's website, initially focusing on the ["Aisle of Shame" or "finds"](https://www.aldi.us/weekly-specials/this-weeks-aldi-finds/), and now expanded to encompass a full catalog of products available. 

Initially inspired by Parija Kavilanz's [CNN story](https://www.cnn.com/2024/04/19/business/aldi-aisle-of-shame-fans/index.html) about ALDI's popular middle-aisle deals, it has since grown to include a complete dataset capturing every product for more comprehensive analysis and accessibility.

*The project — and its documentation — are still a work in progress.*

## Project overview

The project utilizes two scripts: `fetch_all_products.py` for capturing the full product catalog and `fetch_aisle_products.py` for weekly updates of the supermarket chain's "finds" collection. 

This approach ensures detailed data collection of the general inventory but also a specific and regularly updating slice of data detailing the company's "Aisle of Shame" deals. 

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
   python fetch_process.py       # For weekly "finds" updates
   ```

These scripts can be executed automatically via GitHub Actions, ensuring regular data updates without manual intervention.

## Outputs

The data is stored in CSV files with potential configuration for upload to AWS S3 or other specified services. The outputs differ as follows:

- **Full Catalog Output** (`fetch_all_products.py`):
  | Field Name       | Description                                | Example                                  |
  |------------------|--------------------------------------------|------------------------------------------|
  | `name`           | Product name                               | "Meritage Red Wine, 750 ml"              |
  | `sku`            | Stock Keeping Unit identifier              | "0000000000000002"                       |
  | `price`          | Product price                              | "$7.99"                                  |
  | `description`    | Description of the product                 | "Blend of plum, anise, blackberry..."    |
  | `category`       | Product category                           | "Alcohol, Red Wine"                      |
  | `formatted_price`| Formatted price with currency symbol       | "$7.99"                                  |
  | `urlSlugText`    | Slug for product URL                       | "outlander-meritage-red-wine-750-ml"     |

- **Weekly Finds Output** (`fetch_process.py`):
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

The GitHub Actions workflows (`scheduled_data_fetch.yml` for the full catalog and `fetch_deals.yml` for the weekly finds) automate the execution of the scraping scripts on a regular basis (e.g., weekly). These workflows include steps to set up Python, install dependencies, execute the scripts, and handle data storage.

### Workflow steps

1. **Set up Python**: Installs Python and the required packages.
2. **Run Scraper**: Executes the Python scripts to fetch data and generate the output files.
3. **Upload Data**: The CSV files are uploaded to an AWS S3 bucket or another configured storage service.

## Contributing

Contributions to this project are welcome, especially in the following areas:

- **Code Enhancements**: Suggestions for improving the scraping efficiency or expanding data collection features.
- **Documentation**: Updates to README or additional guidelines for users.
- **Feature Requests**: Ideas for new features or data points to collect.

## License

This project is released under the MIT License. See the [LICENSE](LICENSE) file for more details.
