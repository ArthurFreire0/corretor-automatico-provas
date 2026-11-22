
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    abort,
    jsonify,
    current_app
)

from database.db import conectar
from serv.grading import corrigir_respostas
from serv.omr import reconhecer_respostas


results_bp = Blueprint("results", __name__)



# CORRIGIR PROVA MANUALMENTE

@results_bp.route(
    "/provas/<int:prova_id>/corrigir",
    methods=["GET", "POST"]
)
def corr_prova(prova_id):

    conexao = conectar()

    prova = conexao.execute("""
        SELECT * FROM provas
        WHERE id = ?
    """, (prova_id,)).fetchone()

    if prova is None:
        conexao.close()
        abort(404)

    questoes = conexao.execute("""
        SELECT *
        FROM questoes
        WHERE prova_id = ?
        ORDER BY numero
    """, (prova_id,)).fetchall()

    if len(questoes) != prova["quantidade_questoes"]:

        conexao.close()

        flash(
            "Cadastre o gabarito completo antes de corrigir.",
            "erro"
        )

        return redirect(
            url_for(
                "provas.detalhes_prova",
                prova_id=prova_id
            )
        )

    if request.method == "POST":

        aluno_nome = request.form.get(
            "aluno_nome", ""
        ).strip()

        if not aluno_nome:

            conexao.close()

            flash("Informe o nome do aluno.", "erro")

            return redirect(
                url_for(
                    "results.corr_prova",
                    prova_id=prova_id
                )
            )

        alternativas = ["A", "B", "C", "D", "E"]
        respostas = []

        for questao in questoes:

            resposta = request.form.get(
                f"questao_{questao['numero']}",
                ""
            )

            if resposta not in [""] + alternativas:

                conexao.close()

                flash(
                    f"Resposta inválida na questão {questao['numero']}.",
                    "erro"
                )

                return redirect(
                    url_for(
                        "results.corr_prova",
                        prova_id=prova_id
                    )
                )

            respostas.append(resposta)

        gabarito = [
            questao["alternativa_correta"]
            for questao in questoes
        ]

        pesos = [
            questao["peso"]
            for questao in questoes
        ]

        resultado = corrigir_respostas(
            gabarito,
            respostas,
            pesos
        )

        try:

            cursor = conexao.execute("""

                INSERT INTO results (
                    prova_id,
                    aluno_nome,
                    total_questoes,
                    acertos,
                    erros,
                    em_branco,
                    percentual,
                    nota
                )

                VALUES (?, ?, ?, ?, ?, ?, ?, ?)

            """, (
                prova_id,
                aluno_nome,
                resultado["total"],
                resultado["acertos"],
                resultado["erros"],
                resultado["em_branco"],
                resultado["percentual"],
                resultado["nota"]
            ))

            result_id = cursor.lastrowid

            conexao.executemany("""

                INSERT INTO answers_results (
                    result_id,
                    numero_questao,
                    resposta_aluno,
                    resposta_correta,
                    situacao,
                    peso,
                    pontos_obtidos
                )

                VALUES (?, ?, ?, ?, ?, ?, ?)

            """, [

                (
                    result_id,
                    detalhe["numero"],
                    detalhe["resposta"] or None,
                    detalhe["gabarito"],
                    detalhe["situacao"],
                    detalhe["peso"],
                    detalhe["pontos_obtidos"]
                )

                for detalhe in resultado["detalhes"]

            ])

            conexao.commit()

        except Exception:

            conexao.rollback()
            conexao.close()

            raise

        conexao.close()

        return redirect(
            url_for(
                "results.show_result",
                result_id=result_id
            )
        )

    conexao.close()

    return render_template(
        "corr_prov.html",
        prova=prova,
        questoes=questoes
    )



# RECEBER IMAGENS E EXECUTAR O OMR


