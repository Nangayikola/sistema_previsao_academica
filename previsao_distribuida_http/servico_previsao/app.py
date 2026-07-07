import json
import sqlite3
import pika
import time
import os
from datetime import datetime  # <-- importação adicionada

# ---- Caminho absoluto para o ficheiro central.db na raiz do projeto ----
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = r"C:\Users\felis\OneDrive\Documentos\GitHub\sistema_previsao_academica\previsao_distribuida_http\central.db"
print(f"📂 Serviço de Previsão a usar: {DB_PATH}")

def calcular_risco(notas: list, faltas: int = 0, total_aulas: int = 40):
    if not notas:
        return "alto", 0.0, "Sem notas registadas."
    media = sum(notas) / len(notas)
    perc_faltas = faltas / total_aulas if total_aulas > 0 else 0
    if media < 5.0 or perc_faltas > 0.25:
        return "alto", round(media, 2), "Procurar monitoria e regularizar faltas imediatamente."
    elif media < 6.5:
        return "medio", round(media, 2), "Dedicar estudo extra e evitar faltas."
    else:
        return "baixo", round(media, 2), "Parabéns! Continue assim."

RABBIT_HOST = "localhost"

def processar_mensagem_sync(body):
    try:
        data = json.loads(body)
        matricula = data["matricula"]
        disciplinas = data["disciplinas"]
        print(f"📩 Processando {matricula} (síncrono)")

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        for disc in disciplinas:
            codigo = disc["codigo"]
            cursor.execute(
                "SELECT nota, faltas FROM notas WHERE aluno_matricula = ? AND disciplina_codigo = ? ORDER BY data_avaliacao",
                (matricula, codigo)
            )
            rows = cursor.fetchall()
            notas = [r[0] for r in rows]
            faltas = rows[0][1] if rows else 0
            print(f"📊 Notas para {codigo}: {notas}, faltas: {faltas}")
            risco, media_est, rec = calcular_risco(notas, faltas)
            
            # Gera a data/hora atual no formato ISO (ex: 2025-06-24T15:30:00)
            data_calculo = datetime.now().isoformat()
            
            # Inclui a coluna data_calculo no INSERT
            cursor.execute(
                """INSERT INTO previsoes 
                   (aluno_matricula, disciplina_codigo, risco, media_estimada, recomendacao, data_calculo) 
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (matricula, codigo, risco, media_est, rec, data_calculo)
            )
            print(f"✅ Previsão inserida para {matricula} - {codigo}: {risco} (data: {data_calculo})")
        conn.commit()
        conn.close()
        print(f"✅ Todas as previsões guardadas para {matricula}")
    except Exception as e:
        print(f"❌ Erro ao processar: {e}")
        import traceback
        traceback.print_exc()

def callback(ch, method, properties, body):
    print("📨 Mensagem recebida!")
    processar_mensagem_sync(body)

def iniciar_consumidor():
    # Criar tabelas se não existirem no DB_PATH
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            aluno_matricula TEXT,
            disciplina_codigo TEXT,
            nota REAL,
            faltas INTEGER,
            data_avaliacao TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS previsoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            aluno_matricula TEXT,
            disciplina_codigo TEXT,
            risco TEXT,
            media_estimada REAL,
            recomendacao TEXT,
            data_calculo TEXT
        )
    ''')
    conn.commit()
    conn.close()
    print(f"✅ Tabelas criadas/verificadas em {DB_PATH}")

    while True:
        try:
            print("🔗 A conectar ao RabbitMQ...")
            params = pika.ConnectionParameters(
                host=RABBIT_HOST,
                heartbeat=60,
                blocked_connection_timeout=300,
                connection_attempts=10,
                retry_delay=5
            )
            connection = pika.BlockingConnection(params)
            channel = connection.channel()
            channel.queue_declare(queue='previsao_queue', durable=True)
            channel.basic_consume(queue='previsao_queue', on_message_callback=callback, auto_ack=True)
            print("🔮 Serviço de Previsão aguardando mensagens...")
            channel.start_consuming()
        except (pika.exceptions.AMQPConnectionError, pika.exceptions.AMQPChannelError, pika.exceptions.StreamLostError) as e:
            print(f"❌ Erro na conexão: {e}")
            print("🔄 A reconectar em 10 segundos...")
            time.sleep(10)
            continue
        except KeyboardInterrupt:
            print("👋 Encerrando...")
            break
        except Exception as e:
            print(f"❌ Erro inesperado: {e}")
            time.sleep(10)
            continue

if __name__ == "__main__":
    iniciar_consumidor()