import json
import sqlite3
import pika
import time
import os
import traceback
from datetime import datetime

# ============================================================================
# CONFIGURAÇÕES E CAMINHO DO BANCO DE DADOS
# ============================================================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "central.db")
print(f"📂 Serviço de Previsão a usar: {DB_PATH}")

# ============================================================================
# ALGORITMO DE CÁLCULO DE DESEMPENHO E RECOMENDAÇÃO
# ============================================================================
def analisar_desempenho_e_recomendar(
    notas_obtidas, 
    faltas_atuais, 
    total_provas=3, 
    max_faltas=15, 
    media_aprovacao=10.0, 
    media_recurso=7.0
):
    provas_realizadas = len(notas_obtidas)
    provas_restantes = max(0, total_provas - provas_realizadas)
    soma_atual = sum(notas_obtidas)
    media_atual = round(soma_atual / provas_realizadas, 2) if provas_realizadas > 0 else 0.0

    percentual_faltas = (faltas_atuais / max_faltas) * 100 if max_faltas > 0 else 0
    risco_faltas = "CRÍTICO" if faltas_atuais >= max_faltas else ("ALTO" if percentual_faltas >= 75 else "BAIXO")

    pontos_necessarios = (media_aprovacao * total_provas) - soma_atual
    nota_meta = round(pontos_necessarios / provas_restantes, 2) if provas_restantes > 0 else 0.0

    # Avaliação do Estado e Risco
    if faltas_atuais > max_faltas:
        previsao = "REPROVADO POR FALTAS"
        nivel_risco = "ALTO"
    elif provas_restantes == 0:
        if media_atual >= media_aprovacao:
            previsao = "APROVADO"
            nivel_risco = "BAIXO"
        elif media_atual >= media_recurso:
            previsao = "EM EXAME / RECURSO"
            nivel_risco = "MEDIO"
        else:
            previsao = "REPROVADO POR NOTA"
            nivel_risco = "ALTO"
    else:
        if nota_meta <= 0:
            previsao = "APROVAÇÃO GARANTIDA"
            nivel_risco = "BAIXO"
        elif nota_meta <= 20.0:
            previsao = "EM RISCO - APROVAÇÃO POSSÍVEL"
            nivel_risco = "MEDIO" if nota_meta <= 12.0 else "ALTO"
        else:
            previsao = "ENCAMINHADO PARA RECURSO"
            nivel_risco = "ALTO"

    # Geração de Recomendações
    recomendacoes = []
    if risco_faltas == "CRÍTICO":
        recomendacoes.append("⚠️ Limite de faltas atingido!")
    elif risco_faltas == "ALTO":
        recomendacoes.append(f"⚠️ Atenção: consumiu {percentual_faltas:.0f}% das faltas permitidas.")

    if provas_restantes > 0 and nota_meta > 0:
        if nota_meta <= 20.0:
            recomendacoes.append(f"🎯 Meta: Média de {nota_meta} vls nas próximas {provas_restantes} prova(s).")
        else:
            recomendacoes.append("📌 Foco no Exame de Recurso (aprovação direta inviável).")

    return {
        "media_acumulada": media_atual,
        "previsao": previsao,
        "nivel_risco": nivel_risco,
        "nota_meta": max(0.0, nota_meta) if provas_restantes > 0 else None,
        "recomendacoes": json.dumps(recomendacoes, ensure_ascii=False)
    }

