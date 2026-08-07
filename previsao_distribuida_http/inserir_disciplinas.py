import sqlite3
import os

# ---- Caminho do banco de dados ----
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "central.db")

# ---- Lista de disciplinas ----
disciplinas = [
    # I Semestre (1º grupo)
    {"codigo": "IA", "nome": "Inteligência Artificial Aplicada", "semestre": "I SEMESTRE"},
    {"codigo": "MET", "nome": "Metodologia de Investigação Científica", "semestre": "I SEMESTRE"},
    {"codigo": "RIBT", "nome": "Recuperação de Informação em Base de Texto", "semestre": "I SEMESTRE"},
    {"codigo": "SCAD", "nome": "Sistemas Computacionais de Apoio a Decisão", "semestre": "I SEMESTRE"},
    {"codigo": "TASD", "nome": "Tópicos Avançados de Sistemas Distribuídos", "semestre": "I SEMESTRE"},

    # II Semestre (1º grupo)
    {"codigo": "TM", "nome": "Tópicos de Matemática", "semestre": "II SEMESTRE"},
    {"codigo": "CU", "nome": "Computação Ubíqua", "semestre": "II SEMESTRE"},
    {"codigo": "GP", "nome": "Gestão de Projectos", "semestre": "II SEMESTRE"},
    {"codigo": "IPM", "nome": "Interfaces Pessoa-Máquina", "semestre": "II SEMESTRE"},
    {"codigo": "SM", "nome": "Sistemas Multimodais", "semestre": "II SEMESTRE"},
    {"codigo": "TABD", "nome": "Tópicos Avançados de Bases de Dados", "semestre": "II SEMESTRE"},

    # I Semestre (2º grupo)
    {"codigo": "DIO1", "nome": "Desenvolvimento de Investigação Orientada I", "semestre": "I SEMESTRE"},
    {"codigo": "EPD", "nome": "Elaboração do Projecto de Dissertação", "semestre": "I SEMESTRE"},
    {"codigo": "EST", "nome": "Estágio", "semestre": "I SEMESTRE"},
    {"codigo": "SI", "nome": "Seminários de Investigação", "semestre": "I SEMESTRE"},

    # II Semestre (2º grupo)
    {"codigo": "DIO2", "nome": "Desenvolvimento de Investigação Orientada II", "semestre": "II SEMESTRE"},
    {"codigo": "DRE", "nome": "Divulgação dos Resultados, Apresentação de Trabalhos em Eventos", "semestre": "II SEMESTRE"},
    {"codigo": "EDD", "nome": "Elaboração e Defesa da Dissertação", "semestre": "II SEMESTRE"},
]

def inserir_disciplinas():
    if not os.path.exists(DB_PATH):
        print(f"❌ Base de dados não encontrada em: {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Verifica se a tabela disciplinas existe
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='disciplinas'")
    if not cursor.fetchone():
        print("❌ Tabela 'disciplinas' não encontrada. Execute primeiro o serviço de coleta.")
        conn.close()
        return

    # ---- Adicionar colunas em falta ----
    cursor.execute("PRAGMA table_info(disciplinas)")
    colunas_existentes = [col[1] for col in cursor.fetchall()]
    print(f"📋 Colunas existentes: {colunas_existentes}")

    if "nome" not in colunas_existentes:
        print("➕ A adicionar coluna 'nome'...")
        cursor.execute("ALTER TABLE disciplinas ADD COLUMN nome TEXT")
    if "semestre" not in colunas_existentes:
        print("➕ A adicionar coluna 'semestre'...")
        cursor.execute("ALTER TABLE disciplinas ADD COLUMN semestre TEXT")
    if "creditos" not in colunas_existentes:
        print("➕ A adicionar coluna 'creditos'...")
        cursor.execute("ALTER TABLE disciplinas ADD COLUMN creditos INTEGER DEFAULT 0")

    conn.commit()
    print("✅ Colunas adicionadas (se necessário).")

    # ---- Inserir disciplinas ----
    inseridas = 0
    existentes = 0

    for disc in disciplinas:
        # Verifica se já existe
        cursor.execute("SELECT codigo FROM disciplinas WHERE codigo = ?", (disc["codigo"],))
        if cursor.fetchone():
            print(f"⚠️ Disciplina {disc['codigo']} já existe. A ignorar.")
            existentes += 1
            continue

        # Insere nova disciplina
        cursor.execute(
            "INSERT INTO disciplinas (codigo, nome, semestre, creditos) VALUES (?, ?, ?, ?)",
            (disc["codigo"], disc["nome"], disc["semestre"], 0)
        )
        inseridas += 1
        print(f"✅ Inserida: {disc['codigo']} - {disc['nome']} ({disc['semestre']})")

    conn.commit()
    conn.close()

    print(f"\n📊 Resumo: {inseridas} disciplinas inseridas, {existentes} já existentes.")

if __name__ == "__main__":
    inserir_disciplinas()