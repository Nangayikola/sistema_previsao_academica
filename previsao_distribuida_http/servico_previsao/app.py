import json
import sqlite3
import pika
import time
import os
from datetime import datetime

# ---- Caminho absoluto para o ficheiro central.db na raiz do projeto ----
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = r"C:\Users\felis\OneDrive\Documentos\GitHub\sistema_previsao_academica\previsao_distribuida_http\central.db"
print(f"📂 Serviço de Previsão a usar: {DB_PATH}")

def calcular_risco(notas: list, faltas: int = 0, total_aulas: int = 40):
    """
    Calcula o risco de reprovação com base nas notas e faltas.
    Retorna: (risco, media_estimada, recomendacao_detalhada)
    """
    if not notas:
        return ("alto", 0.0, 
                "⚠️ Sem notas registadas. Recomenda-se que o aluno comece a registar o seu desempenho "
                "o mais rapidamente possível e procure apoio pedagógico para não ficar em situação de risco.")

    media = sum(notas) / len(notas)
    perc_faltas = faltas / total_aulas if total_aulas > 0 else 0

    # ---- RISCO ALTO ----
    if media < 5.0 or perc_faltas > 0.25:
        risco = "alto"
        recomendacao = (
            f"🔴 **Risco Alto de Reprovação**\n\n"
            f"📊 Média atual: {media:.2f} (abaixo do mínimo recomendado de 5.0)\n"
            f"📅 Faltas: {faltas} ({perc_faltas*100:.1f}%) – ultrapassa o limite de 25%\n\n"
            "### 🎯 Plano de Ação Imediato:\n"
            "1. **Monitoria intensiva** – Inscreva-se nas monitorias da disciplina o mais rápido possível.\n"
            "2. **Regularização de faltas** – Apresente justificativas para as faltas e procure compensar com trabalhos extras, se permitido.\n"
            "3. **Plano de estudos diário** – Dedique pelo menos 2 horas por dia a esta disciplina, com foco nos tópicos com mais dificuldade.\n"
            "4. **Revisão de conteúdos** – Revise os conteúdos das aulas anteriores, principalmente os que tiveram menor aproveitamento.\n"
            "5. **Simulados e exercícios** – Resolva pelo menos 10 exercícios por semana para praticar.\n"
            "6. **Agendamento com o professor** – Marque uma reunião com o docente para discutir as dificuldades específicas.\n"
            "7. **Grupo de estudo** – Junte-se a um grupo de estudo com colegas para trocar conhecimentos.\n\n"
            "⚠️ **Ação urgente**: A situação é crítica. Recomenda-se intervenção pedagógica imediata."
        )
        return risco, round(media, 2), recomendacao

    # ---- RISCO MÉDIO ----
    if media < 6.5:
        risco = "medio"
        recomendacao = (
            f"🟡 **Risco Médio de Reprovação**\n\n"
            f"📊 Média atual: {media:.2f} (próxima do limite mínimo de 5.0)\n"
            f"📅 Faltas: {faltas} ({perc_faltas*100:.1f}%) – dentro do limite, mas requer atenção\n\n"
            "### 📌 Plano de Melhoria:\n"
            "1. **Estudo extra semanal** – Adicione 4 horas de estudo suplementar à disciplina nas próximas 4 semanas.\n"
            "2. **Exercícios práticos** – Resolva exercícios adicionais dos tópicos onde teve notas mais baixas.\n"
            "3. **Acompanhamento com monitor** – Participe em pelo menos 2 sessões de monitoria por mês.\n"
            "4. **Evitar faltas** – Mantenha a frequência regular para não agravar o risco.\n"
            "5. **Autoavaliação** – Faça uma autoavaliação semanal para monitorizar o progresso.\n"
            "6. **Material complementar** – Utilize livros ou vídeos recomendados pelo professor para reforçar a aprendizagem.\n\n"
            "💡 **Dica**: Com dedicação extra, é possível melhorar o desempenho e evitar a reprovação."
        )
        return risco, round(media, 2), recomendacao

    # ---- RISCO BAIXO ----
    else:
        risco = "baixo"
        recomendacao = (
            f"🟢 **Risco Baixo de Reprovação**\n\n"
            f"📊 Média atual: {media:.2f} (acima de 6.5)\n"
            f"📅 Faltas: {faltas} ({perc_faltas*100:.1f}%) – excelente frequência\n\n"
            "### ✅ Recomendações para Manter o Bom Desempenho:\n"
            "1. **Mantenha o ritmo** – Continue com a mesma dedicação e disciplina.\n"
            "2. **Aprofundamento** – Explore conteúdos avançados para solidificar o conhecimento.\n"
            "3. **Partilha de conhecimento** – Ajude colegas com dificuldades – isso reforça a sua própria aprendizagem.\n"
            "4. **Participação ativa** – Continue participando das aulas e tirando dúvidas.\n"
            "5. **Revisão periódica** – Faça revisões semanais para não acumular matéria.\n"
            "6. **Desafios extras** – Experimente resolver exercícios de níveis superiores para testar os limites do seu conhecimento.\n\n"
            "🌟 **Parabéns!** Continue assim e aproveite para aprofundar os temas que mais lhe interessam."
        )
        return risco, round(media, 2), recomendacao

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

            risco, media_est, recomendacao = calcular_risco(notas, faltas)
            data_calculo = datetime.now().isoformat()

            cursor.execute(
                """INSERT INTO previsoes 
                   (aluno_matricula, disciplina_codigo, risco, media_estimada, recomendacao, data_calculo) 
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (matricula, codigo, risco, media_est, recomendacao, data_calculo)
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