# Cheers Liquor Mart Business Tools

A suite of web-based tools for Cheers Liquor Mart to help with everyday business operations.

## Features

### AP Weekly Report Generator
- Processes AP Aging Excel reports
- Generates weekly payment summaries
- Creates formatted Excel reports with multiple sheets:
  - Weekly Summary
  - Weekly Bill
  - Vendor Subtotals

### Deal Split Calculator
- Calculates product distribution based on annual sales proportions
- Save and load different scenarios
- Generate Excel reports with perfect distribution

### Multi-Product Buying Calculator
- Evaluate ROI for purchasing multiple products in bulk
- Save, load, and delete scenarios
- Generate Excel summaries with charts

## Installation and Setup

### Requirements
- Python 3.8 or higher
- Docker (optional, for containerized deployment)

### Local Development

1. Clone the repository:
   ```
   git clone <repo-url>
   cd report-builder
   ```

2. Create a virtual environment and install dependencies:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Run the application:
   ```
   python app.py
   ```

4. Open your browser and navigate to `http://localhost:8080`
5. Log files will be written to a newly created `logs/` directory

### Docker Deployment

1. Build and start the container using Docker Compose:
   ```
   docker-compose up -d
   ```

2. The application will be available at `http://localhost:8080`

## File Structure

- `app.py` - Main application file with Flask routes
- `report_processor.py` - AP Aging report processing logic
- `deal_split_processor.py` - Deal Split Calculator logic
- `multi_product_calculator.py` - Multi-Product Buying Calculator logic
- `templates/` - HTML templates for the web interface
- `scenarios.json` - Stored Deal Split Calculator scenarios
- `uploads/` - Temporary storage for uploaded files
- `reports/` - Generated report files

## Usage

### AP Weekly Report Generator
1. Upload an AP Aging Excel file
2. Wait for processing to complete
3. Download the generated report

### Deal Split Calculator
1. Enter product varieties and their annual sales figures
2. Specify the desired total order quantity
3. Calculate the optimal distribution
4. Save scenarios for future use or generate Excel reports

### Multi-Product Buying Calculator
1. Add each product with current and bulk pricing
2. Set deal parameters like minimum quantities and payment terms
3. Calculate ROI and savings across all products
4. Save scenarios, download reports, or delete them when no longer needed

## Development

To modify the application:

1. Make changes to the code
2. If using Docker, rebuild the container:
   ```
   docker-compose down
   docker-compose up --build -d
   ```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
