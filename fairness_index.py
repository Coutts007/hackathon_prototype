"""
fairness_index.py
-----------------
Core engine for the AI-Powered Household Energy Fairness Index (HEFI).

Responsibilities
----------------
1. preprocess(df)         — encode categoricals, scale numerics
2. train_model(df)        — train RandomForest vulnerability model
3. calculate_hefi(df)     — compute HEFI score (0–100)
4. classify_tariff(score) — map HEFI to tariff tier
5. run_pipeline(df)       — convenience wrapper (preprocess → model → HEFI)

Run standalone to train and save the model:
    python fairness_index.py
"""

import os
import sqlite3
import warnings
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler, LabelEncoder

warnings.filterwarnings("ignore")

# ─── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "models", "rf_model.pkl")
SCALER_PATH = os.path.join(BASE_DIR, "models", "scaler.pkl")
DB_PATH = os.path.join(BASE_DIR, "data", "registry.db")

# ─── Feature groups ───────────────────────────────────────────────────────────
NUMERIC_FEATURES = [
    "monthly_electricity_consumption_kwh",
    "household_income",
    "household_size",
    "appliance_count",
    "electricity_dependency_score",
]
CATEGORICAL_FEATURES = ["urban_or_rural", "renewable_energy_access"]

# HEFI weights (must sum to 1.0)
HEFI_WEIGHTS = {
    "income_vulnerability": 0.30,
    "household_size_factor": 0.20,
    "energy_dependency": 0.30,
    "consumption_anomaly": 0.20,
}


