import html
import sys
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen


DEFAULT_TIMEOUT_SECONDS = 15
DEFAULT_USER_AGENT = "Mozilla/5.0 (compatible; EXA618-atividade5-parser/1.0)"


@dataclass
class PageData:
    seed_url: str
    final_url: str = ""
    titles: list[str] = field(default_factory=list)
    first_image_url: str = ""
    error: str = ""


class StudentPageParser(HTMLParser):
    def __init__(self, base_url: str) -> None:
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.titles: list[str] = []
        self._open_title_parts: list[str] | None = None
        self.first_image_url = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        normalized = tag.lower()
        attrs_dict = {k.lower(): (v if v is not None else "") for k, v in attrs}

        if normalized == "title":
            self._open_title_parts = []

        if normalized == "img" and not self.first_image_url:
            raw_src = attrs_dict.get("src", "").strip()
            if raw_src:
                self.first_image_url = urljoin(self.base_url, raw_src)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "title" and self._open_title_parts is not None:
            text = normalize_whitespace("".join(self._open_title_parts))
            if text:
                self.titles.append(text)
            self._open_title_parts = None

    def handle_data(self, data: str) -> None:
        if self._open_title_parts is not None:
            self._open_title_parts.append(data)


def normalize_whitespace(value: str) -> str:
    return " ".join(value.split()).strip()


def read_seeds_file(path: Path) -> list[str]:
    seeds: list[str] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        seeds.append(line)
    return seeds


def fetch_html(url: str, timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS) -> tuple[str, str]:
    request = Request(url=url, headers={"User-Agent": DEFAULT_USER_AGENT})
    with urlopen(request, timeout=timeout_seconds) as response:
        final_url = response.geturl()
        content_type = response.headers.get("Content-Type", "")
        if "text/html" not in content_type.lower() and "application/xhtml+xml" not in content_type.lower():
            raise ValueError(f"Resposta nao-HTML ({content_type or 'desconhecido'})")

        payload = response.read()
        charset = response.headers.get_content_charset() or "utf-8"
        html_text = payload.decode(charset, errors="replace")
        return html_text, final_url


def parse_student_page(seed_url: str) -> PageData:
    data = PageData(seed_url=seed_url)
    try:
        html_text, final_url = fetch_html(seed_url)
        parser = StudentPageParser(base_url=final_url)
        parser.feed(html_text)
        parser.close()

        data.final_url = final_url
        data.titles = parser.titles
        data.first_image_url = parser.first_image_url
    except HTTPError as exc:
        data.error = f"HTTP {exc.code}: {exc.reason}"
    except URLError as exc:
        data.error = f"Falha de conexao: {exc.reason}"
    except TimeoutError:
        data.error = "Tempo de requisicao excedido"
    except Exception as exc:
        data.error = f"Erro inesperado: {exc}"
    return data


def build_output_html(results: list[PageData]) -> str:
    ok_count = sum(1 for item in results if not item.error)
    failed_count = len(results) - ok_count

    cards: list[str] = []
    for item in results:
        safe_seed = html.escape(item.seed_url)
        safe_final = html.escape(item.final_url or item.seed_url)

        if item.error:
            safe_error = html.escape(item.error)
            card = (
                '<article class="card card-error">'
                f"<h2><a href=\"{safe_seed}\" target=\"_blank\" rel=\"noopener noreferrer\">{safe_seed}</a></h2>"
                f"<p class=\"error\">Erro: {safe_error}</p>"
                "</article>"
            )
            cards.append(card)
            continue

        title_items: list[str] = []
        if item.titles:
            for title in item.titles:
                title_items.append(f"<li>{html.escape(title)}</li>")
        else:
            title_items.append("<li>(nenhum title encontrado)</li>")

        if item.first_image_url:
            safe_img = html.escape(item.first_image_url)
            image_html = (
                "<figure>"
                f"<img src=\"{safe_img}\" alt=\"Primeira imagem de {safe_seed}\" loading=\"lazy\" />"
                f"<figcaption><a href=\"{safe_img}\" target=\"_blank\" rel=\"noopener noreferrer\">{safe_img}</a></figcaption>"
                "</figure>"
            )
        else:
            image_html = "<p class=\"empty\">Nenhuma imagem encontrada.</p>"

        card = (
            "<article class=\"card\">"
            f"<h2><a href=\"{safe_seed}\" target=\"_blank\" rel=\"noopener noreferrer\">{safe_seed}</a></h2>"
            f"<p class=\"meta\">URL final: <a href=\"{safe_final}\" target=\"_blank\" rel=\"noopener noreferrer\">{safe_final}</a></p>"
            "<h3>Titulos encontrados</h3>"
            f"<ul>{''.join(title_items)}</ul>"
            "<h3>Primeira imagem</h3>"
            f"{image_html}"
            "</article>"
        )
        cards.append(card)

    return f"""<!doctype html>
<html lang=\"pt-BR\">
  <head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>Atividade 5</title>
    <style>
      * {{
        box-sizing: border-box;
      }}

      body {{
        margin: 0;
        padding: 16px;
        font-family: Arial, sans-serif;
        background: #ffffff;
        color: #222222;
      }}

      main {{
        max-width: 960px;
        margin: 0 auto;
      }}

      header {{
        margin-bottom: 16px;
      }}

      .grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        gap: 12px;
      }}

      .card {{
        border: 1px solid #cccccc;
        border-radius: 6px;
        padding: 12px;
        background: #ffffff;
      }}

      .card-error {{
        background: #fff7f7;
      }}

      .card h2 {{
        margin-top: 0;
        font-size: 1rem;
        word-break: break-word;
      }}

      .meta,
      .empty {{
        color: #555555;
      }}

      .error {{
        color: #b00020;
      }}

      ul {{
        padding-left: 18px;
      }}

      figure {{
        margin: 0;
      }}

      img {{
        width: 100%;
        height: auto;
        border: 1px solid #cccccc;
      }}

      figcaption {{
        margin-top: 4px;
        font-size: 0.85rem;
        word-break: break-word;
      }}
    </style>
  </head>
  <body>
    <main>
      <header>
        <h1>Atividade 5 - Agregador HTML</h1>
      </header>
      <section class=\"grid\">
        {''.join(cards)}
      </section>
    </main>
  </body>
</html>
"""


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    seeds_path = base_dir / "seeds.txt"
    output_html_path = base_dir / "agregado.html"

    if len(sys.argv) > 1:
        seeds_path = Path(sys.argv[1]).expanduser().resolve()

    if len(sys.argv) > 2:
        output_html_path = Path(sys.argv[2]).expanduser().resolve()

    if not seeds_path.exists():
        raise FileNotFoundError(f"Arquivo de seeds nao encontrado: {seeds_path}")

    seeds = read_seeds_file(seeds_path)
    if not seeds:
        raise ValueError("O arquivo de seeds nao possui URLs validas")

    results: list[PageData] = []
    print(f"Processando {len(seeds)} URLs de {seeds_path}...")
    for index, url in enumerate(seeds, start=1):
        print(f"[{index:02d}/{len(seeds):02d}] {url}")
        results.append(parse_student_page(url))

    output_html = build_output_html(results)
    output_html_path.write_text(output_html, encoding="utf-8")

    ok_count = sum(1 for item in results if not item.error)
    failed_count = len(results) - ok_count
    print("\nResumo")
    print("-" * 72)
    print(f"Sucesso: {ok_count}")
    print(f"Falhas: {failed_count}")
    print(f"Arquivo gerado: {output_html_path}")


if __name__ == "__main__":
    main()
