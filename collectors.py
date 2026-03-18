"""
collectors.py
--------------
Service layer for digital data ingestion.
Mocks Smart Meter, Government, and Field App streams.
"""

import time
import random
import pandas as pd
import numpy as np

class MeterStream:
    """Mocks Advanced Metering Infrastructure (AMI)."""
    def __init__(self, household_ids):
        self.household_ids = household_ids
        
    def poll_consumption(self, batch_size=5):
        """Returns a batch of consumption updates."""
        targets = random.sample(self.household_ids, min(len(self.household_ids), batch_size))
        updates = []
        for hid in targets:
            # Baseline + variance
            updates.append({
                "household_id": hid,
                "monthly_electricity_consumption_kwh": round(random.uniform(50, 600), 1),
                "timestamp": time.time()
            })
        return updates

class GovtAPI:
    """Mocks Government Social Welfare & Tax Data."""
    def get_socio_economic_data(self, household_id):
        """Simulates API call for income data."""
        # In real life, this would be a secure API call
        return {
            "household_income": random.randint(15000, 120000),
            "household_size": random.randint(1, 8)
        }

class FieldAppCollector:
    """Mocks data synced from field worker tablets."""
    def sync_field_data(self):
        """Simulates field worker submitting a digital form."""
        return {
            "appliance_count": random.randint(2, 15),
            "renewable_energy_access": random.choice(["Yes", "No"]),
            "electricity_dependency_score": round(random.uniform(1, 9), 2)
        }

def simulate_ingestion_log():
    """Returns a list of mock log entries for the dashboard."""
    sources = ["[METER-01]", "[GOVT-SOC-API]", "[FIELD-SYNC]"]
    events = [
        "Ingested consumption data batch",
        "Updated income percentile from treasury",
        "Synced field verification for HH_772",
        "Authenticated service worker #8821",
        "Connection healthy: Meter-Mesh-04"
    ]
    return f"{random.choice(sources)} {random.choice(events)}"
