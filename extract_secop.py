import requests
import pandas as pd
from io import StringIO

BASE_URL = "https://www.datos.gov.co/resource/r5mq-vv6g.csv"

limit = 50000
offset = 0
all_data = []

while True:
    print(f"Descargando offset {offset}")
    
    url = f"{BASE_URL}?$limit={limit}&$offset={offset}"
    response = requests.get(url)
    
    if response.status_code != 200:
        print("Error en la API")
        break
    
    df = pd.read_csv(StringIO(response.text))
    
    if df.empty:
        break
    
    all_data.append(df)
    offset += limit

final_df = pd.concat(all_data, ignore_index=True)

final_df.to_csv("secop_raw.csv", index=False)

print("✅ Datos descargados")
