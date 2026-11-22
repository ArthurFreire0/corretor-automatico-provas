
from io import BytesIO

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    abort
)

from database.db import conectar
from openpyxl import load_workbook
import math


provas_bp = Blueprint("provas", __name__)



# LISTAR PROVAS


@provas_bp.route("/provas")
def listar_provas():

    conexao = conectar()

    provas = conexao.execute("""
        SELECT * FROM provas
        ORDER BY id DESC
    """).fetchall()

    conexao.close()

    return render_template("index.html", provas=provas)


# CADASTRAR NOVA PROVA


@provas_bp.route("/provas/nova", methods=["GET", "POST"])
def cadastrar_prova():

    if request.method == "POST":

        nome = request.form.get("nome", "").strip()

        quantidade = request.form.get(
            "quantidade_questoes",
            type=int
        )

        valor_total = request.form.get(
            "valor_total",
            type=float
        )

        if not nome:
            flash("Informe o nome da prova.", "erro")
            return redirect(url_for("provas.cadastrar_prova"))

        if quantidade is None or not 1 <= quantidade <= 100:
            flash(
                "A prova deve possuir entre 1 e 100 questões.",
                "erro"
            )
            return redirect(url_for("provas.cadastrar_prova"))

        if (
            valor_total is None
            or not math.isfinite(valor_total)
            or valor_total <= 0
        ):
            flash(
                "Informe um valor total válido para a prova.",
                "erro"
            )
            return redirect(url_for("provas.cadastrar_prova"))

        peso_questao = valor_total / quantidade

        conexao = conectar()

        cursor = conexao.execute("""
            INSERT INTO provas (
                nome,
                quantidade_questoes,
                valor_total
            )
            VALUES (?, ?, ?)
        """, (nome, quantidade, valor_total))

        prova_id = cursor.lastrowid

        conexao.commit()
        conexao.close()

        flash(
            f"Prova cadastrada! Cada questão valerá aproximadamente "
            f"{peso_questao:.4f} pontos.",
            "sucesso"
        )

        return redirect(
            url_for(
                "provas.cadastrar_gabarito",
                prova_id=prova_id
            )
        )

    return render_template("cad_prov.html")



# EXIBIR CADASTRO DO GABARITO


def exibir_cadastro_gabarito(prova, peso_questao, respostas_atuais):

    return render_template(
        "cad_gab.html",
        prova=prova,
        peso_questao=peso_questao,
        respostas_atuais=respostas_atuais
    )



# SALVAR GABARITO NO BANCO


def salvar_gabarito(conexao, prova_id, respostas, peso_questao):

    conexao.execute("""
        DELETE FROM questoes
        WHERE prova_id = ?
    """, (prova_id,))

    conexao.executemany("""
        INSERT INTO questoes (
            prova_id,
            numero,
            alternativa_correta,
            peso
        )
        VALUES (?, ?, ?, ?)
    """, [
        (prova_id, numero, resposta, peso_questao)
        for numero, resposta in respostas
    ])

    conexao.commit()



# CADASTRAR GABARITO


