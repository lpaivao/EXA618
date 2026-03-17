import time
from pathlib import Path
import xml.sax
from xml.dom.minidom import parse


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


# SAX (estilo evento usando xml.sax.ContentHandler)
inicio_sax = time.perf_counter()
class Listener(xml.sax.ContentHandler):
    def __init__(self, chaves):
        self.currentData = ""
        self.chaves_tipo = chaves
        self.dados = []
        self.coordenadas_nos = {}
        self.tipo_elemento = None
        self.tags_atuais = {}
        self.referencias_atuais = []
        self.lat_atual = None
        self.lon_atual = None

    def startElement(self, tag, attributes):
        self.currentData = ""

        if tag == "node":
            self.tipo_elemento = "node"
            self.tags_atuais = {}
            self.referencias_atuais = []
            self.lat_atual = float(attributes["lat"]) if "lat" in attributes else None
            self.lon_atual = float(attributes["lon"]) if "lon" in attributes else None

            id_no = attributes.get("id", "")
            if id_no and self.lat_atual is not None and self.lon_atual is not None:
                self.coordenadas_nos[id_no] = (self.lat_atual, self.lon_atual)

        elif tag == "way":
            self.tipo_elemento = "way"
            self.tags_atuais = {}
            self.referencias_atuais = []
            self.lat_atual = None
            self.lon_atual = None

        elif tag == "tag" and self.tipo_elemento in ["node", "way"]:
            chave = attributes.get("k", "")
            valor = attributes.get("v", "")
            self.tags_atuais[chave] = valor

        elif tag == "nd" and self.tipo_elemento == "way":
            referencia = attributes.get("ref", "")
            if referencia:
                self.referencias_atuais.append(referencia)

    def endElement(self, tag):
        if tag == "node" and self.tipo_elemento == "node":
            tipo = None
            for chave in self.chaves_tipo:
                if chave in self.tags_atuais and self.tags_atuais[chave]:
                    tipo = f"{chave}:{self.tags_atuais[chave]}"
                    break

            nome_local = self.tags_atuais.get("name", "").strip()
            if tipo and nome_local and self.lat_atual is not None and self.lon_atual is not None:
                self.dados.append((self.lat_atual, self.lon_atual, tipo, nome_local))

            self.tipo_elemento = None
            self.tags_atuais = {}
            self.referencias_atuais = []
            self.lat_atual = None
            self.lon_atual = None

        elif tag == "way" and self.tipo_elemento == "way":
            tipo = None
            for chave in self.chaves_tipo:
                if chave in self.tags_atuais and self.tags_atuais[chave]:
                    tipo = f"{chave}:{self.tags_atuais[chave]}"
                    break

            nome_local = self.tags_atuais.get("name", "").strip()
            if tipo and nome_local:
                pontos = [self.coordenadas_nos[ref] for ref in self.referencias_atuais if ref in self.coordenadas_nos]
                if pontos:
                    media_lat = sum(p[0] for p in pontos) / len(pontos)
                    media_lon = sum(p[1] for p in pontos) / len(pontos)
                    self.dados.append((media_lat, media_lon, tipo, nome_local))

            self.tipo_elemento = None
            self.tags_atuais = {}
            self.referencias_atuais = []
            self.lat_atual = None
            self.lon_atual = None

    def characters(self, content):
        self.currentData += content


parser = xml.sax.make_parser()
handler = Listener(chaves_tipo)
parser.setContentHandler(handler)
parser.parse(str(caminho_arquivo))

dados_sax = handler.dados

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