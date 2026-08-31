# %% Read Original CSV file

import json
from pathlib import Path

import pandas as pd

base_dir = Path(__file__).resolve().parent.parent
csv_path = base_dir / "data" / "sources" / "financial_transactions_raw.csv"
json_path = base_dir / "data" / "sources" / "simulated_datasources.json"

df = pd.read_csv(csv_path)

# %% Create one JSON for each source system to simulate different datasources
# Preserve CSV-style missing values as the string "NaN" so JSON remains valid
# while keeping the original sentinel value visible in the exported data.
d = {}
for source_system, df_ss in df.groupby("source_system"):
    df_ss = df_ss.astype(object).where(pd.notna(df_ss), "NaN")
    d[source_system] = df_ss.to_dict(orient="records")

with open(json_path, "w", encoding="utf-8") as f:
    json.dump(d, f, indent=4, ensure_ascii=False)
    f.write("\n")

# %%
