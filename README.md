# ⚡ AI-Powered Household Energy Fairness Index (HEFI)

A prototype system that calculates a **Household Energy Fairness Index (HEFI)** to help regulators design equitable electricity tariffs. Instead of classifying households purely on consumption, HEFI uses multiple socio-economic and energy-use variables to produce a vulnerability score and recommend appropriate tariff tiers.

---

## Project Structure

```
myapp/
│
├── data/                          ← Generated/uploaded CSVs & registry.db
├── models/                        ← Saved ML model & scaler (.pkl)
│
├── data_generator.py              ← Simulates 5,000 household records
├── fairness_index.py              ← Core HEFI engine (Preprocessing, ML, DB sync)
├── collectors.py                  ← Mock Digital Collectors (Smart Meter, Govt API)
├── app.py                         ← Admin dashboard (System Monitoring & Bulk Analysis)
├── client_app.py                  ← Citizen portal (Personal HEFI & Self-Reporting)
├── chatbot_logic.py               ← AI Support Bot logic
├── inspect_household.py           ← CLI tool for random inspections
└── README.md
```

---

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. (Optional) Pre-generate the dataset

```bash
python data_generator.py
```
Saves `data/households.csv`.

### 3. (Optional) Pre-train the model

```bash
python fairness_index.py
```
Saves `models/rf_model.pkl` and `models/scaler.pkl`.

### 4. Launch the dashboard

```bash
streamlit run app.py
```
The app opens automatically at **http://localhost:8501**.

---

## Using the Dashboard

| Step | Action |
|------|--------|
| 1 | Choose **Simulate dataset** (pick size) or **Upload CSV** |
| 2 | Tick **Re-train model** if you want to force retraining |
| 3 | Click **▶ Run Analysis** |
| 4 | Explore **Visualizations**, **Data Table**, and **Methodology** tabs |
| 5 | Download results via the **CSV export** button |

---

## Client Portal (Phase 3) 🏠

The **Citizen Portal** allows households to interact directly with the fairness system:
- **Personal HEFI Breakdown**: Users see exactly how their score is calculated.
- **Self-Reporting**: Households can update their size, income, or renewable status to request immediate re-indexing.
- **AI Support Chat**: An instant chatbot to answer "What is HEFI?", "How to lower bills?", and tier-specific questions.

**How to Run the Client Portal:**
```bash
streamlit run client_app.py
```
*(Login with any valid Household ID from the database, e.g., `HH_001`)*

---

## Digital Collection (Phase 2)

The system now supports real-world digital architecture:
- **Smart Meter Polling**: Mock consumption updates via `collectors.py`.
- **Govt Data Integration**: Mock socio-economic lookups for automated fairness checks.
- **SQLite Registry**: Data is stored in `data/registry.db` for transactional efficiency.

To test the digital stream, go to the **🛰️ Digital Ingestion** tab in the dashboard and click **Trigger Mock Data Sync**.

---

## HEFI Formula

```
HEFI = 100 × (
    0.30 × income_vulnerability    +
    0.20 × household_size_factor   +
    0.30 × energy_dependency       +
    0.20 × consumption_anomaly
) ± ML_adjustment (±5 pts)
```

## Tariff Tiers

| HEFI Range | Tariff Tier |
|-----------|-------------|
| 70 – 100 | 🟢 Subsidized |
| 40 – 69  | 🔵 Standard   |
| 0  – 39  | 🔴 Premium    |

---

## CSV Upload Format

If uploading your own data, the CSV must contain these columns:

| Column | Type | Example |
|--------|------|---------|
| `household_id` | string | HH_00001 |
| `monthly_electricity_consumption_kwh` | float | 245.5 |
| `household_income` | int | 32000 |
| `household_size` | int | 4 |
| `urban_or_rural` | Urban / Rural | Urban |
| `appliance_count` | int | 7 |
| `renewable_energy_access` | Yes / No | No |
| `electricity_dependency_score` | float 0–10 | 6.8 |

---

## Technology Stack

- **Python 3.10+**
- **scikit-learn** — RandomForestRegressor
- **Streamlit** — dashboard
- **Pandas / NumPy** — data processing
- **Matplotlib / Seaborn** — visualizations
