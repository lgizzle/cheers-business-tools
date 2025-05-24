"""
Allocation strategy module for the multi-product calculator.
Defines different strategies for allocating quantities across products.
"""

import math
from abc import ABC, abstractmethod
import calculator

class AllocationStrategy(ABC):
    """Base abstract class for allocation strategies."""

    @abstractmethod
    def allocate(self, products, params):
        """
        Allocate quantities across products based on the strategy.

        Parameters:
        - products: List of product dictionaries
        - params: Dictionary of allocation parameters

        Returns: List of product dictionaries with bulk_quantity values set
        """
        pass

    def _ensure_minimum_days_stock(self, products, min_days_stock):
        """
        Ensure all products meet minimum days of stock requirements.

        Parameters:
        - products: List of product dictionaries
        - min_days_stock: Minimum days of stock required

        Returns: Dictionary with total additional cases needed and updated products
        """
        if min_days_stock is None or min_days_stock <= 0:
            return {"additional_cases": 0, "products": products}

        total_additional = 0
        updated_products = []

        for product in products:
            # Calculate daily cases
            daily_cases = calculator.calculate_daily_cases(product["cases_per_year"])

            # Calculate how many more cases needed to meet minimum days
            min_stock_needed = calculator.calculate_minimum_stock_needed(
                product.get("cases_on_hand", 0), daily_cases, min_days_stock
            )

            # Update product with the minimum required quantity
            product_copy = product.copy()
            current_quantity = product_copy.get("bulk_quantity", 0)
            product_copy["bulk_quantity"] = max(current_quantity, min_stock_needed)

            # Track how many additional cases were added
            additional_cases = product_copy["bulk_quantity"] - current_quantity
            total_additional += additional_cases

            updated_products.append(product_copy)

        return {
            "additional_cases": total_additional,
            "products": updated_products
        }

    def _cap_maximum_inventory(self, products, max_days=90):
        """
        Cap inventory to prevent excessive stock levels.

        Parameters:
        - products: List of product dictionaries
        - max_days: Maximum days of stock allowed

        Returns: Updated products list with capped quantities
        """
        updated_products = []

        for product in products:
            # Calculate daily cases
            daily_cases = calculator.calculate_daily_cases(product["cases_per_year"])

            # Calculate maximum reasonable inventory
            max_inventory = calculator.calculate_maximum_stock(
                daily_cases, max_days, product.get("cases_on_hand", 0)
            )

            # Cap bulk quantity to maximum inventory
            product_copy = product.copy()
            current_quantity = product_copy.get("bulk_quantity", 0)
            product_copy["bulk_quantity"] = min(current_quantity, max_inventory)

            updated_products.append(product_copy)

        return updated_products

