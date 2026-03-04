"""Seed the Market Data service with realistic historical sales."""
import asyncio
import random
from datetime import date, timedelta

import httpx
from faker import Faker

fake = Faker()

MARKET_SERVICE = "http://localhost:8002/api/v1/market"
NUM_SALES = 500

ZIP_CODES = [
    "78701", "78702", "78703", "78704", "78745", "78749",
    "75201", "75202", "75204", "75206", "75219",
    "78201", "78204", "78205", "78207", "78210",
    "77001", "77002", "77003", "77006", "77007",
]

ZIP_CITY_MAP = {
    "787": ("Austin", "TX"),
    "752": ("Dallas", "TX"),
    "782": ("San Antonio", "TX"),
    "770": ("Houston", "TX"),
}

PROPERTY_TYPES = ["single_family", "condo", "townhouse", "multi_family"]


def city_for_zip(zip_code: str) -> tuple[str, str]:
    for prefix, (city, state) in ZIP_CITY_MAP.items():
        if zip_code.startswith(prefix):
            return city, state
    return "Unknown", "TX"


def generate_sale():
    zip_code = random.choice(ZIP_CODES)
    city, state = city_for_zip(zip_code)
    prop_type = random.choice(PROPERTY_TYPES)
    sqft = random.randint(800, 4500)
    bedrooms = random.randint(1, 5)
    bathrooms = random.choice([1, 1.5, 2, 2.5, 3, 3.5, 4])

    # Price correlated with sqft
    price_per_sqft = random.uniform(150, 400)
    list_price = int(sqft * price_per_sqft)
    # Sale price within +-5% of list price
    sale_price = int(list_price * random.uniform(0.95, 1.05))
    dom = random.randint(3, 120)

    sale_date = date.today() - timedelta(days=random.randint(1, 365))

    return {
        "mls_number": f"MLS{fake.unique.random_number(digits=7, fix_len=True)}",
        "address": fake.street_address(),
        "city": city,
        "state": state,
        "zip_code": zip_code,
        "property_type": prop_type,
        "sale_price": str(sale_price),
        "list_price": str(list_price),
        "bedrooms": bedrooms,
        "bathrooms": str(bathrooms),
        "square_feet": sqft,
        "lot_size_sqft": random.randint(2000, 15000),
        "year_built": random.randint(1965, 2024),
        "sale_date": sale_date.isoformat(),
        "days_on_market": dom,
        "latitude": str(round(random.uniform(29.0, 33.0), 7)),
        "longitude": str(round(random.uniform(-98.0, -95.0), 7)),
    }


async def main():
    async with httpx.AsyncClient(timeout=30) as client:
        for i in range(NUM_SALES):
            data = generate_sale()
            try:
                resp = await client.post(f"{MARKET_SERVICE}/sales", json=data)
                resp.raise_for_status()
                print(f"[{i+1}/{NUM_SALES}] Recorded sale: {data['city']} {data['zip_code']} - ${data['sale_price']}")
            except httpx.HTTPStatusError as e:
                print(f"[{i+1}/{NUM_SALES}] Error: {e.response.status_code} - {e.response.text[:200]}")
            except httpx.ConnectError:
                print(f"Cannot connect to {MARKET_SERVICE}. Is the service running?")
                return

        # Compute stats for key zip codes
        print("\nComputing market stats...")
        for zip_code in ZIP_CODES[:8]:
            try:
                resp = await client.post(f"{MARKET_SERVICE}/stats/{zip_code}/compute")
                resp.raise_for_status()
                stats = resp.json()
                print(f"  {zip_code}: median=${stats.get('median_price', 'N/A')}, sales={stats.get('total_sales', 0)}")
            except Exception as e:
                print(f"  {zip_code}: Error computing stats - {e}")

    print(f"\nSeeded {NUM_SALES} sales records with market stats.")


if __name__ == "__main__":
    asyncio.run(main())
