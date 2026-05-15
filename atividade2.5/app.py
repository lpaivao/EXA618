from flask import Flask, request, make_response, redirect, url_for, session, render_template_string

app = Flask(__name__)
app.secret_key = 'chave_secreta_123'

# Credenciais fixas para o login
USUARIO = 'admin'
SENHA = 'admin'

# ─── Templates HTML ────────────────────────────────────────────────

TEMPLATE_INDEX = '''
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <title>Início</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 600px; margin: 60px auto; padding: 0 20px; }
        .card { background: #f5f5f5; border-radius: 8px; padding: 24px; margin-bottom: 16px; }
        a { color: #0077cc; text-decoration: none; font-weight: bold; }
        a:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <h1>Página Inicial</h1>

    <div class="card">
        <h2>Identificação</h2>
        {% if nome %}
            <p>Olá, <strong>{{ nome }}</strong>! Bem-vindo de volta.</p>
        {% else %}
            <p>Olá, visitante! <a href="/nome/SeuNome">Clique aqui para definir seu nome</a> (substitua "SeuNome" na URL).</p>
        {% endif %}
    </div>

    <div class="card">
        <h2>Contador de Visitas</h2>
        <p>Você visitou esta página <strong>{{ visitas }}</strong> vez(es).</p>
    </div>

    <div class="card">
        <h2>Área Restrita</h2>
        {% if session.get('usuario') %}
            <p>Você está logado como: <strong>{{ session.get('usuario') }}</strong></p>
            <a href="/perfil">Ver Perfil</a> | 
            <a href="/logout">Fazer Logout</a>
        {% else %}
            <p>Você não está autenticado.</p>
            <a href="/login">Ir para Login</a>
        {% endif %}
    </div>
</body>
</html>
'''

TEMPLATE_LOGIN = '''
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <title>Login</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 400px; margin: 80px auto; padding: 0 20px; }
        input { display: block; width: 100%; padding: 8px; margin: 8px 0 16px; box-sizing: border-box; border: 1px solid #ccc; border-radius: 4px; }
        button { background: #0077cc; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; width: 100%; }
        .erro { color: red; margin-bottom: 12px; }
    </style>
</head>
<body>
    <h1>Login</h1>
    {% if erro %}
        <p class="erro">{{ erro }}</p>
    {% endif %}
    <form method="POST" action="/login">
        <label>Usuário:</label>
        <input type="text" name="usuario" required>
        <label>Senha:</label>
        <input type="password" name="senha" required>
        <button type="submit">Entrar</button>
    </form>
    <p><a href="/">← Voltar</a></p>
</body>
</html>
'''

TEMPLATE_PERFIL = '''
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <title>Perfil</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 500px; margin: 80px auto; padding: 0 20px; }
        .card { background: #e8f4e8; border-radius: 8px; padding: 24px; }
        a { color: #0077cc; }
    </style>
</head>
<body>
    <h1>Perfil do Usuário</h1>
    <div class="card">
        <p><strong>Usuário:</strong> {{ usuario }}</p>
        <p><strong>Status:</strong> Logado ✅</p>
    </div>
    <br>
    <a href="/logout">Sair</a> | <a href="/">Início</a>
</body>
</html>
'''

# ─── Rotas ─────────────────────────────────────────────────────────

@app.route('/')
def index():
    nome = request.cookies.get('nome')
    visitas = int(request.cookies.get('visitas', 0)) + 1

    resp = make_response(render_template_string(
        TEMPLATE_INDEX, nome=nome, visitas=visitas
    ))
    resp.set_cookie('visitas', str(visitas), max_age=60*60*24*30)  # 30 dias
    return resp


@app.route('/nome/<nome>')
def salvar_nome(nome):
    resp = make_response(redirect(url_for('index')))
    resp.set_cookie('nome', nome, max_age=60*60*24*30)  # 30 dias
    return resp


@app.route('/login', methods=['GET', 'POST'])
def login():
    # Se o usuário JÁ ESTIVER LOGADO, manda direto pro perfil
    if 'usuario' in session:
        return redirect(url_for('perfil'))

    if request.method == 'POST':
        usuario = request.form.get('usuario')
        senha = request.form.get('senha')

        if usuario == USUARIO and senha == SENHA:
            session['usuario'] = usuario
            return redirect(url_for('perfil'))
        else:
            return render_template_string(TEMPLATE_LOGIN, erro='Usuário ou senha inválidos.')

    return render_template_string(TEMPLATE_LOGIN, erro=None)


@app.route('/perfil')
def perfil():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    return render_template_string(TEMPLATE_PERFIL, usuario=session['usuario'])


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# ───────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    app.run(debug=True)