import pandas as pd
import numpy as np
from datetime import datetime
import os
import json
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.chart import LineChart, Reference, BarChart


class MultiProductBuyingCalculator:
    """
    Python implementation of the Multi-Product Buying Calculator.
    This calculator analyzes the ROI of purchasing multiple related products at bulk discount pricing.
    """

    def __init__(self):
        # Default parameters
        self.small_deal_minimum = 30
        self.bulk_deal_minimum = 60
        self.payment_terms = 30

        # Initialize product data array
        self.products = []

        # Initialize scenario directory
        self.scenarios_dir = "scenarios"
        if not os.path.exists(self.scenarios_dir):
            os.makedirs(self.scenarios_dir)

    def add_product(self, product_name, current_price, bulk_price, cases_on_hand,
                    cases_per_year, bottles_per_case, bulk_quantity=0):
        """Add a product to the calculator."""
        product = {
            "product_name": product_name,
            "current_price": float(current_price),
            "bulk_price": float(bulk_price),
            "cases_on_hand": int(cases_on_hand),
            "cases_per_year": int(cases_per_year),
            "bottles_per_case": int(bottles_per_case),
            "bulk_quantity": int(bulk_quantity) if bulk_quantity else 0
        }

        # Calculate derived values
        if product["cases_per_year"] > 0:
            product["daily_cases"] = product["cases_per_year"] / 365
            product["monthly_cases"] = product["daily_cases"] * (365/12)
        else:
            product["daily_cases"] = 0
            product["monthly_cases"] = 0

        self.products.append(product)
        return product

    def clear_products(self):
        """Clear all products from the calculator."""
        self.products = []

    def set_parameters(self, small_deal_minimum, bulk_deal_minimum, payment_terms):
        """Set the calculator parameters."""
        self.small_deal_minimum = int(small_deal_minimum)
        self.bulk_deal_minimum = int(bulk_deal_minimum)
        self.payment_terms = int(payment_terms)

    def calculate(self):
        """Calculate all product metrics."""
        results = []

        for product in self.products:
            if not product["bulk_quantity"]:
                # Skip products without bulk quantities
                continue

            result = self._calculate_product(product)
            results.append(result)

        # Calculate summary results
        summary = self._calculate_summary(results)

        return {
            "products": results,
            "summary": summary
        }

    def _calculate_product(self, product):
        """Calculate metrics for a single product."""
        result = product.copy()

        # Skip calculations if no bulk quantity or no sales velocity
        if not product["bulk_quantity"] or not product["daily_cases"]:
            return result

        # Calculate smaller deal metrics
        smaller_deal_quantity = max(self.small_deal_minimum / self.bulk_deal_minimum * product["bulk_quantity"], 0)
        result["smaller_deal_quantity"] = smaller_deal_quantity
        result["smaller_deal_price"] = product["current_price"]
        result["smaller_deal_total"] = smaller_deal_quantity * product["current_price"] * product["bottles_per_case"]

        # Calculate post-terms inventory position for smaller deal
        smaller_post_terms_cases = max(smaller_deal_quantity + product["cases_on_hand"] -
                                     (product["daily_cases"] * self.payment_terms), 0)
        result["smaller_post_terms_cases"] = smaller_post_terms_cases
        result["smaller_post_terms_value"] = smaller_post_terms_cases * product["current_price"] * product["bottles_per_case"]

        # Calculate larger deal metrics
        larger_deal_quantity = product["bulk_quantity"]
        result["larger_deal_quantity"] = larger_deal_quantity
        result["larger_deal_price"] = product["bulk_price"]
        result["larger_deal_total"] = larger_deal_quantity * product["bulk_price"] * product["bottles_per_case"]

        # Calculate post-terms inventory position for larger deal
        larger_post_terms_cases = max(larger_deal_quantity + product["cases_on_hand"] -
                                    (product["daily_cases"] * self.payment_terms), 0)
        result["larger_post_terms_cases"] = larger_post_terms_cases
        result["larger_post_terms_value"] = larger_post_terms_cases * product["bulk_price"] * product["bottles_per_case"]

        # Calculate savings and investment
        result["savings_per_bottle"] = max(product["current_price"] - product["bulk_price"], 0)
        result["total_savings"] = result["savings_per_bottle"] * larger_deal_quantity * product["bottles_per_case"]

        # Calculate investment impact
        result["peak_additional_investment"] = result["larger_post_terms_value"] - result["smaller_post_terms_value"]
        result["average_additional_investment"] = result["peak_additional_investment"] / 2

        # Calculate ROI metrics
        if result["average_additional_investment"] > 0:
            result["roi"] = result["total_savings"] / result["average_additional_investment"]

            # Calculate holding time for extra cases
            if product["daily_cases"] > 0:
                extra_cases = larger_deal_quantity - smaller_deal_quantity
                result["holding_time_days"] = extra_cases / product["daily_cases"]
                result["annualized_roi"] = result["roi"] * 365 / result["holding_time_days"]
            else:
                result["holding_time_days"] = 0
                result["annualized_roi"] = 0
        else:
            result["roi"] = 0
            result["holding_time_days"] = 0
            result["annualized_roi"] = 0

        return result

    def _calculate_summary(self, results):
        """Calculate summary metrics across all products."""
        summary = {
            "peak_additional_investment": 0,
            "average_additional_investment": 0,
            "total_savings": 0,
            "roi": 0,
            "annualized_roi": 0
        }

        # Skip if no valid results
        if not results:
            return summary

        # Calculate totals
        for result in results:
            if "peak_additional_investment" in result:
                summary["peak_additional_investment"] += result.get("peak_additional_investment", 0)
                summary["average_additional_investment"] += result.get("average_additional_investment", 0)
                summary["total_savings"] += result.get("total_savings", 0)

        # Calculate ROI
        if summary["average_additional_investment"] > 0:
            summary["roi"] = summary["total_savings"] / summary["average_additional_investment"]

            # Calculate weighted average of annualized ROI
            weighted_annualized_roi = 0
            total_investment = 0

            for result in results:
                investment = result.get("average_additional_investment", 0)
                annualized_roi = result.get("annualized_roi", 0)

                if investment > 0:
                    weighted_annualized_roi += investment * annualized_roi
                    total_investment += investment

            if total_investment > 0:
                summary["annualized_roi"] = weighted_annualized_roi / total_investment

        return summary

    def save_scenario(self, scenario_name):
        """Save the current scenario to a file."""
        scenario = {
            "parameters": {
                "small_deal_minimum": self.small_deal_minimum,
                "bulk_deal_minimum": self.bulk_deal_minimum,
                "payment_terms": self.payment_terms
            },
            "products": self.products
        }

        # Create scenario file
        filename = f"{self.scenarios_dir}/{scenario_name.lower().replace(' ', '_')}.json"
        with open(filename, 'w') as f:
            json.dump(scenario, f, indent=2)

        return filename

    def load_scenario(self, scenario_name):
        """Load a scenario from a file."""
        filename = f"{self.scenarios_dir}/{scenario_name.lower().replace(' ', '_')}.json"

        if not os.path.exists(filename):
            return False

        with open(filename, 'r') as f:
            scenario = json.load(f)

        # Load parameters
        self.set_parameters(
            scenario["parameters"]["small_deal_minimum"],
            scenario["parameters"]["bulk_deal_minimum"],
            scenario["parameters"]["payment_terms"]
        )

        # Load products
        self.products = scenario["products"]

        return True

    def list_scenarios(self):
        """List all available scenarios."""
        scenarios = []

        for filename in os.listdir(self.scenarios_dir):
            if filename.endswith(".json"):
                scenario_name = filename[:-5].replace("_", " ").title()
                scenarios.append(scenario_name)

        return scenarios

    def generate_report(self, results):
        """Generate an Excel report for the current calculation."""
        wb = Workbook()

        # Create sheets
        summary_sheet = wb.active
        summary_sheet.title = "Summary"
        product_sheet = wb.create_sheet("Product Details")
        chart_sheet = wb.create_sheet("Charts")

        # Add styles
        title_font = Font(name='Calibri', size=14, bold=True)
        header_font = Font(name='Calibri', size=12, bold=True)
        header_fill = PatternFill(start_color="D0E2F3", end_color="D0E2F3", fill_type="solid")
        money_format = '#,##0.00'
        percent_format = '0.00%'

        # Create summary sheet
        summary_sheet['B2'] = "CHEERS LIQUOR MART"
        summary_sheet['B3'] = "MULTI PRODUCT DEAL BUYING CALCULATOR"
        summary_sheet['B2'].font = title_font
        summary_sheet['B3'].font = title_font

        # Parameters section
        summary_sheet['B5'] = "PARAMETERS"
        summary_sheet['B5'].font = header_font

        summary_sheet['B7'] = "Small Deal Minimum"
        summary_sheet['B8'] = self.small_deal_minimum
        summary_sheet['C8'] = "cases"

        summary_sheet['E7'] = "Bulk Deal Minimum"
        summary_sheet['E8'] = self.bulk_deal_minimum
        summary_sheet['F8'] = "cases"

        summary_sheet['H7'] = "Payment Terms"
        summary_sheet['H8'] = self.payment_terms
        summary_sheet['I8'] = "days"

        # Results section
        summary_sheet['B15'] = "INVESTMENT SUMMARY"
        summary_sheet['B15'].font = header_font

        summary_sheet['B17'] = "Peak Additional Investment"
        summary_sheet['C17'] = results["summary"]["peak_additional_investment"]
        summary_sheet['C17'].number_format = money_format

        summary_sheet['B18'] = "Average Investment"
        summary_sheet['C18'] = results["summary"]["average_additional_investment"]
        summary_sheet['C18'].number_format = money_format

        summary_sheet['B19'] = "Total Savings"
        summary_sheet['C19'] = results["summary"]["total_savings"]
        summary_sheet['C19'].number_format = money_format

        summary_sheet['B20'] = "ROI"
        summary_sheet['C20'] = results["summary"]["roi"]
        summary_sheet['C20'].number_format = percent_format

        summary_sheet['B21'] = "Annualized Total ROI"
        summary_sheet['C21'] = results["summary"]["annualized_roi"]
        summary_sheet['C21'].number_format = percent_format

        # Product Details sheet
        self._create_product_details_sheet(product_sheet, results["products"], header_fill, money_format, percent_format)

        # Charts sheet
        self._create_charts_sheet(chart_sheet, results["products"], wb)

        # Set column widths
        for sheet in [summary_sheet, product_sheet, chart_sheet]:
            for col in range(1, 20):  # Adjust up to 20 columns
                sheet.column_dimensions[get_column_letter(col)].width = 15

        # Create timestamp for filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"multi_product_deal_{timestamp}.xlsx"
        filepath = os.path.join("reports", filename)

        # Ensure reports directory exists
        if not os.path.exists("reports"):
            os.makedirs("reports")

        # Save workbook
        wb.save(filepath)

        return filename

    def _create_product_details_sheet(self, sheet, products, header_fill, money_format, percent_format):
        """Create the product details sheet."""
        # Headers
        headers = [
            "Product", "Current Price", "Bulk Price", "Cases/Year", "Bottles/Case", "Bulk Quantity",
            "Smaller Deal Qty", "Smaller Post-Terms Cases", "Smaller Post-Terms Value",
            "Larger Deal Qty", "Larger Post-Terms Cases", "Larger Post-Terms Value",
            "Savings Per Bottle", "Total Savings", "Peak Add'l Investment", "Average Add'l Investment",
            "ROI", "Annualized ROI", "Holding Time (Days)"
        ]

        for col, header in enumerate(headers, start=1):
            cell = sheet.cell(row=1, column=col, value=header)
            cell.font = Font(bold=True)
            cell.fill = header_fill

        # Product data
        for row, product in enumerate(products, start=2):
            sheet.cell(row=row, column=1, value=product["product_name"])
            sheet.cell(row=row, column=2, value=product["current_price"]).number_format = money_format
            sheet.cell(row=row, column=3, value=product["bulk_price"]).number_format = money_format
            sheet.cell(row=row, column=4, value=product["cases_per_year"])
            sheet.cell(row=row, column=5, value=product["bottles_per_case"])
            sheet.cell(row=row, column=6, value=product["bulk_quantity"])

            if "smaller_deal_quantity" in product:
                sheet.cell(row=row, column=7, value=product["smaller_deal_quantity"])
                sheet.cell(row=row, column=8, value=product["smaller_post_terms_cases"])
                sheet.cell(row=row, column=9, value=product["smaller_post_terms_value"]).number_format = money_format
                sheet.cell(row=row, column=10, value=product["larger_deal_quantity"])
                sheet.cell(row=row, column=11, value=product["larger_post_terms_cases"])
                sheet.cell(row=row, column=12, value=product["larger_post_terms_value"]).number_format = money_format
                sheet.cell(row=row, column=13, value=product["savings_per_bottle"]).number_format = money_format
                sheet.cell(row=row, column=14, value=product["total_savings"]).number_format = money_format
                sheet.cell(row=row, column=15, value=product["peak_additional_investment"]).number_format = money_format
                sheet.cell(row=row, column=16, value=product["average_additional_investment"]).number_format = money_format
                sheet.cell(row=row, column=17, value=product["roi"]).number_format = percent_format
                sheet.cell(row=row, column=18, value=product["annualized_roi"]).number_format = percent_format
                sheet.cell(row=row, column=19, value=product["holding_time_days"])

    def _create_charts_sheet(self, sheet, products, workbook):
        """Create charts to visualize the data."""
        # ROI chart
        roi_chart = BarChart()
        roi_chart.title = "ROI by Product"

        # Prepare data
        product_names = []
        roi_values = []
        annualized_roi_values = []

        for product in products:
            if "roi" in product:
                product_names.append(product["product_name"])
                roi_values.append(product["roi"])
                annualized_roi_values.append(product["annualized_roi"])

        # Write data to sheet for referencing
        sheet.cell(row=1, column=1, value="Product")
        sheet.cell(row=1, column=2, value="ROI")
        sheet.cell(row=1, column=3, value="Annualized ROI")

        for i, (product, roi, ann_roi) in enumerate(zip(product_names, roi_values, annualized_roi_values), start=2):
            sheet.cell(row=i, column=1, value=product)
            sheet.cell(row=i, column=2, value=roi)
            sheet.cell(row=i, column=3, value=ann_roi)

        # Create the chart
        if product_names:
            cat_ref = Reference(sheet, min_col=1, min_row=2, max_row=1+len(product_names))
            roi_ref = Reference(sheet, min_col=2, min_row=1, max_row=1+len(product_names))
            ann_roi_ref = Reference(sheet, min_col=3, min_row=1, max_row=1+len(product_names))

            roi_chart.add_data(roi_ref, titles_from_data=True)
            roi_chart.add_data(ann_roi_ref, titles_from_data=True)
            roi_chart.set_categories(cat_ref)

            roi_chart.x_axis.title = "Product"
            roi_chart.y_axis.title = "ROI"

            # Add chart to sheet
            sheet.add_chart(roi_chart, "A10")

        # Investment vs. Savings chart
        inv_chart = BarChart()
        inv_chart.title = "Investment vs. Savings by Product"

        # Write data to sheet for referencing
        sheet.cell(row=1, column=5, value="Product")
        sheet.cell(row=1, column=6, value="Investment")
        sheet.cell(row=1, column=7, value="Savings")

        for i, product in enumerate(products, start=2):
            if "peak_additional_investment" in product:
                sheet.cell(row=i, column=5, value=product["product_name"])
                sheet.cell(row=i, column=6, value=product["peak_additional_investment"])
                sheet.cell(row=i, column=7, value=product["total_savings"])

        # Create the chart
        if product_names:
            cat_ref = Reference(sheet, min_col=5, min_row=2, max_row=1+len(product_names))
            inv_ref = Reference(sheet, min_col=6, min_row=1, max_row=1+len(product_names))
            sav_ref = Reference(sheet, min_col=7, min_row=1, max_row=1+len(product_names))

            inv_chart.add_data(inv_ref, titles_from_data=True)
            inv_chart.add_data(sav_ref, titles_from_data=True)
            inv_chart.set_categories(cat_ref)

            inv_chart.x_axis.title = "Product"
            inv_chart.y_axis.title = "Amount ($)"

            # Add chart to sheet
            sheet.add_chart(inv_chart, "A30")
