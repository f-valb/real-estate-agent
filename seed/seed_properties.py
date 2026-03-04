"""Seed the Property Listing service with realistic fake data."""
import asyncio
import random
from decimal import Decimal

import httpx
from faker import Faker

fake = Faker()

PROPERTY_SERVICE = "http://localhost:8000/api/v1/listings"
NUM_PROPERTIES = 50

PROPERTY_TYPES = ["single_family", "condo", "townhouse", "multi_family", "land"]
CITIES = [
    ("Austin", "TX", ["78701", "78702", "78703", "78704", "78745", "78749"]),
    ("Dallas", "TX", ["75201", "75202", "75204", "75206", "75219"]),
    ("San Antonio", "TX", ["78201", "78204", "78205", "78207", "78210"]),
    ("Houston", "TX", ["77001", "77002", "77003", "77006", "77007"]),
]


def generate_property():
    city, state, zips = random.choice(CITIES)
    prop_type = random.choice(PROPERTY_TYPES)
    bedrooms = random.randint(1, 6) if prop_type != "land" else None
    bathrooms = random.choice([1, 1.5, 2, 2.5, 3, 3.5, 4]) if prop_type != "land" else None
    sqft = random.randint(800, 5000) if prop_type != "land" else None
    price = random.randint(150_000, 1_200_000)

    return {
        "mls_number": f"MLS{fake.unique.random_number(digits=7, fix_len=True)}",
        "property_type": prop_type,
        "address_line1": fake.street_address(),
        "city": city,
        "state": state,
        "zip_code": random.choice(zips),
        "latitude": str(round(random.uniform(29.0, 33.0), 7)),
        "longitude": str(round(random.uniform(-98.0, -95.0), 7)),
        "list_price": str(price),
        "bedrooms": bedrooms,
        "bathrooms": str(bathrooms) if bathrooms else None,
        "square_feet": sqft,
        "lot_size_sqft": random.randint(2000, 20000),
        "year_built": random.randint(1960, 2024),
        "description": fake.paragraph(nb_sentences=3),
        "listing_date": fake.date_between(start_date="-6m", end_date="today").isoformat(),
    }


async def main():
    async with httpx.AsyncClient(timeout=30) as client:
        for i in range(NUM_PROPERTIES):
            data = generate_property()
            try:
                resp = await client.post(PROPERTY_SERVICE, json=data)
                resp.raise_for_status()
                print(f"[{i+1}/{NUM_PROPERTIES}] Created listing: {data['mls_number']} - {data['city']}")
            except httpx.HTTPStatusError as e:
                print(f"[{i+1}/{NUM_PROPERTIES}] Error: {e.response.status_code} - {e.response.text[:200]}")
            except httpx.ConnectError:
                print(f"Cannot connect to {PROPERTY_SERVICE}. Is the service running?")
                return

    print(f"\nSeeded {NUM_PROPERTIES} properties.")


if __name__ == "__main__":
    asyncio.run(main())