class ProportionalAllocationStrategy(AllocationStrategy):
    """Allocate quantities proportionally based on annual sales volume."""

    def allocate(self, products, params):
        """
        Allocate quantities proportionally to annual sales.

        Parameters:
        - products: List of product dictionaries
        - params: Dictionary with allocation parameters:
          - bulk_deal_minimum: Minimum total bulk quantity
          - min_days_stock: Minimum days of stock (optional)

        Returns: List of product dictionaries with bulk_quantity values set
        """
        # Initialize all bulk quantities to 0
        result_products = [{**p, "bulk_quantity": 0} for p in products]

        # Calculate total annual sales
        total_annual_cases = sum(p.get("cases_per_year", 0) for p in products)

        if total_annual_cases <= 0:
            return result_products

        # Calculate proportional allocation
        target_total = params["bulk_deal_minimum"]

        # Apply minimum days of stock constraint if specified
        if "min_days_stock" in params and params["min_days_stock"]:
            min_stock_result = self._ensure_minimum_days_stock(
                result_products, params["min_days_stock"]
            )
            result_products = min_stock_result["products"]
            additional_cases = min_stock_result["additional_cases"]

            # Adjust target for remaining allocation
            target_total = max(0, target_total - additional_cases)

        # Calculate proportions based on annual sales
        for i, product in enumerate(result_products):
            # Skip products with no sales
            if product.get("cases_per_year", 0) <= 0:
                continue

            # Calculate proportion of sales
            proportion = product["cases_per_year"] / total_annual_cases

            # Allocate proportionally
            current_qty = product.get("bulk_quantity", 0)
            additional_qty = proportion * target_total

            # Update product
            result_products[i]["bulk_quantity"] = current_qty + additional_qty

        # Round quantities while preserving the total
        result_products = self._round_preserving_total(result_products, params["bulk_deal_minimum"])

        # Cap maximum inventory
        result_products = self._cap_maximum_inventory(result_products)

        # Final check: ensure we meet the minimum
        current_total = sum(p.get("bulk_quantity", 0) for p in result_products)
        if current_total < params["bulk_deal_minimum"]:
            # Find a product to add the difference to
            for i, p in enumerate(result_products):
                if p.get("cases_per_year", 0) > 0:
                    result_products[i]["bulk_quantity"] += (params["bulk_deal_minimum"] - current_total)
                    break

        return result_products

    def _round_preserving_total(self, products, target_total):
        """
        Round quantities while preserving the total target.

        Parameters:
        - products: List of product dictionaries with bulk_quantity values
        - target_total: Target total quantity

        Returns: Updated products with rounded quantities
        """
        # First, round down all quantities
        rounded_products = []
        total_rounded = 0
        fractional_parts = []

        for product in products:
            product_copy = product.copy()
            qty = product_copy.get("bulk_quantity", 0)
            floor_qty = math.floor(qty)
            fractional = qty - floor_qty

            product_copy["bulk_quantity"] = floor_qty
            total_rounded += floor_qty

            # Store fractional parts for distribution
            fractional_parts.append({
                "product_idx": len(rounded_products),
                "fractional": fractional
            })

            rounded_products.append(product_copy)

        # Distribute remaining quantity based on fractional parts
        remaining = int(target_total - total_rounded)

        if remaining > 0:
            # Sort by fractional part (descending)
            fractional_parts.sort(key=lambda x: x["fractional"], reverse=True)

            # Distribute to products with largest fractional parts
            for i in range(min(remaining, len(fractional_parts))):
                idx = fractional_parts[i]["product_idx"]
                rounded_products[idx]["bulk_quantity"] += 1

        # Check if we're still under the target, and if so, add more to the first product
        actual_total = sum(p["bulk_quantity"] for p in rounded_products)
        if actual_total < target_total and len(rounded_products) > 0:
            # Add the shortfall to the first product with sales
            for p in rounded_products:
                if p.get("cases_per_year", 0) > 0:
                    p["bulk_quantity"] += (target_total - actual_total)
                    break

        return rounded_products

