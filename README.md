# Scraping ALDI's "Aisle of Shame"

This project contains a Python script that scrapes product information from ALDI's ["finds" page](https://www.aldi.us/weekly-specials/this-weeks-aldi-finds/), known in the store as the "Aisle of Shame". The project is inspired by Parija Kavilanz's [story for CNN](https://www.cnn.com/2024/04/19/business/aldi-aisle-of-shame-fans/index.html) about these middle-aisle deals. 

The extracted data has details about each product, such as the brand, description, price and sales week. The script is scheduled to run weekly using GitHub Actions, which stores the output in CSV files to an AWS S3 bucket.

## How to Run the Script

The script `fetch_process.py` is designed to be executed automatically via GitHub Actions, but can also be run manually or through other automation services. To run it manually:

1. Ensure Python 3.8+ is installed on your machine.
2. Install the required Python libraries:
   ```
   pip install requests beautifulsoup4 pandas boto3
   ```
3. Run the script:
   ```
   python fetch_process.py
   ```

## Output Data

The script outputs a weekly snapshot CSV file named `<current-date>_aldi_finds.csv`, which is uploaded to an AWS S3 bucket. It also adds any new rows to an archive called [`https://stilesdata.com/aldi/aldi_finds_archive.csv`](https://stilesdata.com/aldi/aldi_finds_archive.csv). 

The data fields in the CSV are as follows:

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

## Automated Workflow

The GitHub Actions workflow (`fetch_deals.yml`) automates the execution of the scraping script weekly. It is set up to install dependencies, run the script, and handle the file upload to AWS S3. The workflow is triggered every Sunday at midnight Pacific Time.

### Workflow Steps

1. **Set up Python**: Installs Python and the required packages.
2. **Run scraper**: Executes the Python script to fetch data and generate the CSV file.
3. **Upload to S3**: The CSV file is uploaded to the specified AWS S3 bucket using credentials stored in GitHub Secrets.

## Contributing

Contributions to this project are welcome. You can contribute to this CRITICAL project in several ways:

- **Code pull requests**: If you have improvements or bug fixes, please submit a PR.
- **Documentation**: Improvements to documentation or the README are greatly appreciated.
- **Feature suggestions**: Have an idea? Submit it as an issue!

## License

This project is released under the MIT License. See the [LICENSE](LICENSE) file for details.
