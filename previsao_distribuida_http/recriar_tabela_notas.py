import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "central.db")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Apagar tabela existente
cursor.execute("DROP TABLE IF EXISTS notas")
print("🗑️ Tabela notas removida.")

# Recriar com a estrutura correta
cursor.execute('''
    CREATE TABLE notas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        aluno_id INTEGER,
        disciplina_id INTEGER,
        nota REAL,
        faltas INTEGER DEFAULT 0,
        semestre TEXT NOT NULL,
        data_avaliacao TEXT,
        FOREIGN KEY(aluno_id) REFERENCES users(id),
        FOREIGN KEY(disciplina_id) REFERENCES disciplinas(id)
    )
''')
conn.commit()
conn.close()
print("✅ Tabela notas recriada com sucesso!")