@results_bp.route(
    "/provas/<int:prova_id>/receber-imagem",
    methods=["POST"]
)
def receber_imagem(prova_id):

    conexao = conectar()

    prova = conexao.execute("""
        SELECT *
        FROM provas
        WHERE id = ?
    """, (prova_id,)).fetchone()

    if prova is None:

        conexao.close()

        return jsonify({
            "erro": "Prova não encontrada."
        }), 404

    quantidade_questoes = prova["quantidade_questoes"]

    questoes = conexao.execute("""
        SELECT id
        FROM questoes
        WHERE prova_id = ?
    """, (prova_id,)).fetchall()

    conexao.close()

    if len(questoes) != quantidade_questoes:

        return jsonify({
            "erro": "O gabarito da prova está incompleto."
        }), 400

    aluno_nome = request.form.get(
        "aluno_nome", ""
    ).strip()

    if not aluno_nome:

        return jsonify({
            "erro": "Informe o nome do aluno."
        }), 400

    
    imagens = request.files.getlist("imagens")

    
    if not imagens:
        imagem_antiga = request.files.get("imagem")

        if imagem_antiga:
            imagens = [imagem_antiga]

    imagens = [
        imagem for imagem in imagens
        if imagem and imagem.filename
    ]

    
    if quantidade_questoes <= 50:
        quantidade_imagens_esperada = 1
    else:
        quantidade_imagens_esperada = 2

    if len(imagens) != quantidade_imagens_esperada:

        if quantidade_imagens_esperada == 1:
            mensagem = "Envie uma imagem da folha de respostas."
        else:
            mensagem = (
                "Esta prova possui mais de 50 questões. "
                "Envie duas imagens, na ordem: página 1 e página 2."
            )

        return jsonify({
            "erro": mensagem
        }), 400

    respostas_completas = []

    limite = 10 * 1024 * 1024

    
    for indice, imagem in enumerate(imagens):

        conteudo = imagem.read()

        if not conteudo:

            return jsonify({
                "erro": f"A imagem da página {indice + 1} está vazia."
            }), 400

        if len(conteudo) > limite:

            return jsonify({
                "erro": (
                    f"A imagem da página {indice + 1} "
                    "ultrapassa o limite de 10 MB."
                )
            }), 413

        assinatura_jpeg = conteudo.startswith(b"\xff\xd8\xff")

        assinatura_png = conteudo.startswith(
            b"\x89PNG\r\n\x1a\n"
        )

        assinatura_webp = (
            len(conteudo) >= 12
            and conteudo[:4] == b"RIFF"
            and conteudo[8:12] == b"WEBP"
        )

        if not (
            assinatura_jpeg
            or assinatura_png
            or assinatura_webp
        ):

            return jsonify({
                "erro": (
                    f"Formato inválido na página {indice + 1}. "
                    "Envie JPG, PNG ou WEBP."
                )
            }), 400

        
        if indice == 0:
            questoes_desta_pagina = min(
                quantidade_questoes,
                50
            )
            deslocamento = 0

        else:
            questoes_desta_pagina = quantidade_questoes - 50
            deslocamento = 50

        try:

            resultado_omr = reconhecer_respostas(
                conteudo,
                questoes_desta_pagina
            )

            if not resultado_omr.get("sucesso"):

                return jsonify({
                    "erro": (
                        f"Não foi possível reconhecer a página "
                        f"{indice + 1}."
                    )
                }), 400

            respostas_pagina = resultado_omr["respostas"]

            for resposta in respostas_pagina:

                numero_global = (
                    resposta["numero"] + deslocamento
                )

                pontuacoes = {
                    alternativa: float(valor)
                    for alternativa, valor
                    in resposta["pontuacoes"].items()
                }

                respostas_completas.append({

                    "numero": numero_global,

                    "resposta": resposta["resposta"],

                    "situacao": resposta["situacao"],

                    "pontuacoes": pontuacoes

                })

        except ValueError as erro:

            return jsonify({
                "erro": str(erro)
            }), 400

        except Exception:

            current_app.logger.exception(
                "Erro durante o reconhecimento da folha."
            )

            return jsonify({
                "erro": (
                    f"Ocorreu um erro ao processar a página "
                    f"{indice + 1}. Verifique a imagem e tente novamente."
                )
            }), 500

    
    if len(respostas_completas) != quantidade_questoes:

        return jsonify({
            "erro": (
                "O reconhecimento não retornou a quantidade "
                "esperada de questões."
            )
        }), 400

    return jsonify({

        "sucesso": True,

        "mensagem": (
            "Reconhecimento concluído! "
            "Confira as respostas antes de corrigir a prova."
        ),

        "aluno_nome": aluno_nome,

        "quantidade_questoes": quantidade_questoes,

        "respostas": respostas_completas

    }), 200



