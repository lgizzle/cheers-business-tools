import os
import json

# Mapping from old keys to new keys
PRODUCT_KEY_MAP = {
    "name": "product_name",
    "priceSmall": "current_price",
    "priceBulk": "bulk_price",
    "onHandCases": "on_hand",
    "annualCases": "annual_cases",
    "bottlesPerCase": "bottles_per_case",
    "bulkCases": "bulk_quantity"
}

SCENARIO_DIR = "scenarios/multi_product"

def migrate_product(product):
    return {PRODUCT_KEY_MAP.get(k, k): v for k, v in product.items()}

def migrate_file(filepath):
    with open(filepath, "r") as f:
        data = json.load(f)
    if "products" in data:
        data["products"] = [migrate_product(p) for p in data["products"]]
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Migrated: {filepath}")

def main():
    for filename in os.listdir(SCENARIO_DIR):
        if filename.endswith(".json"):
            migrate_file(os.path.join(SCENARIO_DIR, filename))

if __name__ == "__main__":
    main()
