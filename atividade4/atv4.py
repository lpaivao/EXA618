import json
import csv
from pathlib import Path

base_dir = Path(__file__).resolve().parent
csv_dom = base_dir / "saida_dom.csv"
csv_sax = base_dir / "saida_sax.csv"
arquivo_saida = base_dir / "geojson.json"

arquivo_csv = csv_dom if csv_dom.exists() else csv_sax
if not arquivo_csv.exists():
    raise FileNotFoundError("Nenhum CSV encontrado. Esperado: saida_dom.csv ou saida_sax.csv")

main = {"type": "FeatureCollection", "features": []}

with arquivo_csv.open("r", encoding="utf-8", newline="") as f:
    leitor = csv.DictReader(f)

    for i, linha in enumerate(leitor, start=1):
        lat = float(linha["lat"])
        lon = float(linha["lon"])
        tipo = linha["tipo"].strip()
        nome = linha["nome"].strip()

        feature = {
            "type": "Feature",
            "properties": {
                "id": i,
                "name": nome,
                "amenity": tipo,
            },
            "geometry": {
                "type": "Point",
                "coordinates": [lon, lat],
            },
        }
        main["features"].append(feature)

with arquivo_saida.open("w", encoding="utf-8") as f:
    json.dump(main, f, indent=4, ensure_ascii=False)

print(f"GeoJSON gerado com {len(main['features'])} features em: {arquivo_saida.name}")