# LISTAR TODAS AS PROVAS

@results_bp.route("/provas-corrigidas")
def listar_provas_corrigidas():

    conexao = conectar()

    provas = conexao.execute("""

        SELECT
            provas.id,
            provas.nome,
            provas.quantidade_questoes,
            provas.valor_total,
            COUNT(results.id) AS total_alunos

        FROM provas

        LEFT JOIN results
            ON results.prova_id = provas.id

        GROUP BY
            provas.id,
            provas.nome,
            provas.quantidade_questoes,
            provas.valor_total

        ORDER BY provas.nome

    """).fetchall()

    conexao.close()

    return render_template(
        "provas_corrigidas.html",
        provas=provas
    )



# LISTAR ALUNOS CORRIGIDOS DE UMA PROVA


@results_bp.route("/provas/<int:prova_id>/alunos-corrigidos")
def alunos_prova(prova_id):

    conexao = conectar()

    prova = conexao.execute("""

        SELECT *
        FROM provas
        WHERE id = ?

    """, (prova_id,)).fetchone()

    if prova is None:

        conexao.close()
        abort(404)

    resultados = conexao.execute("""

        SELECT *
        FROM results
        WHERE prova_id = ?

        ORDER BY aluno_nome

    """, (prova_id,)).fetchall()

    conexao.close()

    return render_template(
        "alunos_prova.html",
        prova=prova,
        resultados=resultados
    )


# EXIBIR RESULTADO


@results_bp.route("/results/<int:result_id>")
def show_result(result_id):

    conexao = conectar()

    resultado = conexao.execute("""

        SELECT
            results.*,
            provas.nome AS nome_prova,
            provas.valor_total AS valor_total

        FROM results

        JOIN provas
            ON provas.id = results.prova_id

        WHERE results.id = ?

    """, (result_id,)).fetchone()

    if resultado is None:

        conexao.close()
        abort(404)

    detalhes = conexao.execute("""

        SELECT *
        FROM answers_results
        WHERE result_id = ?
        ORDER BY numero_questao

    """, (result_id,)).fetchall()

    conexao.close()

    return render_template(
        "result.html",
        resultado=resultado,
        detalhes=detalhes
    )



# HISTÓRICO


@results_bp.route("/results")
def list_results():

    conexao = conectar()

    resultados = conexao.execute("""

        SELECT
            results.*,
            provas.nome AS nome_prova

        FROM results

        JOIN provas
            ON provas.id = results.prova_id

        ORDER BY results.id DESC

    """).fetchall()

    conexao.close()

    return render_template(
        "hist.html",
        resultados=resultados
    )



# EXCLUIR RESULTADO DO HISTÓRICO


@results_bp.route(
    "/results/<int:result_id>/delete",
    methods=["POST"]
)
def delete_result(result_id):

    conexao = conectar()

    resultado = conexao.execute("""
        SELECT id FROM results
        WHERE id = ?
    """, (result_id,)).fetchone()

    if resultado is None:

        conexao.close()
        abort(404)

    conexao.execute("""
        DELETE FROM results
        WHERE id = ?
    """, (result_id,))

    conexao.commit()
    conexao.close()

    flash(
        "Correção excluída do histórico!",
        "sucesso"
    )

    return redirect(
        url_for("results.list_results")
    )
