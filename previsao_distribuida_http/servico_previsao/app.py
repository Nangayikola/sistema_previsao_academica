import json
import sqlite3
import pika
import time
import os
from datetime import datetime

# ---- Caminho absoluto para o ficheiro central.db na raiz do projeto ----
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "central.db")
print(f"📂 Serviço de Previsão a usar: {DB_PATH}")

# ============================================================================
# FUNÇÃO DE CÁLCULO DE RISCO (mantida)
# ============================================================================
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

# ============================================================================
# PROCESSAMENTO DA MENSAGEM
# ============================================================================
def processar_mensagem_sync(body):
    try:
        data = json.loads(body)
        aluno_id = data.get("aluno_id")
        matricula = data.get("matricula")
        semestre = data.get("semestre")
        disciplinas = data.get("disciplinas", [])
        print(f"📩 Processando {matricula} - semestre {semestre}")

        if not aluno_id or not semestre or not disciplinas:
            print("❌ Mensagem inválida: faltam campos obrigatórios")
            return

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # --- 1. Calcular previsões por disciplina ---
        disciplinas_processadas = []
        total_notas = 0
        total_faltas = 0
        count_disciplinas = 0
        disciplinas_em_risco = 0

        for disc in disciplinas:
            codigo = disc["codigo"]
            # Busca o ID da disciplina
            cursor.execute("SELECT id FROM disciplinas WHERE codigo = ?", (codigo,))
            row_disc = cursor.fetchone()
            if not row_disc:
                print(f"⚠️ Disciplina {codigo} não encontrada. A ignorar.")
                continue
            disciplina_id = row_disc[0]

            # Busca todas as notas do aluno na disciplina e semestre
            cursor.execute("""
                SELECT nota, faltas FROM notas
                WHERE aluno_id = ? AND disciplina_id = ? AND semestre = ?
                ORDER BY data_avaliacao
            """, (aluno_id, disciplina_id, semestre))
            rows = cursor.fetchall()
            notas = [r[0] for r in rows]
            faltas = rows[0][1] if rows else 0
            media = sum(notas) / len(notas) if notas else 0
            print(f"📊 {codigo}: notas={notas}, faltas={faltas}, média={media:.2f}")

            # Calcula risco individual
            risco, media_est, recomendacao = calcular_risco(notas, faltas)
            data_calculo = datetime.now().isoformat()

            # Guarda a previsão individual
            cursor.execute("""
                INSERT OR REPLACE INTO previsoes
                (aluno_id, disciplina_id, semestre, risco, media_estimada, recomendacao, data_calculo)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (aluno_id, disciplina_id, semestre, risco, media_est, recomendacao, data_calculo))

            # Acumula para o agregado
            total_notas += media
            total_faltas += faltas
            count_disciplinas += 1
            if risco in ("alto", "medio"):
                disciplinas_em_risco += 1

            disciplinas_processadas.append(codigo)
            print(f"✅ Previsão individual guardada para {matricula} - {codigo}: {risco}")

        # --- 2. Calcular previsão agregada do semestre ---
        if count_disciplinas > 0:
            media_global = total_notas / count_disciplinas
            # Define risco global
            if disciplinas_em_risco >= 2:
                risco_global = "alto"
                recomendacao_geral = (
                    f"🔴 **Risco Global Alto** – {disciplinas_em_risco} disciplinas em risco.\n"
                    "Recomenda-se intervenção imediata: priorize as disciplinas com risco alto, "
                    "procure monitoria e reduza faltas. Consulte o plano de ação individual para cada disciplina."
                )
            elif disciplinas_em_risco == 1:
                risco_global = "medio"
                recomendacao_geral = (
                    f"🟡 **Risco Global Médio** – 1 disciplina em risco.\n"
                    "Dedique atenção extra a essa disciplina e mantenha o bom desempenho nas restantes. "
                    "Evite faltas e acompanhe as monitorias disponíveis."
                )
            else:
                risco_global = "baixo"
                recomendacao_geral = (
                    f"🟢 **Risco Global Baixo** – Nenhuma disciplina em risco.\n"
                    "Continue com o bom desempenho. Aproveite para aprofundar conhecimentos e ajudar colegas."
                )

            # Guarda previsão agregada
            cursor.execute("""
                INSERT OR REPLACE INTO previsoes_semestre
                (aluno_id, semestre, media_global, total_faltas, disciplinas_em_risco, risco_global, recomendacao_geral, data_calculo)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (aluno_id, semestre, round(media_global, 2), total_faltas, disciplinas_em_risco,
                  risco_global, recomendacao_geral, datetime.now().isoformat()))

            print(f"✅ Previsão agregada guardada para {matricula} - {semestre}: {risco_global}")

        conn.commit()
        conn.close()
        print(f"✅ Processamento completo para {matricula} - {semestre}")

    except Exception as e:
        print(f"❌ Erro ao processar: {e}")
        import traceback
        traceback.print_exc()

# ============================================================================
# CONSUMIDOR RABBITMQ
# ============================================================================
def callback(ch, method, properties, body):
    print("📨 Mensagem recebida!")
    processar_mensagem_sync(body)

def iniciar_consumidor():
    # Verifica/cria tabelas necessárias
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Tabela de utilizadores (se não existir, mas já deve existir)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL,
            nome TEXT NOT NULL,
            email TEXT UNIQUE
        )
    ''')

    # Tabela de disciplinas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS disciplinas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT UNIQUE NOT NULL,
            nome TEXT NOT NULL,
            semestre TEXT NOT NULL,
            creditos INTEGER DEFAULT 0
        )
    ''')

    # Tabela de notas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notas (
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

    # Tabela de previsões individuais
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS previsoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            aluno_id INTEGER,
            disciplina_id INTEGER,
            semestre TEXT NOT NULL,
            risco TEXT,
            media_estimada REAL,
            recomendacao TEXT,
            data_calculo TEXT,
            FOREIGN KEY(aluno_id) REFERENCES users(id),
            FOREIGN KEY(disciplina_id) REFERENCES disciplinas(id)
        )
    ''')

    # Tabela de previsões agregadas por semestre
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS previsoes_semestre (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            aluno_id INTEGER,
            semestre TEXT NOT NULL,
            media_global REAL,
            total_faltas INTEGER,
            disciplinas_em_risco INTEGER,
            risco_global TEXT,
            recomendacao_geral TEXT,
            data_calculo TEXT,
            FOREIGN KEY(aluno_id) REFERENCES users(id)
        )
    ''')

    conn.commit()
    conn.close()
    print(f"✅ Tabelas criadas/verificadas em {DB_PATH}")

    # Loop de consumo com reconexão automática
    RABBIT_HOST = "localhost"
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