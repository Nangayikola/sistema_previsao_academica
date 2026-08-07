import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "central.db")

def limpar_e_inserir():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Apaga todas as disciplinas
    cursor.execute("DELETE FROM disciplinas")
    print("✅ Todas as disciplinas removidas.")

    # Insere as 18 disciplinas do plano curricular
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

    for disc in disciplinas:
        cursor.execute(
            "INSERT INTO disciplinas (codigo, nome, semestre, creditos) VALUES (?, ?, ?, ?)",
            (disc["codigo"], disc["nome"], disc["semestre"], 0)
        )
        print(f"✅ Inserida: {disc['codigo']} - {disc['nome']} ({disc['semestre']})")

    conn.commit()
    conn.close()
    print(f"\n📊 Total: {len(disciplinas)} disciplinas inseridas.")

if __name__ == "__main__":
    limpar_e_inserir()