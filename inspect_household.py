"""
inspect_household.py
--------------------
Utility script to pick a random household from the dataset and
calculate its HEFI score using the fairness engine.
"""

import os
import sqlite3
import pandas as pd
from fairness_index import run_pipeline, DB_PATH

def inspect_random():
    try:
        # 1. Prefer SQLite Registry (Phase 2), fallback to CSV
        if os.path.exists(DB_PATH):
            conn = sqlite3.connect(DB_PATH)
            results = pd.read_sql("SELECT * FROM households", conn)
            conn.close()
            source = "SQLite Registry"
        else:
            df_raw = pd.read_csv("data/households.csv")
            results = run_pipeline(df_raw)
            source = "CSV Export"
        
        if results.empty:
            print("Registry is empty. Run analysis in the dashboard first.")
            return

        # 2. Pick a random household
        sample = results.sample(1).iloc[0]
        
        print("="*40)
        print(f" HOUSEHOLD INSPECTION: {sample['household_id']} (via {source})")
        print("="*40)
        print(f"Income:         ₹{sample['household_income']:,}/mo")
        print(f"Size:           {sample['household_size']} members")
        print(f"Urban/Rural:    {sample['urban_or_rural']}")
        print(f"Appliances:     {sample['appliance_count']}")
        print(f"Dependency:     {sample['electricity_dependency_score']}/10")
        print(f"Consumption:    {sample['monthly_electricity_consumption_kwh']} kWh")
        print("-"*40)
        print(f"HEFI SCORE:     {sample['hefi_score']} / 100")
        print(f"TARIFF TIER:    {sample['tariff_tier']}")
        print("="*40)
        print("\nScore Components (0-1):")
        print(f" - Income Vuln:    {sample['income_vulnerability']:.2f}")
        print(f" - Size Factor:    {sample['household_size_factor']:.2f}")
        print(f" - Energy Dep:     {sample['energy_dependency']:.2f}")
        print(f" - Consumption An: {sample['consumption_anomaly']:.2f}")
        print(f" - ML Adjustment:  {sample['ml_adjustment']:.2f}")

    except FileNotFoundError:
        print("Error: households.csv not found. Run 'python data_generator.py' first.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    inspect_random()
