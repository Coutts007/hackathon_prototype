"""
data_generator.py
-----------------
Generates a synthetic dataset of 5,000 households for the
AI-Powered Household Energy Fairness Index (HEFI) prototype.

Run standalone to (re)create data/households.csv:
    python data_generator.py
"""

import os
import numpy as np
import pandas as pd

SEED = 42
N = 5_000
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
OUTPUT_PATH = os.path.join(DATA_DIR, "households.csv")


def generate_households(n: int = N, seed: int = SEED) -> pd.DataFrame:
    """
    Simulate n household records with realistic correlated distributions.

    Returns
    -------
    pd.DataFrame
        DataFrame with one row per household.
    """
    rng = np.random.default_rng(seed)

    household_id = [f"HH_{str(i).zfill(5)}" for i in range(1, n + 1)]

    # Urban / Rural split (~65 % urban)
    urban_or_rural = rng.choice(
        ["Urban", "Rural"], size=n, p=[0.65, 0.35]
    )

    # Household income (₹/month) — log-normal, skewed right
    # Urban households tend to earn more
    income_base = np.where(urban_or_rural == "Urban", 35_000, 18_000)
    household_income = rng.lognormal(
        mean=np.log(income_base), sigma=0.6
    ).astype(int)

    # Household size — Poisson, min 1
    household_size = np.clip(rng.poisson(lam=4, size=n), 1, 12).astype(int)

    # Appliance count — correlated with income
    appliance_count = np.clip(
        (household_income / 10_000 + rng.normal(0, 1, n)).astype(int), 1, 20
    )

    # Renewable energy access — rural households less likely
    renewable_prob = np.where(urban_or_rural == "Urban", 0.45, 0.20)
    renewable_energy_access = np.array(
        [rng.choice(["Yes", "No"], p=[p, 1 - p]) for p in renewable_prob]
    )

    # Electricity dependency score (0–10) — higher for rural, low income
    income_norm = (household_income - household_income.min()) / (
        household_income.max() - household_income.min()
    )
    dep_base = 8 - 5 * income_norm + (urban_or_rural == "Rural").astype(float) * 1.5
    electricity_dependency_score = np.clip(
        dep_base + rng.normal(0, 0.8, n), 0, 10
    ).round(2)

    # Monthly electricity consumption (kWh)
    # Driven by appliance count, household size, and dependency
    consumption_base = (
        50
        + appliance_count * 15
        + household_size * 8
        + electricity_dependency_score * 10
    )
    monthly_electricity_consumption_kwh = np.clip(
        consumption_base + rng.normal(0, 30, n), 10, 2000
    ).round(1)

    df = pd.DataFrame(
        {
            "household_id": household_id,
            "monthly_electricity_consumption_kwh": monthly_electricity_consumption_kwh,
            "household_income": household_income,
            "household_size": household_size,
            "urban_or_rural": urban_or_rural,
            "appliance_count": appliance_count,
            "renewable_energy_access": renewable_energy_access,
            "electricity_dependency_score": electricity_dependency_score,
        }
    )
    return df


def save_dataset(df: pd.DataFrame, path: str = OUTPUT_PATH) -> None:
    """Persist the generated DataFrame to CSV."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_csv(path, index=False)
    print(f"[data_generator] Saved {len(df):,} records → {path}")


if __name__ == "__main__":
    df = generate_households()
    save_dataset(df)
    print(df.head())
    print("\nShape:", df.shape)
    print("\nData types:\n", df.dtypes)
