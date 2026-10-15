import re

from flask import Flask, abort, flash, redirect, render_template, request, url_for
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError

from database import SessionLocal, init_db
from models import Cliente, Endereco

app = Flask(__name__)
app.secret_key = "troque-esta-chave-em-producao"

ESTADOS = [
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", "MG", "PA",
    "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO",
]


@app.teardown_appcontext
def encerrar_sessao(_exc=None):
    SessionLocal.remove()


@app.context_processor
def variaveis_globais():
    return {"ESTADOS": ESTADOS}


def obter_cliente_ou_404(cliente_id: int) -> Cliente:
    cliente = SessionLocal.get(Cliente, cliente_id)
    if cliente is None:
        abort(404)
    return cliente


def obter_endereco_ou_404(endereco_id: int) -> Endereco:
    endereco = SessionLocal.get(Endereco, endereco_id)
    if endereco is None:
        abort(404)
    return endereco


def validar_cliente(form):
    dados = {
        "nome": form.get("nome", "").strip(),
        "email": form.get("email", "").strip().lower(),
        "telefone": form.get("telefone", "").strip() or None,
    }
    erros = {}
    if len(dados["nome"]) < 3:
        erros["nome"] = "Informe o nome (mínimo de 3 caracteres)."
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", dados["email"]):
        erros["email"] = "Informe um e-mail válido."
    return dados, erros


def validar_endereco(form):
    cep = form.get("cep", "").strip()
    dados = {
        "rua": form.get("rua", "").strip(),
        "numero": form.get("numero", "").strip(),
        "cidade": form.get("cidade", "").strip(),
        "estado": form.get("estado", "").strip().upper(),
        "cep": cep,
    }
    erros = {}
    if not dados["rua"]:
        erros["rua"] = "Informe a rua."
    if not dados["numero"]:
        erros["numero"] = "Informe o número."
    if not dados["cidade"]:
        erros["cidade"] = "Informe a cidade."
    if dados["estado"] not in ESTADOS:
        erros["estado"] = "Selecione o estado."
    if not re.fullmatch(r"\d{5}-?\d{3}", cep):
        erros["cep"] = "CEP inválido (use 00000-000)."
    else:
        dados["cep"] = f"{cep[:5]}-{cep[-3:]}"
    return dados, erros


@app.route("/")
def index():
    busca = request.args.get("q", "").strip()
    stmt = (
        select(Cliente, func.count(Endereco.id).label("total"))
        .outerjoin(Endereco, Endereco.cliente_id == Cliente.id)
        .group_by(Cliente.id)
        .order_by(Cliente.nome)
    )
    if busca:
        termo = f"%{busca}%"
        stmt = stmt.where(or_(Cliente.nome.ilike(termo), Cliente.email.ilike(termo)))
    linhas = SessionLocal.execute(stmt).all()
    return render_template("index.html", linhas=linhas, busca=busca)


@app.route("/clientes/novo", methods=["GET", "POST"])
def cliente_novo():
    dados, erros = {}, {}
    if request.method == "POST":
        dados, erros = validar_cliente(request.form)
        if not erros:
            cliente = Cliente(**dados)
            SessionLocal.add(cliente)
            try:
                SessionLocal.commit()
            except IntegrityError:
                SessionLocal.rollback()
                erros["email"] = "Já existe um cliente com este e-mail."
            else:
                flash("Cliente cadastrado com sucesso!", "sucesso")
                return redirect(url_for("cliente_detalhe", cliente_id=cliente.id))
    return render_template("cliente_form.html", cliente=None, dados=dados, erros=erros)


@app.route("/clientes/<int:cliente_id>")
def cliente_detalhe(cliente_id):
    cliente = obter_cliente_ou_404(cliente_id)
    return render_template("cliente_detalhe.html", cliente=cliente)


