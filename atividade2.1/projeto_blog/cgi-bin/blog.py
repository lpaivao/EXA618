import os
import sys
import traceback
from urllib.parse import parse_qs
from datetime import datetime

def print_exception():
    exc_type, exc_value, exc_traceback = sys.exc_info()
    traceback.print_exception(exc_type, exc_value, exc_traceback)

print("Content-type: text/html; charset=utf-8\n")

ARQUIVO_DADOS = "mensagens.txt"

qs = os.environ.get("QUERY_STRING", "")

dados = parse_qs(qs, encoding="utf-8")

if "autor" in dados and "mensagem" in dados:
    autor = dados["autor"][0]
    mensagem = dados["mensagem"][0]
    
    data_atual = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    # Salva no arquivo de texto
    with open(ARQUIVO_DADOS, "a", encoding="utf-8") as f:
        msg_limpa = mensagem.replace("\n", " ").replace("\r", "")
        f.write(f"{autor}|{data_atual}|{msg_limpa}\n")

# Geração de página HTML
print('''
<html>
<head>
    <title>Blog Atividade 2.1</title>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
</head>
<body>
''')

print('''
    <form method="GET" action="blog.py">
        Nome: <br>
        <input type="text" size="40" name="autor" required><br><br>
        Mensagem: <br>
        <textarea rows="4" cols="42" name="mensagem" required></textarea><br><br>
        <input type="submit" value="Enviar Mensagem"> <input type="reset" value="Limpar">
    </form>
''')

print('''
    <div class="mural">
        <H3>Mural de Mensagens</H3>
''')

if os.path.exists(ARQUIVO_DADOS):
    with open(ARQUIVO_DADOS, "r", encoding="utf-8") as f:
        linhas = f.readlines()
        if linhas:
            for linha in reversed(linhas):
                partes = linha.strip().split("|", 2)
                if len(partes) == 3:
                    print(f"<div class='msg'><b>{partes[0]}</b> <i>({partes[1]})</i>:<br>{partes[2]}</div>")
        else:
            print("<p>Mural vazio.</p>")
else:
    print("<p>Nenhuma mensagem foi enviada ainda.</p>")

print('''
    </div>
</body>
</html>
''')