import time
from pathlib import Path
from xml.dom.minidom import parse
from xml.parsers import expat


caminho_arquivo = Path(__file__).with_name("map.osm")
chaves_tipo = ["amenity", "shop", "tourism", "office", "craft", "leisure", "healthcare"]


# DOM
inicio_dom = time.perf_counter()
documento = parse(str(caminho_arquivo))
dados_dom = []
coordenadas_nos_dom = {}

for no in documento.getElementsByTagName("node"):
    id_no = no.getAttribute("id")
    lat = no.getAttribute("lat")
    lon = no.getAttribute("lon")
    if id_no and lat and lon:
        coordenadas_nos_dom[id_no] = (float(lat), float(lon))

for no in documento.getElementsByTagName("node"):
    tags = {}
    for tag in no.getElementsByTagName("tag"):
        if tag.parentNode is no:
            tags[tag.getAttribute("k")] = tag.getAttribute("v")

    tipo = None
    for chave in chaves_tipo:
        if chave in tags and tags[chave]:
            tipo = f"{chave}:{tags[chave]}"
            break

    nome = tags.get("name", "").strip()
    lat = no.getAttribute("lat")
    lon = no.getAttribute("lon")

    if tipo and nome and lat and lon:
        dados_dom.append((float(lat), float(lon), tipo, nome))

for via in documento.getElementsByTagName("way"):
    tags = {}
    for tag in via.getElementsByTagName("tag"):
        if tag.parentNode is via:
            tags[tag.getAttribute("k")] = tag.getAttribute("v")

    tipo = None
    for chave in chaves_tipo:
        if chave in tags and tags[chave]:
            tipo = f"{chave}:{tags[chave]}"
            break

    nome = tags.get("name", "").strip()
    if not tipo or not nome:
        continue

    referencias = []
    for no_ref in via.getElementsByTagName("nd"):
        if no_ref.parentNode is via:
            referencia = no_ref.getAttribute("ref")
            if referencia:
                referencias.append(referencia)

    pontos = [coordenadas_nos_dom[ref] for ref in referencias if ref in coordenadas_nos_dom]
    if not pontos:
        continue

    media_lat = sum(p[0] for p in pontos) / len(pontos)
    media_lon = sum(p[1] for p in pontos) / len(pontos)
    dados_dom.append((media_lat, media_lon, tipo, nome))

dados_dom.sort(key=lambda item: (item[3].lower(), item[2]))
fim_dom = time.perf_counter()


# SAX (estilo evento usando Expat)
inicio_sax = time.perf_counter()
dados_sax = []
coordenadas_nos_sax = {}

tipo_elemento = None
tags_atuais = {}
referencias_atuais = []
lat_atual = None
lon_atual = None


def inicio_elemento(nome, attrs):
    global tipo_elemento, tags_atuais, referencias_atuais, lat_atual, lon_atual

    if nome == "node":
        tipo_elemento = "node"
        tags_atuais = {}
        referencias_atuais = []
        lat_atual = float(attrs["lat"]) if "lat" in attrs else None
        lon_atual = float(attrs["lon"]) if "lon" in attrs else None

        id_no = attrs.get("id", "")
        if id_no and lat_atual is not None and lon_atual is not None:
            coordenadas_nos_sax[id_no] = (lat_atual, lon_atual)

    elif nome == "way":
        tipo_elemento = "way"
        tags_atuais = {}
        referencias_atuais = []
        lat_atual = None
        lon_atual = None

    elif nome == "tag" and tipo_elemento in ["node", "way"]:
        chave = attrs.get("k", "")
        valor = attrs.get("v", "")
        tags_atuais[chave] = valor

    elif nome == "nd" and tipo_elemento == "way":
        referencia = attrs.get("ref", "")
        if referencia:
            referencias_atuais.append(referencia)


def fim_elemento(nome):
    global tipo_elemento, tags_atuais, referencias_atuais, lat_atual, lon_atual

    if nome == "node" and tipo_elemento == "node":
        tipo = None
        for chave in chaves_tipo:
            if chave in tags_atuais and tags_atuais[chave]:
                tipo = f"{chave}:{tags_atuais[chave]}"
                break

        nome_local = tags_atuais.get("name", "").strip()
        if tipo and nome_local and lat_atual is not None and lon_atual is not None:
            dados_sax.append((lat_atual, lon_atual, tipo, nome_local))

        tipo_elemento = None
        tags_atuais = {}
        referencias_atuais = []
        lat_atual = None
        lon_atual = None

    elif nome == "way" and tipo_elemento == "way":
        tipo = None
        for chave in chaves_tipo:
            if chave in tags_atuais and tags_atuais[chave]:
                tipo = f"{chave}:{tags_atuais[chave]}"
                break

        nome_local = tags_atuais.get("name", "").strip()
        if tipo and nome_local:
            pontos = [coordenadas_nos_sax[ref] for ref in referencias_atuais if ref in coordenadas_nos_sax]
            if pontos:
                media_lat = sum(p[0] for p in pontos) / len(pontos)
                media_lon = sum(p[1] for p in pontos) / len(pontos)
                dados_sax.append((media_lat, media_lon, tipo, nome_local))

        tipo_elemento = None
        tags_atuais = {}
        referencias_atuais = []
        lat_atual = None
        lon_atual = None


parser = expat.ParserCreate()
parser.StartElementHandler = inicio_elemento
parser.EndElementHandler = fim_elemento

with open(caminho_arquivo, "rb") as arquivo:
    parser.Parse(arquivo.read(), True)

dados_sax.sort(key=lambda item: (item[3].lower(), item[2]))
fim_sax = time.perf_counter()


# Saida
print(f"\nDOM - mostrando {min(15, len(dados_dom))} de {len(dados_dom)}")
print("-" * 90)
for lat, lgt, tipo, nome in dados_dom[:15]:
    print(f"lat={lat:.7f} | lgt={lgt:.7f} | tipo={tipo:<25} | nome={nome}")

print(f"\nSAX - mostrando {min(15, len(dados_sax))} de {len(dados_sax)}")
print("-" * 90)
for lat, lgt, tipo, nome in dados_sax[:15]:
    print(f"lat={lat:.7f} | lgt={lgt:.7f} | tipo={tipo:<25} | nome={nome}")

tempo_dom_ms = (fim_dom - inicio_dom) * 1000
tempo_sax_ms = (fim_sax - inicio_sax) * 1000

print("\nTempo de processamento")
print("-" * 90)
print(f"DOM: {tempo_dom_ms:.2f} ms")
print(f"SAX: {tempo_sax_ms:.2f} ms")

if set(dados_dom) == set(dados_sax):
    print("Consistencia: DOM e SAX encontraram os mesmos estabelecimentos.")
else:
    print("Consistencia: DOM e SAX encontraram resultados diferentes.")