@provas_bp.route(
    "/provas/<int:prova_id>/gabarito",
    methods=["GET", "POST"]
)
def cadastrar_gabarito(prova_id):

    conexao = conectar()

    prova = conexao.execute("""
        SELECT * FROM provas
        WHERE id = ?
    """, (prova_id,)).fetchone()

    if prova is None:
        conexao.close()
        abort(404)

    quantidade = prova["quantidade_questoes"]

    peso_questao = (
        prova["valor_total"] / quantidade
    )

    # Recuperar gabarito já cadastrado, caso exista
    questoes_existentes = conexao.execute("""
        SELECT numero, alternativa_correta
        FROM questoes
        WHERE prova_id = ?
        ORDER BY numero
    """, (prova_id,)).fetchall()

    respostas_atuais = {
        item["numero"]: item["alternativa_correta"]
        for item in questoes_existentes
    }

    if request.method == "POST":

        acao = request.form.get("acao")
        alternativas = ["A", "B", "C", "D", "E"]

        respostas = []
        

        if acao == "manual":

            for numero in range(1, quantidade + 1):

                resposta = request.form.get(
                    f"questao_{numero}",
                    ""
                ).strip().upper()

                if resposta not in alternativas:

                    conexao.close()

                    flash(
                        f"Selecione uma alternativa válida para "
                        f"a questão {numero}.",
                        "erro"
                    )

                    return redirect(
                        url_for(
                            "provas.cadastrar_gabarito",
                            prova_id=prova_id
                        )
                    )

                respostas.append((numero, resposta))


        elif acao == "sequencia":

            sequencia = request.form.get(
                "sequencia",
                ""
            ).upper()

            # Permite espaços, vírgulas, ponto e vírgula
            # e quebras de linha entre as respostas.
            sequencia = "".join(
                caractere
                for caractere in sequencia
                if not caractere.isspace()
                and caractere not in ",;"
            )

            if len(sequencia) != quantidade:

                conexao.close()

                flash(
                    f"Você informou {len(sequencia)} respostas, "
                    f"mas a prova possui {quantidade} questões.",
                    "erro"
                )

                return redirect(
                    url_for(
                        "provas.cadastrar_gabarito",
                        prova_id=prova_id
                    )
                )

            for numero, resposta in enumerate(sequencia, start=1):

                if resposta not in alternativas:

                    conexao.close()

                    flash(
                        f"A resposta da posição {numero} é inválida. "
                        "Utilize somente A, B, C, D ou E.",
                        "erro"
                    )

                    return redirect(
                        url_for(
                            "provas.cadastrar_gabarito",
                            prova_id=prova_id
                        )
                    )

                respostas.append((numero, resposta))


        elif acao == "excel":

            arquivo = request.files.get("arquivo_excel")

            if not arquivo or not arquivo.filename:

                conexao.close()

                flash(
                    "Selecione uma planilha Excel.",
                    "erro"
                )

                return redirect(
                    url_for(
                        "provas.cadastrar_gabarito",
                        prova_id=prova_id
                    )
                )

            if not arquivo.filename.lower().endswith(".xlsx"):

                conexao.close()

                flash(
                    "Envie um arquivo Excel no formato .xlsx.",
                    "erro"
                )

                return redirect(
                    url_for(
                        "provas.cadastrar_gabarito",
                        prova_id=prova_id
                    )
                )

            try:

                planilha = load_workbook(
                    BytesIO(arquivo.read()),
                    data_only=True,
                    read_only=True
                )

                aba = planilha.active

                linhas = list(
                    aba.iter_rows(
                        values_only=True
                    )
                )

                if linhas:

                    primeira = [
                        str(valor).strip().lower()
                        if valor is not None else ""
                        for valor in linhas[0][:2]
                    ]

                    if (
                        primeira
                        and primeira[0] in ["questao", "questão", "numero"]
                        and len(primeira) > 1
                        and primeira[1] in ["resposta", "alternativa", "gabarito"]
                    ):
                        linhas = linhas[1:]

                dados = []

                for linha in linhas:

                    if not linha or all(
                        valor is None or str(valor).strip() == ""
                        for valor in linha
                    ):
                        continue

                    if len(linha) < 2:

                        raise ValueError(
                            "A planilha deve possuir duas colunas: "
                            "Questão e Resposta."
                        )

                    numero = linha[0]
                    resposta = str(linha[1]).strip().upper()

                    if isinstance(numero, bool) or not isinstance(numero, (int, float)):
                        raise ValueError(
                            "A primeira coluna deve conter o número da questão."
                        )

                    if int(numero) != numero:
                        raise ValueError(
                            "Os números das questões devem ser inteiros."
                        )

                    dados.append((int(numero), resposta))

                planilha.close()

                if len(dados) != quantidade:

                    raise ValueError(
                        f"A planilha contém {len(dados)} respostas, "
                        f"mas a prova possui {quantidade} questões."
                    )

                for indice, (numero, resposta) in enumerate(dados, start=1):

                    if numero != indice:

                        raise ValueError(
                            f"Esperava a questão {indice}, "
                            f"mas encontrei a questão {numero}."
                        )

                    if resposta not in alternativas:

                        raise ValueError(
                            f"A resposta da questão {numero} é inválida. "
                            "Utilize A, B, C, D ou E."
                        )

                    respostas.append((numero, resposta))

            except Exception as erro:

                conexao.close()

                flash(
                    f"Erro ao importar a planilha: {erro}",
                    "erro"
                )

                return redirect(
                    url_for(
                        "provas.cadastrar_gabarito",
                        prova_id=prova_id
                    )
                )

        else:

            conexao.close()

            flash("Opção de cadastro inválida.", "erro")

            return redirect(
                url_for(
                    "provas.cadastrar_gabarito",
                    prova_id=prova_id
                )
            )

        
        # GRAVAR GABARITO
        

        try:

            salvar_gabarito(
                conexao,
                prova_id,
                respostas,
                peso_questao
            )

        except Exception:

            conexao.rollback()
            conexao.close()
            raise

        conexao.close()

        flash(
            "Gabarito cadastrado com sucesso!",
            "sucesso"
        )

        return redirect(
            url_for(
                "provas.detalhes_prova",
                prova_id=prova_id
            )
        )

    conexao.close()

    return exibir_cadastro_gabarito(
        prova,
        peso_questao,
        respostas_atuais
    )



# DETALHES DA PROVA


@provas_bp.route("/provas/<int:prova_id>")
def detalhes_prova(prova_id):

    conexao = conectar()

    prova = conexao.execute("""
        SELECT * FROM provas
        WHERE id = ?
    """, (prova_id,)).fetchone()

    if prova is None:
        conexao.close()
        abort(404)

    questoes = conexao.execute("""
        SELECT * FROM questoes
        WHERE prova_id = ?
        ORDER BY numero
    """, (prova_id,)).fetchall()

    conexao.close()

    return render_template(
        "det_prov.html",
        prova=prova,
        questoes=questoes
    )



# EXCLUIR PROVA


@provas_bp.route(
    "/provas/<int:prova_id>/excluir",
    methods=["POST"]
)
def excluir_prova(prova_id):

    conexao = conectar()

    prova = conexao.execute("""
        SELECT * FROM provas
        WHERE id = ?
    """, (prova_id,)).fetchone()

    if prova is None:
        conexao.close()
        abort(404)

    conexao.execute("""
        DELETE FROM provas
        WHERE id = ?
    """, (prova_id,))

    conexao.commit()
    conexao.close()

    flash("Prova excluída com sucesso!", "sucesso")

    return redirect(url_for("provas.listar_provas"))