@app.route("/clientes/<int:cliente_id>/editar", methods=["GET", "POST"])
def cliente_editar(cliente_id):
    cliente = obter_cliente_ou_404(cliente_id)
    erros = {}
    dados = {"nome": cliente.nome, "email": cliente.email, "telefone": cliente.telefone}
    if request.method == "POST":
        dados, erros = validar_cliente(request.form)
        if not erros:
            cliente.nome = dados["nome"]
            cliente.email = dados["email"]
            cliente.telefone = dados["telefone"]
            try:
                SessionLocal.commit()
            except IntegrityError:
                SessionLocal.rollback()
                erros["email"] = "Já existe outro cliente com este e-mail."
            else:
                flash("Cliente atualizado com sucesso!", "sucesso")
                return redirect(url_for("cliente_detalhe", cliente_id=cliente_id))
    return render_template("cliente_form.html", cliente=cliente, dados=dados, erros=erros)


@app.route("/clientes/<int:cliente_id>/excluir", methods=["POST"])
def cliente_excluir(cliente_id):
    cliente = obter_cliente_ou_404(cliente_id)
    nome = cliente.nome
    SessionLocal.delete(cliente)
    SessionLocal.commit()
    flash(f"Cliente “{nome}” e seus endereços foram excluídos.", "sucesso")
    return redirect(url_for("index"))


@app.route("/clientes/<int:cliente_id>/enderecos/novo", methods=["GET", "POST"])
def endereco_novo(cliente_id):
    cliente = obter_cliente_ou_404(cliente_id)
    dados, erros = {}, {}
    if request.method == "POST":
        dados, erros = validar_endereco(request.form)
        if not erros:
            SessionLocal.add(Endereco(cliente_id=cliente.id, **dados))
            SessionLocal.commit()
            flash("Endereço adicionado com sucesso!", "sucesso")
            return redirect(url_for("cliente_detalhe", cliente_id=cliente_id))
    return render_template(
        "endereco_form.html", cliente=cliente, endereco=None, dados=dados, erros=erros
    )

@app.route("/enderecos/<int:endereco_id>/editar", methods=["GET", "POST"])
def endereco_editar(endereco_id):
    endereco = obter_endereco_ou_404(endereco_id)
    erros = {}
    dados = {
        "rua": endereco.rua, "numero": endereco.numero, "cidade": endereco.cidade,
        "estado": endereco.estado, "cep": endereco.cep,
    }
    if request.method == "POST":
        dados, erros = validar_endereco(request.form)
        if not erros:
            for campo, valor in dados.items():
                setattr(endereco, campo, valor)
            SessionLocal.commit()
            flash("Endereço atualizado com sucesso!", "sucesso")
            return redirect(url_for("cliente_detalhe", cliente_id=endereco.cliente_id))
    return render_template(
        "endereco_form.html", cliente=endereco.cliente, endereco=endereco,
        dados=dados, erros=erros,
    )

@app.route("/enderecos/<int:endereco_id>/excluir", methods=["POST"])
def endereco_excluir(endereco_id):
    endereco = obter_endereco_ou_404(endereco_id)
    cliente_id = endereco.cliente_id
    SessionLocal.delete(endereco)
    SessionLocal.commit()
    flash("Endereço excluído.", "sucesso")
    return redirect(url_for("cliente_detalhe", cliente_id=cliente_id))


@app.route("/relatorio")
def relatorio():
    tipo = request.args.get("tipo", "inner")   
    cidade = request.args.get("cidade", "").strip()
    estado = request.args.get("estado", "").strip().upper()

    stmt = select(
        Cliente.id.label("cliente_id"),
        Cliente.nome,
        Cliente.email,
        Cliente.telefone,
        Endereco.rua,
        Endereco.numero,
        Endereco.cidade,
        Endereco.estado,
        Endereco.cep,
    )
    condicao = Endereco.cliente_id == Cliente.id
    stmt = stmt.outerjoin(Endereco, condicao) if tipo == "left" else stmt.join(Endereco, condicao)

    if cidade:
        stmt = stmt.where(Endereco.cidade.ilike(f"%{cidade}%"))
    if estado:
        stmt = stmt.where(Endereco.estado == estado)
    stmt = stmt.order_by(Cliente.nome, Endereco.cidade)

    linhas = SessionLocal.execute(stmt).all()
    return render_template(
        "relatorio.html", linhas=linhas, sql=str(stmt),
        tipo=tipo, cidade=cidade, estado=estado,
    )


@app.errorhandler(404)
def nao_encontrado(_erro):
    return render_template("404.html"), 404


init_db()

if __name__ == "__main__":
    app.run(debug=True)
