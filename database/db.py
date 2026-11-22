

import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "corretor.db"


def conectar():
    """Abre uma conexão com o SQLite."""

    conexao = sqlite3.connect(DB_PATH)

    conexao.row_factory = sqlite3.Row

    conexao.execute("PRAGMA foreign_keys = ON")

    return conexao


def inicializar_banco():
    """Cria e atualiza as tabelas do sistema."""

    conexao = conectar()

    conexao.executescript("""

        CREATE TABLE IF NOT EXISTS provas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            quantidade_questoes INTEGER NOT NULL,
            data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS questoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prova_id INTEGER NOT NULL,
            numero INTEGER NOT NULL,
            alternativa_correta TEXT NOT NULL,
            peso REAL NOT NULL DEFAULT 1.0,

            FOREIGN KEY (prova_id)
                REFERENCES provas(id)
                ON DELETE CASCADE,

            UNIQUE (prova_id, numero)
        );

    """)

    
    colunas = conexao.execute(
        "PRAGMA table_info(provas)"
    ).fetchall()

    nomes_colunas = [
        coluna["name"] for coluna in colunas
    ]

    # Adicionar valor_total em bancos antigos
    if "valor_total" not in nomes_colunas:

        conexao.execute("""
            ALTER TABLE provas
            ADD COLUMN valor_total REAL NOT NULL DEFAULT 0
        """)

        # Preservar os valores das provas anteriores
        conexao.execute("""
            UPDATE provas
            SET valor_total = (
                SELECT COALESCE(SUM(peso), 0)
                FROM questoes
                WHERE questoes.prova_id = provas.id
            )
        """)

    
    conexao.execute("""

        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prova_id INTEGER NOT NULL,
            aluno_nome TEXT NOT NULL,
            total_questoes INTEGER NOT NULL,
            acertos INTEGER NOT NULL,
            erros INTEGER NOT NULL,
            em_branco INTEGER NOT NULL,
            percentual REAL NOT NULL,
            nota REAL NOT NULL,
            data_correcao DATETIME DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (prova_id)
                REFERENCES provas(id)
                ON DELETE CASCADE
        )

    """)

   
    conexao.execute("""

        CREATE TABLE IF NOT EXISTS answers_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            result_id INTEGER NOT NULL,
            numero_questao INTEGER NOT NULL,
            resposta_aluno TEXT,
            resposta_correta TEXT NOT NULL,
            situacao TEXT NOT NULL,
            peso REAL NOT NULL,
            pontos_obtidos REAL NOT NULL,

            FOREIGN KEY (result_id)
                REFERENCES results(id)
                ON DELETE CASCADE
        )

    """)

    conexao.commit()
    conexao.close()


if __name__ == "__main__":

    inicializar_banco()

    print("Banco de dados inicializado com sucesso!")
