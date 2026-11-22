
from flask import (
    Blueprint,
    send_file,
    abort,
    flash,
    redirect,
    url_for
)

from database.db import conectar
from serv.sheet_gen import gerar_folha_pdf


sheet_bp = Blueprint("sheet", __name__)



# BUSCAR PROVA


def buscar_prova(prova_id):

    conexao = conectar()

    prova = conexao.execute("""
        SELECT *
        FROM provas
        WHERE id = ?
    """, (prova_id,)).fetchone()

    conexao.close()

    return prova



# ABRIR PDF PARA VISUALIZAR E IMPRIMIR


@sheet_bp.route("/provas/<int:prova_id>/folha")
def view_sheet(prova_id):

    prova = buscar_prova(prova_id)

    if prova is None:
        abort(404)

    try:

        arquivo = gerar_folha_pdf(prova)

        return send_file(
            arquivo,
            mimetype="application/pdf",
            as_attachment=False,
            download_name=f"folha_prova_{prova_id}.pdf"
        )

    except ValueError as erro:

        flash(str(erro), "erro")

        return redirect(
            url_for(
                "provas.detalhes_prova",
                prova_id=prova_id
            )
        )



# BAIXAR PDF


@sheet_bp.route("/provas/<int:prova_id>/folha/download")
def download_sheet(prova_id):

    prova = buscar_prova(prova_id)

    if prova is None:
        abort(404)

    try:

        arquivo = gerar_folha_pdf(prova)

        return send_file(
            arquivo,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=f"folha_prova_{prova_id}.pdf"
        )

    except ValueError as erro:

        flash(str(erro), "erro")

        return redirect(
            url_for(
                "provas.detalhes_prova",
                prova_id=prova_id
            )
        )