# ============================================================================
# PROCESSAMENTO SÍNCRONO DA MENSAGEM
# ============================================================================
def processar_mensagem_sync(body):
    try:
        data = json.loads(body)
        aluno_id = data.get("aluno_id")
        matricula = data.get("matricula")
        ano_letivo = data.get("ano_letivo")
        semestre = data.get("semestre")
        disciplinas = data.get("disciplinas", [])
        print(f"📩 Processando {matricula} - {ano_letivo} - {semestre}")

        if not aluno_id or not ano_letivo or not semestre or not disciplinas:
            print("❌ Mensagem inválida: faltam campos obrigatórios")
            return

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        total_notas = 0
        total_faltas = 0
        count_disciplinas = 0
        disciplinas_em_risco = 0

        for disc in disciplinas:
            codigo = disc.get("codigo")
            cursor.execute("SELECT id FROM disciplinas WHERE codigo = ?", (codigo,))
            row_disc = cursor.fetchone()
            if not row_disc:
                print(f"⚠️ Disciplina {codigo} não encontrada no BD. A ignorar.")
                continue
            disciplina_id = row_disc[0]

            p1 = disc.get("parcial1")
            p2 = disc.get("parcial2")
            exame = disc.get("exame")
            faltas = disc.get("faltas", 0)

            # 1. Persistir/Atualizar notas
            cursor.execute("""
                INSERT INTO notas (aluno_id, disciplina_id, parcial1, parcial2, exame, faltas, ano_letivo)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(aluno_id, disciplina_id, ano_letivo) DO UPDATE SET
                    parcial1 = excluded.parcial1,
                    parcial2 = excluded.parcial2,
                    exame = excluded.exame,
                    faltas = excluded.faltas
            """, (aluno_id, disciplina_id, p1, p2, exame, faltas, ano_letivo))

            # 2. Montar lista de notas obtidas para o algoritmo
            notas_obtidas = [n for n in [p1, p2, exame] if n is not None]
            
            res = analisar_desempenho_e_recomendar(notas_obtidas, faltas)
            data_calculo = datetime.now().isoformat()

            media_parcial = round((p1 + p2) / 2, 2) if (p1 is not None and p2 is not None) else None
            media_final = res["media_acumulada"]

            cursor.execute("""
                INSERT INTO previsoes (aluno_id, disciplina_id, ano_letivo, media_parcial, media_final, risco, recomendacao, data_calculo)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(aluno_id, disciplina_id, ano_letivo) DO UPDATE SET
                    media_parcial = excluded.media_parcial,
                    media_final = excluded.media_final,
                    risco = excluded.risco,
                    recomendacao = excluded.recomendacao,
                    data_calculo = excluded.data_calculo
            """, (aluno_id, disciplina_id, ano_letivo, media_parcial, media_final, res["nivel_risco"], res["recomendacoes"], data_calculo))

            total_faltas += faltas
            if media_final is not None:
                total_notas += media_final
                count_disciplinas += 1
            if res["nivel_risco"] in ("ALTO", "MEDIO"):
                disciplinas_em_risco += 1

            print(f"✅ Previsão para {matricula} - {codigo}: {res['previsao']} (Risco: {res['nivel_risco']})")

        # 3. Previsão agregada do semestre
        if count_disciplinas > 0:
            media_global = round(total_notas / count_disciplinas, 2)
            if disciplinas_em_risco >= 2:
                risco_global = "ALTO"
                recomendacao_geral = f"🔴 Risco Global Alto: {disciplinas_em_risco} disciplinas em risco. Priorize estudos e reduza faltas."
            elif disciplinas_em_risco == 1:
                risco_global = "MEDIO"
                recomendacao_geral = "🟡 Risco Global Médio: 1 disciplina em risco. Atenção reforçada necessária."
            else:
                risco_global = "BAIXO"
                recomendacao_geral = "🟢 Risco Global Baixo: Desempenho satisfatório em todas as disciplinas."

            cursor.execute("""
                INSERT INTO previsoes_semestre 
                (aluno_id, ano_letivo, semestre_nome, media_global, total_faltas, disciplinas_em_risco, risco_global, recomendacao_geral, data_calculo)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(aluno_id, ano_letivo, semestre_nome) DO UPDATE SET
                    media_global = excluded.media_global,
                    total_faltas = excluded.total_faltas,
                    disciplinas_em_risco = excluded.disciplinas_em_risco,
                    risco_global = excluded.risco_global,
                    recomendacao_geral = excluded.recomendacao_geral,
                    data_calculo = excluded.data_calculo
            """, (aluno_id, ano_letivo, semestre, media_global, total_faltas, disciplinas_em_risco,
                  risco_global, recomendacao_geral, datetime.now().isoformat()))

            print(f"✅ Previsão agregada para {matricula} - {ano_letivo} - {semestre}: {risco_global}")

        conn.commit()
        conn.close()
        print(f"✅ Processamento concluído para {matricula}")

    except Exception as e:
        print(f"❌ Erro ao processar mensagem: {e}")
        traceback.print_exc()

