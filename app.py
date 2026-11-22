

from flask import Flask, redirect, url_for

from database.db import inicializar_banco
from routes.prov import provas_bp
from routes.results import results_bp
from routes.sheet import sheet_bp

app = Flask(__name__)

app.secret_key = "chave-local-desenvolvimento"

# Inicializa o banco de dados
inicializar_banco()

# Registra as rotas do sistema
app.register_blueprint(provas_bp)
app.register_blueprint(results_bp)
app.register_blueprint(sheet_bp)


@app.route("/")
def inicio():
    return redirect(url_for("provas.listar_provas"))


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )