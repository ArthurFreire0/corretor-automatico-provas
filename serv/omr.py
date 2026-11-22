
import cv2
import numpy as np



# CONFIGURAÇÕES DA FOLHA


ALTERNATIVAS = ["A", "B", "C", "D", "E"]

MAX_QUESTOES = 100

QUESTOES_POR_PAGINA = 50
QUESTOES_POR_COLUNA = 25

DPI = 150

LARGURA_MM = 210
ALTURA_MM = 297

# Limiares iniciais. Serão calibrados com testes reais.
LIMITE_PREENCHIMENTO = 0.58
LIMITE_DUVIDA = 0.15


def mm_para_pixel(valor):
    """Converte milímetros para pixels."""

    return round(valor * DPI / 25.4)



# DETECTAR OS MARCADORES




def detectar_marcadores(imagem):
    """
    Localiza os quatro marcadores pretos da folha.

    Utiliza threshold adaptativo para lidar com
    iluminação irregular e sombras.

    Retorna:
    superior esquerdo,
    superior direito,
    inferior direito,
    inferior esquerdo.
    """

    altura, largura = imagem.shape[:2]

    cinza = cv2.cvtColor(
        imagem,
        cv2.COLOR_BGR2GRAY
    )

    suavizada = cv2.GaussianBlur(
        cinza,
        (3, 3),
        0
    )

    binaria = cv2.adaptiveThreshold(
        suavizada,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        51,
        12
    )

    contornos, _ = cv2.findContours(
        binaria,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    referencia = min(largura, altura)

    tamanho_minimo = referencia * 0.012
    tamanho_maximo = referencia * 0.10

    candidatos = []

    for contorno in contornos:

        area = cv2.contourArea(contorno)

        if area <= 0:
            continue

        x, y, w, h = cv2.boundingRect(contorno)

        if not (
            tamanho_minimo <= w <= tamanho_maximo
            and tamanho_minimo <= h <= tamanho_maximo
        ):
            continue

        proporcao = w / float(h)

        if not 0.60 <= proporcao <= 1.50:
            continue

        preenchimento = area / float(w * h)

        if preenchimento < 0.40:
            continue

        centro_x = x + w / 2
        centro_y = y + h / 2

        candidatos.append({
            "centro": (centro_x, centro_y),
            "area": area
        })


    regioes = {
        "se": (0, 0, largura * 0.35, altura * 0.25),

        "sd": (
            largura * 0.65,
            0,
            largura,
            altura * 0.25
        ),

        "id": (
            largura * 0.65,
            altura * 0.75,
            largura,
            altura
        ),

        "ie": (
            0,
            altura * 0.75,
            largura * 0.35,
            altura
        )
    }

    pontos = []

    for nome, regiao in regioes.items():

        x1, y1, x2, y2 = regiao

        encontrados = [
            candidato
            for candidato in candidatos
            if (
                x1 <= candidato["centro"][0] <= x2
                and y1 <= candidato["centro"][1] <= y2
            )
        ]

        if not encontrados:

            raise ValueError(
                f"Marcador do quadrante {nome} não encontrado. "
                f"Foram encontrados {len(candidatos)} candidatos no total."
            )

        # O marcador de registro é maior que as bolinhas
        # das questões e costuma ter maior área.
        escolhido = max(
            encontrados,
            key=lambda item: item["area"]
        )

        pontos.append(escolhido["centro"])

    return np.array(
        pontos,
        dtype=np.float32
    )



# ALINHAR A FOLHA


def alinhar_folha(imagem):
    """
    Corrige a perspectiva utilizando os centros
    dos quatro marcadores.
    """

    marcadores = detectar_marcadores(imagem)

    largura = mm_para_pixel(LARGURA_MM)
    altura = mm_para_pixel(ALTURA_MM)

    # Centros esperados dos marcadores.
    margem = mm_para_pixel(12)

    destino = np.array([
        [margem, margem],
        [largura - margem, margem],
        [largura - margem, altura - margem],
        [margem, altura - margem]
    ], dtype=np.float32)

    matriz = cv2.getPerspectiveTransform(
        marcadores,
        destino
    )

    alinhada = cv2.warpPerspective(
        imagem,
        matriz,
        (largura, altura)
    )

    return alinhada



# PREPARAR IMAGEM PARA LEITURA


def preparar_imagem(imagem):

    cinza = cv2.cvtColor(
        imagem,
        cv2.COLOR_BGR2GRAY
    )

    binaria = cv2.adaptiveThreshold(
        cinza,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        31,
        10
    )

    return binaria



# MEDIR PREENCHIMENTO DA BOLINHA


def medir_preenchimento(binaria, centro_x, centro_y):
    """
    Mede a quantidade de pixels escuros
    em um anel interno da alternativa.

    O anel evita contar diretamente a letra
    impressa no centro da bolinha.
    """

    raio_interno = mm_para_pixel(0.95)
    raio_externo = mm_para_pixel(1.65)

    altura, largura = binaria.shape

    x1 = max(0, centro_x - raio_externo)
    x2 = min(largura, centro_x + raio_externo + 1)

    y1 = max(0, centro_y - raio_externo)
    y2 = min(altura, centro_y + raio_externo + 1)

    recorte = binaria[y1:y2, x1:x2]

    yy, xx = np.ogrid[y1:y2, x1:x2]

    distancia = np.sqrt(
        (xx - centro_x) ** 2
        + (yy - centro_y) ** 2
    )

    mascara = (
        (distancia >= raio_interno)
        & (distancia <= raio_externo)
    )

    total = np.count_nonzero(mascara)

    if total == 0:
        return 0.0

    escuros = np.count_nonzero(
        (recorte > 0) & mascara
    )

    return escuros / float(total)



# IDENTIFICAR UMA RESPOSTA



def identificar_resposta(pontuacoes):
    """
    Classifica uma questão como:
    reconhecida, em branco, dupla ou duvidosa.

    O limite de preenchimento foi calibrado
    inicialmente com a folha de teste fotografada.
    """

    ordenadas = sorted(
        pontuacoes.items(),
        key=lambda item: item[1],
        reverse=True
    )

    primeira = ordenadas[0]
    segunda = ordenadas[1]

    marcadas = [
        alternativa
        for alternativa, valor in ordenadas
        if valor >= LIMITE_PREENCHIMENTO
    ]

    if len(marcadas) > 1:

        return {
            "resposta": None,
            "situacao": "dupla"
        }

    if len(marcadas) == 0:

        return {
            "resposta": None,
            "situacao": "em_branco"
        }

    if primeira[1] - segunda[1] < LIMITE_DUVIDA:

        return {
            "resposta": None,
            "situacao": "duvida"
        }

    return {
        "resposta": primeira[0],
        "situacao": "reconhecida"
    }




# LER UMA PÁGINA DE 1 A 50 QUESTÕES


def ler_pagina(imagem, quantidade_questoes):
    """
    Reconhece as alternativas de uma página.

    A folha utiliza duas colunas de 25 questões.
    """

    if not 1 <= quantidade_questoes <= 50:

        raise ValueError(
            "Esta função recebe páginas com até 50 questões."
        )

    binaria = preparar_imagem(imagem)

   
    posicoes_colunas = [23, 110]

    y_inicial = 114

    espacamento_vertical = 6.5

    inicio_alternativas = 18
    espacamento_horizontal = 9
    
    resultados = []

    for indice in range(quantidade_questoes):

        coluna = indice // QUESTOES_POR_COLUNA
        linha = indice % QUESTOES_POR_COLUNA

        x_base = posicoes_colunas[coluna]

        y_base = (
            y_inicial
            + linha * espacamento_vertical
        )

        pontuacoes = {}

        for indice_alt, alternativa in enumerate(ALTERNATIVAS):

            x_mm = (
                x_base
                + inicio_alternativas
                + indice_alt * espacamento_horizontal
            )

            y_mm = y_base

            centro_x = mm_para_pixel(x_mm)
            centro_y = mm_para_pixel(y_mm)

            pontuacao = medir_preenchimento(
                binaria,
                centro_x,
                centro_y
            )

            pontuacoes[alternativa] = round(
                pontuacao,
                3
            )

        classificacao = identificar_resposta(
            pontuacoes
        )

        resultados.append({
            "numero": indice + 1,
            "resposta": classificacao["resposta"],
            "situacao": classificacao["situacao"],
            "pontuacoes": pontuacoes
        })

    return resultados


# FUNÇÃO PRINCIPAL DE RECONHECIMENTO

def reconhecer_respostas(conteudo_imagem, quantidade_questoes):
    """
    Recebe os bytes de uma imagem,
    alinha a folha e reconhece as respostas.

    Nesta versão, processa uma página de até 50 questões.
    """

    if not 1 <= quantidade_questoes <= MAX_QUESTOES:

        raise ValueError(
            "A prova deve possuir entre 1 e 100 questões."
        )

    if quantidade_questoes > QUESTOES_POR_PAGINA:

        raise ValueError(
            "O reconhecimento de provas com mais de 50 questões "
            "será implementado após a validação de uma página."
        )

    dados = np.frombuffer(
        conteudo_imagem,
        dtype=np.uint8
    )

    imagem = cv2.imdecode(
        dados,
        cv2.IMREAD_COLOR
    )

    if imagem is None:

        raise ValueError(
            "Não foi possível abrir a imagem enviada."
        )

    folha_alinhada = alinhar_folha(imagem)

    respostas = ler_pagina(
        folha_alinhada,
        quantidade_questoes
    )

    return {
        "sucesso": True,
        "quantidade_questoes": quantidade_questoes,
        "respostas": respostas,
        "folha_alinhada": folha_alinhada
    }