# ─── 0. Database Registry (Phase 2) ───────────────────────────────────────────
def init_db(force=False):
    """Initialize the SQLite registry for households."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if force:
        cursor.execute("DROP TABLE IF EXISTS households")
        
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS households (
            household_id TEXT PRIMARY KEY,
            monthly_electricity_consumption_kwh REAL,
            household_income INTEGER,
            household_size INTEGER,
            urban_or_rural TEXT,
            appliance_count INTEGER,
            renewable_energy_access TEXT,
            electricity_dependency_score REAL,
            income_vulnerability REAL,
            household_size_factor REAL,
            energy_dependency REAL,
            consumption_anomaly REAL,
            ml_adjustment REAL,
            hefi_score REAL,
            tariff_tier TEXT,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Check for missing columns and add them (migration)
    cursor.execute("PRAGMA table_info(households)")
    existing_cols = [row[1] for row in cursor.fetchall()]
    
    # Define expected columns and their types
    expected_schema = {
        "income_vulnerability": "REAL",
        "household_size_factor": "REAL",
        "energy_dependency": "REAL",
        "consumption_anomaly": "REAL",
        "ml_adjustment": "REAL"
    }
    
    for col, dtype in expected_schema.items():
        if col not in existing_cols:
            cursor.execute(f"ALTER TABLE households ADD COLUMN {col} {dtype}")
            
    conn.commit()
    conn.close()

def upsert_households(df: pd.DataFrame):
    """Effectively syncs a DataFrame (CSV or Live) to the DB registry using an atomic strategy."""
    conn = sqlite3.connect(DB_PATH)
    try:
        # We use a temp table + INSERT OR REPLACE for atomic updates in SQLite
        # This prevents data loss and ensures specific IDs are updated correctly
        df.to_sql("temp_households", conn, if_exists="replace", index=False)
        
        conn.execute("""
            INSERT OR REPLACE INTO households (
                household_id, monthly_electricity_consumption_kwh, household_income, 
                household_size, urban_or_rural, appliance_count, renewable_energy_access, 
                electricity_dependency_score, income_vulnerability, household_size_factor, 
                energy_dependency, consumption_anomaly, ml_adjustment, hefi_score, tariff_tier
            )
            SELECT 
                household_id, monthly_electricity_consumption_kwh, household_income, 
                household_size, urban_or_rural, appliance_count, renewable_energy_access, 
                electricity_dependency_score, income_vulnerability, household_size_factor, 
                energy_dependency, consumption_anomaly, ml_adjustment, hefi_score, tariff_tier
            FROM temp_households
        """)
        conn.execute("DROP TABLE temp_households")
        conn.commit()
    finally:
        conn.close()

def recalculate_with_context(updated_row_df: pd.DataFrame) -> pd.DataFrame:
    """
    Recalculates HEFI for a specific update by loading the full registry context.
    Ensures relative features (like income rank) remain accurate.
    """
    conn = sqlite3.connect(DB_PATH)
    try:
        # 1. Load full population
        full_df = pd.read_sql("SELECT * FROM households", conn)
        
        if full_df.empty:
            # Fallback to single-row pipeline if DB is empty
            return run_pipeline(updated_row_df, retrain=False)
        
        # 2. Merge update
        hid = updated_row_df.iloc[0]["household_id"]
        # Remove old version if exists
        full_df = full_df[full_df["household_id"] != hid]
        # Append new version
        full_df = pd.concat([full_df, updated_row_df], ignore_index=True)
        
        # 3. Recalculate for everyone (to maintain correct ranks)
        # Convert to numeric where needed in case SQLite/Pandas type drift
        full_df["household_income"] = pd.to_numeric(full_df["household_income"])
        full_df["household_size"] = pd.to_numeric(full_df["household_size"])
        full_df["monthly_electricity_consumption_kwh"] = pd.to_numeric(full_df["monthly_electricity_consumption_kwh"])
        
        results = run_pipeline(full_df, retrain=False)
        
        # 4. Return just the updated row
        return results[results["household_id"] == hid]
    finally:
        conn.close()


# ─── 1. Preprocessing ─────────────────────────────────────────────────────────
def preprocess(df: pd.DataFrame) -> pd.DataFrame:
    """
    Encode categoricals and scale numeric features.

    Parameters
    ----------
    df : pd.DataFrame
        Raw household data.

    Returns
    -------
    pd.DataFrame
        Preprocessed copy (original df unchanged).
    """
    df = df.copy()

    # Label-encode categoricals (consistent mapping for stability)
    for col in CATEGORICAL_FEATURES:
        if col in df.columns:
            if col == "renewable_energy_access":
                df[col + "_enc"] = np.where(df[col] == "Yes", 1, 0)
            elif col == "urban_or_rural":
                df[col + "_enc"] = np.where(df[col] == "Rural", 1, 0)
            else:
                df[col + "_enc"] = 0

    # Standard-scale numerics (reuse saved scaler if available)
    if os.path.exists(SCALER_PATH):
        scaler = joblib.load(SCALER_PATH)
        existing_features = [f for f in NUMERIC_FEATURES if f in df.columns]
        df[existing_features] = scaler.transform(df[existing_features])
    else:
        scaler = StandardScaler()
        df[NUMERIC_FEATURES] = scaler.fit_transform(df[NUMERIC_FEATURES])
        os.makedirs(os.path.dirname(SCALER_PATH), exist_ok=True)
        joblib.dump(scaler, SCALER_PATH)

    return df


# ─── 2. Synthetic vulnerability target ────────────────────────────────────────
def _make_vulnerability_target(df_raw: pd.DataFrame) -> np.ndarray:
    """
    Build a deterministic vulnerability score from raw features
    so the RandomForest has a meaningful regression target.
    Formula blends income (inverted), size, dependency, and renewables.
    """
    income_norm = df_raw["household_income"] / df_raw["household_income"].max()
    size_norm = df_raw["household_size"] / df_raw["household_size"].max()
    dep_norm = df_raw["electricity_dependency_score"] / 10.0
    renewable_penalty = (df_raw["renewable_energy_access"] == "No").astype(float)
    rural_penalty = (df_raw["urban_or_rural"] == "Rural").astype(float)

    score = (
        0.35 * (1 - income_norm)
        + 0.20 * size_norm
        + 0.25 * dep_norm
        + 0.10 * renewable_penalty
        + 0.10 * rural_penalty
    )
    # Clip and scale to [0, 1]
    return np.clip(score, 0, 1).values


# ─── 3. Model training ────────────────────────────────────────────────────────
def train_model(df_raw: pd.DataFrame) -> RandomForestRegressor:
    """
    Train a RandomForestRegressor to predict household vulnerability.

    Parameters
    ----------
    df_raw : pd.DataFrame
        Raw (unscaled) household data.

    Returns
    -------
    RandomForestRegressor
        Trained model, also saved to models/rf_model.pkl.
    """
    df_proc = preprocess(df_raw)

    feature_cols = NUMERIC_FEATURES + [c + "_enc" for c in CATEGORICAL_FEATURES]
    X = df_proc[feature_cols].values
    y = _make_vulnerability_target(df_raw)

    model = RandomForestRegressor(
        n_estimators=200,
        max_depth=10,
        min_samples_leaf=5,
        n_jobs=-1,
        random_state=42,
    )
    model.fit(X, y)

    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    print(f"[fairness_index] Model saved → {MODEL_PATH}")
    return model


# ─── 4. HEFI calculation ──────────────────────────────────────────────────────
def _component_income_vulnerability(df: pd.DataFrame) -> pd.Series:
    """Inverted income rank: poorest households score highest (0–1)."""
    return 1 - (df["household_income"].rank(pct=True))


def _component_household_size(df: pd.DataFrame) -> pd.Series:
    """Larger households score higher (0–1)."""
    mn, mx = df["household_size"].min(), df["household_size"].max()
    return (df["household_size"] - mn) / (mx - mn + 1e-9)


def _component_energy_dependency(df: pd.DataFrame) -> pd.Series:
    """Higher electricity dependency → higher score (0–1)."""
    return df["electricity_dependency_score"] / 10.0


def _component_consumption_anomaly(df: pd.DataFrame) -> pd.Series:
    """
    Flag households whose consumption is unusually LOW relative to
    their appliance count — suggests they may be under-reported or
    energy-deprived.
    """
    expected = df["appliance_count"] * 25
    ratio = df["monthly_electricity_consumption_kwh"] / (expected + 1e-9)
    # Lower ratio (consuming less than expected) → higher vulnerability
    anomaly = 1 - np.clip(ratio, 0, 2) / 2
    return anomaly


def calculate_hefi(df_raw: pd.DataFrame, model=None) -> pd.DataFrame:
    """
    Compute HEFI scores for every household in df_raw.

    The raw ML model prediction is used as a tiebreaker/adjuster
    (±5 points), so the formula components remain the primary driver.

    Parameters
    ----------
    df_raw   : pd.DataFrame  — raw household data
    model    : trained sklearn model (optional; loaded from disk if None)

    Returns
    -------
    pd.DataFrame
        Original df with extra columns:
        income_vulnerability, household_size_factor, energy_dependency,
        consumption_anomaly, ml_adjustment, hefi_score, tariff_tier
    """
    df = df_raw.copy()

    # Components (0–1 each)
    df["income_vulnerability"] = _component_income_vulnerability(df)
    df["household_size_factor"] = _component_household_size(df)
    df["energy_dependency"] = _component_energy_dependency(df)
    df["consumption_anomaly"] = _component_consumption_anomaly(df)

    # Weighted sum → scale to 0–100
    raw_hefi = (
        HEFI_WEIGHTS["income_vulnerability"] * df["income_vulnerability"]
        + HEFI_WEIGHTS["household_size_factor"] * df["household_size_factor"]
        + HEFI_WEIGHTS["energy_dependency"] * df["energy_dependency"]
        + HEFI_WEIGHTS["consumption_anomaly"] * df["consumption_anomaly"]
    ) * 100

    # ML model adjustment (optional ±5 pts)
    if model is None and os.path.exists(MODEL_PATH):
        model = joblib.load(MODEL_PATH)

    if model is not None:
        df_proc = preprocess(df_raw)
        feature_cols = NUMERIC_FEATURES + [c + "_enc" for c in CATEGORICAL_FEATURES]
        pred = model.predict(df_proc[feature_cols].values)  # 0–1
        df["ml_adjustment"] = (pred - 0.5) * 10  # ±5 pts
    else:
        df["ml_adjustment"] = 0.0

    df["hefi_score"] = np.clip(raw_hefi + df["ml_adjustment"], 0, 100).round(2)
    df["tariff_tier"] = df["hefi_score"].apply(classify_tariff)

    return df


# ─── 5. Tariff classification ─────────────────────────────────────────────────
def classify_tariff(score: float) -> str:
    """
    Map a HEFI score to a tariff tier.

    70–100 → Subsidized
    40–69  → Standard
    0–39   → Premium
    """
    if score >= 70:
        return "Subsidized"
    elif score >= 40:
        return "Standard"
    else:
        return "Premium"


# ─── 6. Convenience pipeline ──────────────────────────────────────────────────
def run_pipeline(df_raw: pd.DataFrame, retrain: bool = False) -> pd.DataFrame:
    """
    Full pipeline: (optionally retrain) → calculate HEFI.

    Parameters
    ----------
    df_raw  : raw household DataFrame
    retrain : if True, always retrain the model from scratch

    Returns
    -------
    pd.DataFrame with HEFI scores and tariff tiers appended.
    """
    if retrain or not os.path.exists(MODEL_PATH):
        model = train_model(df_raw)
    else:
        model = joblib.load(MODEL_PATH)

    return calculate_hefi(df_raw, model=model)


# ─── Standalone execution ─────────────────────────────────────────────────────
if __name__ == "__main__":
    from data_generator import generate_households

    print("Generating dataset …")
    raw = generate_households()

    print("Running pipeline …")
    result = run_pipeline(raw, retrain=True)

    print("\nSample output:")
    print(
        result[
            ["household_id", "household_income", "hefi_score", "tariff_tier"]
        ].head(10)
    )
    print("\nTariff distribution:\n", result["tariff_tier"].value_counts())
    print("\nHEFI stats:\n", result["hefi_score"].describe())
