from sqlalchemy import create_engine
import pandas as pd

engine = create_engine("postgresql://admin:admin@localhost:5432/cividata")

df = pd.read_csv("secop_raw.csv")

df.to_sql("secop_raw", engine, schema="raw", if_exists="replace", index=False)

print("✅ Datos cargados en RAW")
