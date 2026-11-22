
def corrigir_respostas(gabarito, respostas, pesos):
    """
    Compara as respostas do aluno com o gabarito.

    gabarito: alternativas corretas
    respostas: alternativas marcadas pelo aluno
    pesos: valor individual de cada questão
    """

    if not (len(gabarito) == len(respostas) == len(pesos)):
        raise ValueError(
            "A quantidade de respostas e pesos deve ser igual."
        )

    alternativas = ["A", "B", "C", "D", "E"]

    total = len(gabarito)

    acertos = 0
    erros = 0
    em_branco = 0
    nota = 0.0

    detalhes = []

    for indice in range(total):

        numero = indice + 1

        correta = gabarito[indice]
        marcada = respostas[indice]
        peso = float(pesos[indice])

        if correta not in alternativas:
            raise ValueError("Gabarito contém alternativa inválida.")

        if marcada == "":
            situacao = "Em branco"
            em_branco += 1
            pontos = 0.0

        elif marcada not in alternativas:
            raise ValueError("Resposta do aluno inválida.")

        elif marcada == correta:
            situacao = "Acerto"
            acertos += 1
            pontos = peso

        else:
            situacao = "Erro"
            erros += 1
            pontos = 0.0

        nota += pontos

        detalhes.append({
            "numero": numero,
            "gabarito": correta,
            "resposta": marcada,
            "situacao": situacao,
            "peso": peso,
            "pontos_obtidos": pontos
        })

    percentual = (
        (acertos / total) * 100
        if total > 0 else 0
    )

    return {
        "total": total,
        "acertos": acertos,
        "erros": erros,
        "em_branco": em_branco,
        "percentual": round(percentual, 2),
        "nota": round(nota, 2),
        "detalhes": detalhes
    }
