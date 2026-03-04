"""Seed the CRM Contact service with realistic fake data."""
import asyncio
import random

import httpx
from faker import Faker

fake = Faker()

CRM_SERVICE = "http://localhost:8001/api/v1/contacts"
NUM_CONTACTS = 100

CONTACT_TYPES = ["buyer", "seller", "agent", "vendor", "lead"]
PIPELINE_STAGES = ["new", "contacted", "qualified", "proposal", "negotiation", "closed_won"]
LEAD_SOURCES = ["website", "referral", "open_house", "zillow", "realtor.com", "social_media"]
TAGS = ["hot_lead", "investor", "first_time_buyer", "relocating", "luxury", "downsizing", "upsizing"]
CITIES = ["Austin", "Dallas", "San Antonio", "Houston"]


def generate_contact():
    contact_type = random.choices(
        CONTACT_TYPES,
        weights=[35, 25, 15, 10, 15],
        k=1,
    )[0]

    preferences = None
    if contact_type in ("buyer", "lead"):
        preferences = {
            "min_price": random.randint(100_000, 400_000),
            "max_price": random.randint(400_000, 1_500_000),
            "bedrooms": random.randint(2, 5),
            "preferred_areas": random.sample(CITIES, k=random.randint(1, 3)),
            "property_types": random.sample(
                ["single_family", "condo", "townhouse"], k=random.randint(1, 2)
            ),
        }

    return {
        "contact_type": contact_type,
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "email": fake.email(),
        "phone": fake.phone_number(),
        "company": fake.company() if contact_type in ("agent", "vendor") else None,
        "address": fake.address().replace("\n", ", "),
        "pipeline_stage": "new",
        "lead_source": random.choice(LEAD_SOURCES),
        "notes": fake.sentence() if random.random() > 0.5 else None,
        "preferences": preferences,
    }


async def main():
    async with httpx.AsyncClient(timeout=30) as client:
        created_ids = []

        for i in range(NUM_CONTACTS):
            data = generate_contact()
            try:
                resp = await client.post(CRM_SERVICE, json=data)
                resp.raise_for_status()
                contact = resp.json()
                created_ids.append(contact["id"])
                print(f"[{i+1}/{NUM_CONTACTS}] Created: {data['first_name']} {data['last_name']} ({data['contact_type']})")
            except httpx.HTTPStatusError as e:
                print(f"[{i+1}/{NUM_CONTACTS}] Error: {e.response.status_code} - {e.response.text[:200]}")
            except httpx.ConnectError:
                print(f"Cannot connect to {CRM_SERVICE}. Is the service running?")
                return

        # Add some tags
        for contact_id in random.sample(created_ids, min(30, len(created_ids))):
            tag = random.choice(TAGS)
            try:
                await client.post(
                    f"{CRM_SERVICE}/{contact_id}/tags",
                    json={"tag": tag},
                )
            except Exception:
                pass

    print(f"\nSeeded {NUM_CONTACTS} contacts with tags.")


if __name__ == "__main__":
    asyncio.run(main())
