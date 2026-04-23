import pandas as pd
from sqlalchemy import create_engine

engine = create_engine("postgresql://admin:admin@localhost:5432/cividata")

df = pd.read_sql("SELECT * FROM raw.secop_raw", engine)

# Normalizar columnas
df.columns = df.columns.str.lower()

# Limpiar valores
if 'valor_contrato' in df.columns:
    df['valor_contrato'] = pd.to_numeric(df['valor_contrato'], errors='coerce')

# Quitar nulos importantes
df = df.dropna()

# Quitar duplicados
df = df.drop_duplicates()

# Guardar en marts
df.to_sql("secop_clean", engine, schema="marts", if_exists="replace", index=False)

print("✅ Datos limpios en MARTS")