class ROIAllocationStrategy(AllocationStrategy):
    """Allocate quantities to maximize ROI across products."""

    def allocate(self, products, params):
        """
        Allocate quantities to maximize overall ROI.

        Parameters:
        - products: List of product dictionaries
        - params: Dictionary with allocation parameters:
          - bulk_deal_minimum: Minimum total bulk quantity
          - min_days_stock: Minimum days of stock (optional)
          - payment_terms: Payment terms in days

        Returns: List of product dictionaries with bulk_quantity values set
        """
        # Initialize all bulk quantities to 0
        result_products = [{**p, "bulk_quantity": 0} for p in products]

        # Apply minimum days of stock constraint if specified
        min_days_stock = params.get("min_days_stock")
        if min_days_stock:
            min_stock_result = self._ensure_minimum_days_stock(
                result_products, min_days_stock
            )
            result_products = min_stock_result["products"]
            allocated_cases = min_stock_result["additional_cases"]
        else:
            allocated_cases = 0

        # Calculate remaining cases to allocate
        remaining_cases = max(0, params["bulk_deal_minimum"] - allocated_cases)

        if remaining_cases <= 0:
            return result_products

        # Calculate ROI metrics for each product
        products_with_roi = self._calculate_product_roi_metrics(result_products, params)

        # Sort products by ROI (descending)
        products_with_roi.sort(key=lambda p: p["roi_metric"], reverse=True)

        # Allocate remaining cases by ROI
        for product in products_with_roi:
            # Skip products with zero sales
            if product["daily_cases"] <= 0:
                continue

            # Calculate how many cases to allocate to this product
            allocation = min(remaining_cases, product["max_additional"])

            # Update the product
            idx = next(i for i, p in enumerate(result_products) if p["product_name"] == product["product_name"])
            result_products[idx]["bulk_quantity"] += allocation

            # Update remaining cases
            remaining_cases -= allocation

            if remaining_cases <= 0:
                break

        # If we still have cases to allocate, add them to the highest ROI product
        if remaining_cases > 0 and products_with_roi:
            best_product = products_with_roi[0]
            idx = next(i for i, p in enumerate(result_products) if p["product_name"] == best_product["product_name"])
            result_products[idx]["bulk_quantity"] += remaining_cases

        # Cap maximum inventory
        result_products = self._cap_maximum_inventory(result_products)

        # Final check: ensure we meet the minimum
        current_total = sum(p.get("bulk_quantity", 0) for p in result_products)
        if current_total < params["bulk_deal_minimum"]:
            # Find a product to add the difference to (prefer highest ROI product)
            if products_with_roi:
                best_product = products_with_roi[0]
                idx = next(i for i, p in enumerate(result_products) if p["product_name"] == best_product["product_name"])
                result_products[idx]["bulk_quantity"] += (params["bulk_deal_minimum"] - current_total)

        return result_products

    def _calculate_product_roi_metrics(self, products, params):
        """
        Calculate ROI metrics for each product.

        Parameters:
        - products: List of product dictionaries
        - params: Dictionary with parameters

        Returns: List of products with additional ROI metrics
        """
        result = []

        for product in products:
            # Skip products with zero price
            if product.get("current_price", 0) <= 0 or product.get("bulk_price", 0) <= 0:
                continue

            # Calculate daily cases
            daily_cases = calculator.calculate_daily_cases(product.get("cases_per_year", 0))

            # Calculate savings per case
            savings_per_case = calculator.calculate_savings_per_case(
                product["current_price"],
                product["bulk_price"],
                product["bottles_per_case"]
            )

            # Calculate days of stock
            days_of_stock = calculator.calculate_days_of_stock(
                product.get("cases_on_hand", 0),
                product.get("cases_per_year", 0)
            )

            # Calculate maximum additional inventory
            max_additional = calculator.calculate_maximum_stock(
                daily_cases, 90, product.get("cases_on_hand", 0)
            )

            # For ROI calculation, we need to estimate the holding time
            holding_time = calculator.calculate_holding_time(1, product.get("cases_per_year", 0))

            # Calculate ROI for a single case
            if holding_time > 0 and product.get("cases_per_year", 0) > 0:
                # Estimate peak investment for a single case
                peak_investment = product["bulk_price"] * product["bottles_per_case"]

                # Calculate ROI
                roi = calculator.calculate_roi(savings_per_case, peak_investment)

                # Calculate annualized ROI
                annual_roi = calculator.calculate_annualized_roi(roi, holding_time)

                # ROI metric is the ROI value
                roi_metric = roi
            else:
                roi = 0
                annual_roi = 0
                roi_metric = 0

            result.append({
                "product_name": product["product_name"],
                "daily_cases": daily_cases,
                "savings_per_case": savings_per_case,
                "days_of_stock": days_of_stock,
                "max_additional": max_additional,
                "roi": roi,
                "annual_roi": annual_roi,
                "roi_metric": roi_metric
            })

        return result

class MinimumAllocationStrategy(AllocationStrategy):
    """Allocate exact minimum quantity proportional to sales volumes."""

    def allocate(self, products, params):
        """
        Allocate exact minimum quantity proportionally.

        Parameters:
        - products: List of product dictionaries
        - params: Dictionary with allocation parameters:
          - bulk_deal_minimum: Minimum total bulk quantity

        Returns: List of product dictionaries with bulk_quantity values set
        """
        # Use proportional allocation strategy
        proportional = ProportionalAllocationStrategy()
        return proportional.allocate(products, params)

def get_allocation_strategy(mode):
    """
    Factory method to get the appropriate allocation strategy.

    Parameters:
    - mode: Allocation mode string ('proportional', 'roi', 'minimum')

    Returns: AllocationStrategy instance
    """
    strategies = {
        "proportional": ProportionalAllocationStrategy(),
        "roi": ROIAllocationStrategy(),
        "minimum": MinimumAllocationStrategy()
    }

    return strategies.get(mode.lower(), ProportionalAllocationStrategy())
