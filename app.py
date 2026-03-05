from flask import Flask, render_template, request, redirect, session, jsonify
import os
from werkzeug.utils import secure_filename
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
app = Flask(__name__)


load_dotenv() 

# ← MUDE ISSO:
app.secret_key = os.getenv("SECRET_KEY", "dev_key_default")

UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# =========================
# CONEXÃO
# =========================

def conectar():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn


# =========================
# CRIAR TABELAS
# =========================



def criar_tabelas():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS produtos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        preco REAL NOT NULL,
        categoria TEXT,
        imagem TEXT,
        ativo INTEGER DEFAULT 1
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pedidos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cliente TEXT,
        endereco TEXT NOT NULL,
        pagamento TEXT NOT NULL,
        observacao TEXT,
        total REAL NOT NULL,
        status TEXT DEFAULT 'Pendente',
        data TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS itens_pedido (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pedido_id INTEGER,
        produto_id INTEGER,
        quantidade INTEGER,
        preco REAL,
        FOREIGN KEY (pedido_id) REFERENCES pedidos(id),
        FOREIGN KEY (produto_id) REFERENCES produtos(id)
    )
    """)

    conn.commit()
    conn.close()


# =========================
# FRONT
# =========================

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/produtos")
def listar_produtos():
    conn = conectar()
    produtos = conn.execute(
        "SELECT * FROM produtos WHERE ativo = 1"
    ).fetchall()
    conn.close()

    return jsonify([dict(p) for p in produtos])


# =========================
# LOGIN
# =========================

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form.get("usuario")
        senha = request.form.get("senha")

        admin_user = os.getenv("ADMIN_USER", "admin")
        admin_pass = os.getenv("ADMIN_PASSWORD", "1234")

        if usuario == admin_user and senha == admin_pass:
            session["admin"] = True
            return redirect("/admin")
        else:
            return "Login inválido"

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("admin", None)
    return redirect("/login")


# =========================
# ADMIN DASHBOARD
# =========================

@app.route("/admin")
def admin():
    if not session.get("admin"):
        return redirect("/login")

    conn = conectar()
    produtos = conn.execute("SELECT * FROM produtos").fetchall()
    conn.close()

    return render_template("admin.html", produtos=produtos)


# =========================
# ADMIN PEDIDOS (CORRIGIDO)
# =========================

@app.route("/admin/pedidos")
def admin_pedidos():
    if not session.get("admin"):
        return redirect("/login")

    conn = conectar()

    pedidos = conn.execute("""
        SELECT * FROM pedidos
        ORDER BY id DESC
    """).fetchall()

    pedidos_completos = []

    for pedido in pedidos:
        itens = conn.execute("""
            SELECT 
                p.nome,
                ip.quantidade,
                ip.preco
            FROM itens_pedido ip
            JOIN produtos p ON ip.produto_id = p.id
            WHERE ip.pedido_id = ?
        """, (pedido["id"],)).fetchall()

        itens_formatados = []

        for item in itens:
            subtotal = round(item["quantidade"] * item["preco"], 2)

            itens_formatados.append({
                "nome": item["nome"],
                "quantidade": item["quantidade"],
                "preco": round(item["preco"], 2),
                "subtotal": subtotal
            })

        pedidos_completos.append({
            "pedido": pedido,
            "itens": itens_formatados
        })

    conn.close()

    return render_template(
        "admin_pedidos.html",
        pedidos_completos=pedidos_completos
    )


# =========================
# ALTERAR STATUS
# =========================

@app.route("/admin/alterar_status/<int:id>")
def alterar_status(id):
    if not session.get("admin"):
        return redirect("/login")

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("SELECT status FROM pedidos WHERE id = ?", (id,))
    status_atual = cursor.fetchone()[0]

    if status_atual == "Pendente":
        novo_status = "Enviado"
    elif status_atual == "Enviado":
        novo_status = "Finalizado"
    else:
        novo_status = "Pendente"

    cursor.execute(
        "UPDATE pedidos SET status = ? WHERE id = ?",
        (novo_status, id)
    )

    conn.commit()
    conn.close()

    return redirect("/admin/pedidos")


# =========================
# PRODUTOS
# =========================

@app.route("/admin/novo", methods=["POST"])
def novo_produto():
    if not session.get("admin"):
        return redirect("/login")

    nome = request.form.get("nome")
    preco = request.form.get("preco")
    categoria = request.form.get("categoria")
    imagem = request.files.get("imagem")

    filename = ""

    if imagem and imagem.filename != "":
        filename = secure_filename(imagem.filename)
        imagem.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

    conn = conectar()
    conn.execute("""
        INSERT INTO produtos (nome, preco, categoria, imagem)
        VALUES (?, ?, ?, ?)
    """, (nome, preco, categoria, filename))

    conn.commit()
    conn.close()

    return redirect("/admin")


@app.route("/admin/remover/<int:id>")
def remover_produto(id):
    if not session.get("admin"):
        return redirect("/login")

    conn = conectar()
    conn.execute("DELETE FROM produtos WHERE id = ?", (id,))
    conn.commit()
    conn.close()

    return redirect("/admin")


@app.route("/admin/editar/<int:id>", methods=["POST"])
def editar_produto(id):
    if not session.get("admin"):
        return redirect("/login")

    nome = request.form.get("nome")
    preco = request.form.get("preco")
    categoria = request.form.get("categoria")
    imagem = request.files.get("imagem")

    conn = conectar()

    if imagem and imagem.filename != "":
        filename = secure_filename(imagem.filename)
        imagem.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        conn.execute("""
            UPDATE produtos
            SET nome=?, preco=?, categoria=?, imagem=?
            WHERE id=?
        """, (nome, preco, categoria, filename, id))
    else:
        conn.execute("""
            UPDATE produtos
            SET nome=?, preco=?, categoria=?
            WHERE id=?
        """, (nome, preco, categoria, id))

    conn.commit()
    conn.close()

    return redirect("/admin")


# =========================
# FINALIZAR PEDIDO (CORRIGIDO)
# =========================

@app.route("/finalizar_pedido", methods=["POST"])
def finalizar_pedido():
    data = request.get_json()

    endereco = data["endereco"]
    pagamento = data["pagamento"]
    observacao = data.get("observacao", "")
    itens = data["itens"]

    total = 0
    for item in itens:
        total += float(item["preco"]) * int(item.get("quantidade", 1))

    total = round(total, 2)

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO pedidos (endereco, pagamento, observacao, total)
        VALUES (?, ?, ?, ?)
    """, (endereco, pagamento, observacao, total))

    pedido_id = cursor.lastrowid

    for item in itens:
        cursor.execute("""
            INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco)
            VALUES (?, ?, ?, ?)
        """, (
            pedido_id,
            item["id"],
            item.get("quantidade", 1),
            float(item["preco"])
        ))

    conn.commit()
    conn.close()

    return jsonify({"success": True})


# =========================
# TOTAL PEDIDOS
# =========================

@app.route("/admin/total_pedidos")
def total_pedidos():
    conn = conectar()
    total = conn.execute("SELECT COUNT(*) FROM pedidos").fetchone()[0]
    conn.close()
    return jsonify({"total": total})


# =========================

# =========================
# LIMPAR TODOS PEDIDOS
# =========================

@app.route("/admin/limpar_pedidos", methods=["POST"])
def limpar_pedidos():
    if not session.get("admin"):
        return redirect("/login")

    conn = conectar()
    cursor = conn.cursor()

    # Apaga primeiro os itens
    cursor.execute("DELETE FROM itens_pedido")

    # Depois apaga os pedidos
    cursor.execute("DELETE FROM pedidos")

    conn.commit()
    conn.close()

    return redirect("/admin/pedidos")

# Crie as tabelas quando a app iniciar (não só no __main__)
criar_tabelas()

if __name__ == "__main__":
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)