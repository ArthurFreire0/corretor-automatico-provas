#  Corretor Automático de Provas

Sistema multiplataforma desenvolvido em Python para automatizar a correção de provas objetivas, utilizando técnicas de processamento de imagens e reconhecimento óptico de marcações (OMR).

O projeto permite cadastrar provas, gerar folhas de respostas, realizar a leitura das marcações dos alunos por meio de imagens e apresentar os resultados das correções.

##  Objetivo

Desenvolver uma solução que facilite e agilize o processo de correção de avaliações objetivas, reduzindo o trabalho manual dos professores e proporcionando maior organização no armazenamento e consulta dos resultados.

##  Funcionalidades

- **Cadastro de provas:** registro de avaliações e seus respectivos gabaritos.
- **Geração de folhas de respostas:** criação de modelos de folhas de respostas para impressão, com alternativas de A a E.
- **Correção automática:** identificação das alternativas preenchidas pelos alunos utilizando processamento de imagens (OMR).
- **Captura de imagens:** possibilidade de utilizar a câmera ou enviar imagens armazenadas no computador.
- **Resultados:** apresentação das respostas identificadas e das notas obtidas pelos alunos.
- **Histórico de correções:** consulta às provas que já foram corrigidas.

##  Tecnologias utilizadas

| Tecnologia | Aplicação |
|---|---|
| Python | Linguagem principal |
| Flask | Desenvolvimento da aplicação web |
| OpenCV | Processamento e análise de imagens |
| NumPy | Operações e processamento de matrizes |
| SQLite | Banco de dados |
| HTML | Estrutura das interfaces |
| ReportLab | Geração de documentos PDF |

##  Estrutura do projeto

```text
CORRETOR DE PROVAS/
│
├── app.py
├── requirement.txt
│
├── database/
│   └── db.py
│
├── routes/
│   ├── prov.py
│   ├── results.py
│   └── sheet.py
│
├── serv/
│   ├── grading.py
│   ├── omr.py
│   └── sheet_gen.py
│
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── cad_prov.html
│   ├── corr_prov.html
│   ├── det_prov.html
│   ├── hist.html
│   ├── result.html
│   └── ...
│
└── README.md
```

##  Como executar o projeto

### 1. Pré-requisitos

- Python instalado.
- Git instalado.
- Visual Studio Code (recomendado).

### 2. Clonar o repositório

```bash
git clone https://github.com/ArthurFreire0/corretor-automatico-provas.git
```

Entre na pasta do projeto:

```bash
cd corretor-automatico-provas
```

### 3. Criar o ambiente virtual

```bash
python -m venv .venv
```

### 4. Ativar o ambiente virtual

No Windows (PowerShell):

```powershell
.venv\Scripts\Activate.ps1
```

### 5. Instalar as dependências

```bash
pip install -r requirement.txt
```

### 6. Executar a aplicação

```bash
python app.py
```

Após iniciar o servidor, acesse o endereço local indicado no terminal pelo Flask.

##  Sobre o funcionamento

O sistema utiliza técnicas de Optical Mark Recognition (OMR), ou reconhecimento óptico de marcações, para identificar as alternativas preenchidas nas folhas de respostas.

O processamento envolve a análise das regiões correspondentes às alternativas, permitindo identificar as marcações realizadas pelos alunos e compará-las com o gabarito cadastrado.

##  Projeto acadêmico

Projeto desenvolvido como parte das atividades acadêmicas do curso de Ciência da Computação, com foco na aplicação prática de programação, processamento digital de imagens, desenvolvimento web e banco de dados.

---

**Desenvolvido por Arthur Freire**

GitHub: [@ArthurFreire0](https://github.com/ArthurFreire0)