# ============================================================================
# CALLBACK E INICIALIZAÇÃO DO CONSUMIDOR RABBITMQ
# ============================================================================
def callback(ch, method, properties, body):
    print("📨 Mensagem recebida!")
    processar_mensagem_sync(body)

def iniciar_consumidor():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Estrutura do Banco de Dados
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
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS anos_academicos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT UNIQUE NOT NULL,
            ativo INTEGER DEFAULT 1
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS semestres (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ano_academico_id INTEGER,
            nome TEXT NOT NULL,
            FOREIGN KEY(ano_academico_id) REFERENCES anos_academicos(id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS disciplinas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT UNIQUE NOT NULL,
            nome TEXT NOT NULL,
            semestre_id INTEGER,
            creditos INTEGER DEFAULT 0,
            FOREIGN KEY(semestre_id) REFERENCES semestres(id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            aluno_id INTEGER,
            disciplina_id INTEGER,
            parcial1 REAL,
            parcial2 REAL,
            exame REAL,
            faltas INTEGER DEFAULT 0,
            ano_letivo TEXT NOT NULL,
            FOREIGN KEY(aluno_id) REFERENCES users(id),
            FOREIGN KEY(disciplina_id) REFERENCES disciplinas(id),
            UNIQUE(aluno_id, disciplina_id, ano_letivo)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS previsoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            aluno_id INTEGER,
            disciplina_id INTEGER,
            ano_letivo TEXT NOT NULL,
            media_parcial REAL,
            media_final REAL,
            risco TEXT,
            recomendacao TEXT,
            data_calculo TEXT,
            FOREIGN KEY(aluno_id) REFERENCES users(id),
            FOREIGN KEY(disciplina_id) REFERENCES disciplinas(id),
            UNIQUE(aluno_id, disciplina_id, ano_letivo)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS previsoes_semestre (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            aluno_id INTEGER,
            ano_letivo TEXT NOT NULL,
            semestre_nome TEXT NOT NULL,
            media_global REAL,
            total_faltas INTEGER,
            disciplinas_em_risco INTEGER,
            risco_global TEXT,
            recomendacao_geral TEXT,
            data_calculo TEXT,
            FOREIGN KEY(aluno_id) REFERENCES users(id),
            UNIQUE(aluno_id, ano_letivo, semestre_nome)
        )
    ''')
    conn.commit()
    conn.close()
    print(f"✅ Tabelas criadas/verificadas em {DB_PATH}")

    RABBIT_HOST = os.getenv("RABBIT_HOST", "localhost")
    RABBIT_PORT = int(os.getenv("RABBIT_PORT", 5679))

    while True:
        try:
            print(f"🔗 A conectar ao RabbitMQ em {RABBIT_HOST}:{RABBIT_PORT}...")
            params = pika.ConnectionParameters(
                host=RABBIT_HOST,
                port=RABBIT_PORT,
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
            print(f"❌ Erro na conexão com RabbitMQ: {e}")
            print("🔄 A reconectar em 10 segundos...")
            time.sleep(10)
        except KeyboardInterrupt:
            print("👋 Encerrando o serviço...")
            break
        except Exception as e:
            print(f"❌ Erro inesperado: {e}")
            time.sleep(10)

if __name__ == "__main__":
    iniciar_consumidor()