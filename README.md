# Report Builder

A Python Flask application for business reporting and financial calculations with multiple specialized calculators for beverage industry.

## Calculators

The application includes the following specialized calculators:

1. **Multi-Product Buying Calculator** - Analyzes the ROI of purchasing multiple related products at bulk discount pricing
2. **Deal Split Calculator** - Splits a deal across multiple product varieties based on sales volume
3. **Single Deal Calculator** - Calculates ROI for a single product deal
4. **Sales Tax Calculator** - Calculates sales tax for different jurisdictions
5. **Margin Calculator** - Calculates margins and markup for products
6. **AP Report Processor** - Processes accounts payable reports

## Multi-Product Buying Calculator

The Multi-Product Buying Calculator is a sophisticated tool for beverage industry buyers. It allows you to:

- Analyze the ROI of bulk purchases across multiple related products
- Allocate case quantities proportionally across a portfolio
- Optimize allocations to maximize ROI
- Save and load scenarios
- Generate Excel reports with detailed metrics

### Features

- **Pure calculation engine**: Core logic implemented in both JavaScript (client-side) and Python (server-side)
- **Proportional allocation**: Distribute deal cases based on annual sales volume
- **ROI-based optimization**: Iterative swapping engine to maximize overall ROI
- **Minimum days of stock**: Ensures sufficient inventory levels
- **Investment and savings analysis**: Detailed financial metrics for each product
- **Portfolio ROI calculation**: Aggregate metrics across all products
- **Scenario management**: Save, load, and delete scenarios
- **Visualizations**: ROI optimization progress chart
- **Excel reporting**: Comprehensive reports with detailed product metrics

### Architecture

The calculator follows a client-server architecture:

- **Client-side**: JavaScript implementation for real-time calculations and UI interactions
  - Pure functions for core calculations
  - UI components for data entry and result display
  - Charting for visualization

- **Server-side**: Python Flask implementation for persistence and report generation
  - RESTful API endpoints
  - Scenario storage
  - Excel report generation

### API Endpoints

The following API endpoints are available for the Multi-Product Buying Calculator:

- `GET /multi-product-calculator` - Renders the calculator page
- `POST /api/calculate-multi-product-deal` - Calculates results for products
- `POST /api/optimize-multi-product-deal` - Runs optimization to improve ROI
- `POST /api/generate-multi-product-report` - Generates an Excel report
- `POST /api/save-multi-product-scenario` - Saves a scenario
- `GET /api/list-multi-product-scenarios` - Lists all saved scenarios
- `GET /api/get-multi-product-scenario/<name>` - Gets a specific scenario
- `DELETE /api/delete-multi-product-scenario/<name>` - Deletes a scenario

## Installation

### Prerequisites

- Python 3.8 or higher
- Node.js and npm (for development)

### Setup

1. Clone the repository
2. Create a virtual environment:
   ```
   python -m venv venv
   ```
3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`
4. Install the dependencies:
   ```
   pip install -r requirements.txt
   ```
5. Run the application:
   ```
   python app.py
   ```
6. Open your browser and navigate to `http://localhost:8080`

## Project Structure

```
Report-Builder/
├── app.py                   # Main Flask application
├── static/                  # Static assets
│   ├── css/                 # CSS files
│   ├── js/                  # JavaScript files
│   │   ├── calculator.js    # Multi-Product Calculator core logic
│   │   └── multi_product_calculator_app.js # UI logic
│   └── assets/              # Images and other assets
├── templates/               # HTML templates
│   ├── base.html            # Base template
│   ├── index.html           # Home page
│   └── multi_product_calculator.html # Calculator page
├── multi_product_calculator.py # Server-side calculator implementation
├── api_utils.py             # API utilities
├── logging_utils.py         # Logging utilities
├── excel_utils.py           # Excel report utilities
├── scenario_utils.py        # Scenario management utilities
├── scenarios/               # Saved scenarios
├── reports/                 # Generated reports
├── logs/                    # Application logs
└── uploads/                 # Uploaded files
```

## Development

### Adding a New Calculator

1. Create a new template in the `templates` directory
2. Add routes to `app.py`
3. Create a Python class for the calculator
4. Implement the JavaScript frontend if needed

### Testing

Run the tests:
```
python -m unittest discover tests
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
