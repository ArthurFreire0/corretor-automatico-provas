

from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas


ALTERNATIVAS = ["A", "B", "C", "D", "E"]

MAX_QUESTOES = 100
QUESTOES_POR_PAGINA = 50
QUESTOES_POR_COLUNA = 25


def desenhar_marcadores(pdf, largura, altura):
    """Desenha quatro marcadores pretos para o alinhamento pelo OpenCV."""

    tamanho = 8 * mm
    margem = 8 * mm

    posicoes = [
        (margem, altura - margem - tamanho),
        (largura - margem - tamanho, altura - margem - tamanho),
        (margem, margem),
        (largura - margem - tamanho, margem)
    ]

    pdf.setFillColorRGB(0, 0, 0)

    for x, y in posicoes:
        pdf.rect(x, y, tamanho, tamanho, fill=1, stroke=0)


def desenhar_cabecalho(
    pdf,
    prova,
    pagina_atual,
    total_paginas,
    largura,
    altura
):
    """Desenha o cabeçalho e os campos de identificação."""

    centro = largura / 2

    pdf.setFont("Helvetica-Bold", 15)
    pdf.drawCentredString(
        centro,
        altura - 23 * mm,
        "FOLHA DE RESPOSTAS"
    )

    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawCentredString(
        centro,
        altura - 30 * mm,
        "CORRETOR AUTOMATICO DE PROVAS"
    )

    pdf.setFont("Helvetica", 9)

    pdf.drawString(
        20 * mm,
        altura - 42 * mm,
        f"Prova: {prova['nome'][:65]}"
    )

    pdf.drawString(
        20 * mm,
        altura - 49 * mm,
        f"Codigo da prova: {prova['id']}"
    )

    pdf.drawString(
        20 * mm,
        altura - 62 * mm,
        "Aluno:"
    )

    pdf.line(
        33 * mm,
        altura - 63 * mm,
        largura - 20 * mm,
        altura - 63 * mm
    )

    pdf.drawString(
        20 * mm,
        altura - 74 * mm,
        "Turma:"
    )

    pdf.line(
        33 * mm,
        altura - 75 * mm,
        85 * mm,
        altura - 75 * mm
    )

    pdf.drawString(
        100 * mm,
        altura - 74 * mm,
        "Data:"
    )

    pdf.line(
        113 * mm,
        altura - 75 * mm,
        largura - 20 * mm,
        altura - 75 * mm
    )

    pdf.setFont("Helvetica", 8)

    pdf.drawCentredString(
        centro,
        altura - 85 * mm,
        "Preencha completamente apenas uma alternativa por questao."
    )

    pdf.drawCentredString(
        centro,
        altura - 90 * mm,
        "Utilize caneta azul ou preta e evite rasuras."
    )

    pdf.drawRightString(
        largura - 20 * mm,
        15 * mm,
        f"Pagina {pagina_atual} de {total_paginas}"
    )


def desenhar_questao(pdf, numero, x, y, largura_coluna):
    """Desenha o número da questão e as cinco alternativas."""

    pdf.setFont("Helvetica-Bold", 9)

    pdf.drawString(
        x,
        y - 3,
        str(numero)
    )

    inicio = x + 18 * mm
    espacamento = 9 * mm
    raio = 2.5 * mm

    centro_y = y - 2 * mm

    pdf.setLineWidth(0.8)
    pdf.setStrokeColorRGB(0, 0, 0)

    for indice, alternativa in enumerate(ALTERNATIVAS):

        centro_x = inicio + indice * espacamento

        pdf.circle(
            centro_x,
            centro_y,
            raio,
            fill=0,
            stroke=1
        )

        pdf.setFont("Helvetica", 7)

        pdf.drawCentredString(
            centro_x,
            centro_y - 2.5,
            alternativa
        )


def gerar_folha_pdf(prova):
    """Gera o PDF da folha de respostas em branco."""

    quantidade = prova["quantidade_questoes"]

    if not 1 <= quantidade <= MAX_QUESTOES:
        raise ValueError(
            "A prova deve possuir entre 1 e 100 questões."
        )

    arquivo = BytesIO()

    largura, altura = A4

    pdf = canvas.Canvas(
        arquivo,
        pagesize=A4
    )

    total_paginas = (
        quantidade + QUESTOES_POR_PAGINA - 1
    ) // QUESTOES_POR_PAGINA

    for pagina in range(total_paginas):

        inicio_pagina = pagina * QUESTOES_POR_PAGINA

        fim_pagina = min(
            inicio_pagina + QUESTOES_POR_PAGINA,
            quantidade
        )

        desenhar_marcadores(
            pdf,
            largura,
            altura
        )

        desenhar_cabecalho(
            pdf,
            prova,
            pagina + 1,
            total_paginas,
            largura,
            altura
        )

        y_inicial = altura - 112 * mm
        espacamento_vertical = 6.5 * mm

        largura_coluna = 75 * mm

        posicoes_colunas = [
            23 * mm,
            110 * mm
        ]

        for indice in range(inicio_pagina, fim_pagina):

            numero = indice + 1

            indice_local = indice - inicio_pagina

            coluna = indice_local // QUESTOES_POR_COLUNA
            linha = indice_local % QUESTOES_POR_COLUNA

            x = posicoes_colunas[coluna]

            y = (
                y_inicial -
                linha * espacamento_vertical
            )

            desenhar_questao(
                pdf,
                numero,
                x,
                y,
                largura_coluna
            )

        pdf.setFont("Helvetica", 7)

        pdf.drawCentredString(
            largura / 2,
            8 * mm,
            f"Prova {prova['id']} - Corretor Automatico de Provas"
        )

        pdf.showPage()

    pdf.save()

    arquivo.seek(0)

    return arquivo
