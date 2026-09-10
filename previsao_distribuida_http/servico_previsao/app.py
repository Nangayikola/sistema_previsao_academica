import json
import sqlite3
import pika
import time
import os
import traceback
from datetime import datetime

try:
    from sklearn.ensemble import RandomForestClassifier
    ML_DISPONIVEL = True
except ImportError:
    RandomForestClassifier = None
    ML_DISPONIVEL = False

# ============================================================================
# CONFIGURAÇÕES E CAMINHO DO BANCO DE DADOS
# ============================================================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "central.db")
print(f"📂 Serviço de Previsão a usar: {DB_PATH}")


def add_column_if_not_exists(conn, table_name, column_sql):
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]
    column_name = column_sql.split()[0]
    if column_name not in columns:
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_sql}")
        print(f"✅ Coluna '{column_name}' adicionada à tabela '{table_name}'")


def obter_contexto_historico(cursor, aluno_id, disciplina_id, ano_letivo_atual):
    """Resume resultados anteriores para personalizar a previsão atual."""
    cursor.execute("""
        SELECT parcial1, parcial2, exame, faltas
        FROM notas
                WHERE disciplina_id = ?
                    AND NOT (aluno_id = ? AND ano_letivo = ?)
        ORDER BY ano_letivo
        """, (disciplina_id, aluno_id, ano_letivo_atual))
    historico_disciplina = cursor.fetchall()

    cursor.execute("""
        SELECT n.parcial1, n.parcial2, n.exame, n.faltas
        FROM notas n
        WHERE n.aluno_id = ? AND n.ano_letivo <> ?
    """, (aluno_id, ano_letivo_atual))
    historico_aluno = cursor.fetchall()

    def resumir(registos):
        medias = []
        aprovados = 0
        for parcial1, parcial2, exame, faltas in registos:
            notas = [nota for nota in (parcial1, parcial2, exame) if nota is not None]
            if not notas:
                continue
            media = sum(notas) / len(notas)
            medias.append(media)
            if len(notas) == 3 and media >= 10 and (faltas or 0) <= 15:
                aprovados += 1
        return {
            "amostras": len(medias),
            "media": sum(medias) / len(medias) if medias else None,
            "taxa_aprovacao": aprovados / len(medias) if medias else None,
        }

    return {
        "disciplina": resumir(historico_disciplina),
        "aluno": resumir(historico_aluno),
    }


def construir_features(parcial1, parcial2, exame, faltas, disciplina_id):
    notas = [nota for nota in (parcial1, parcial2, exame) if nota is not None]
    media = sum(notas) / len(notas) if notas else 0.0
    desvio = (sum((nota - media) ** 2 for nota in notas) / len(notas)) ** 0.5 if notas else 0.0
    tendencia = notas[-1] - notas[0] if len(notas) > 1 else 0.0
    return [media, faltas or 0, len(notas), desvio, tendencia, disciplina_id]


def treinar_modelo_historico(cursor):
    """Treina apenas com resultados completos e retorna None se não houver base confiável."""
    if not ML_DISPONIVEL:
        return None, 0

    cursor.execute("""
        SELECT parcial1, parcial2, exame, faltas, disciplina_id
        FROM notas
        WHERE parcial1 IS NOT NULL AND parcial2 IS NOT NULL AND exame IS NOT NULL
    """)
    registos = cursor.fetchall()
    exemplos = []
    alvos = []
    for parcial1, parcial2, exame, faltas, disciplina_id in registos:
        features = construir_features(parcial1, parcial2, exame, faltas, disciplina_id)
        media = (parcial1 + parcial2 + exame) / 3
        aprovado = int(media >= 10 and (faltas or 0) <= 15)
        exemplos.append(features)
        alvos.append(aprovado)

    if len(exemplos) < 12 or len(set(alvos)) < 2:
        return None, len(exemplos)

    modelo = RandomForestClassifier(
        n_estimators=150,
        max_depth=6,
        min_samples_leaf=2,
        class_weight="balanced",
        random_state=42,
    )
    modelo.fit(exemplos, alvos)
    return modelo, len(exemplos)


def prever_com_modelo(modelo, parcial1, parcial2, exame, faltas, disciplina_id):
    if modelo is None:
        return None
    features = [construir_features(parcial1, parcial2, exame, faltas, disciplina_id)]
    probabilidades = modelo.predict_proba(features)[0]
    classes = list(modelo.classes_)
    return float(probabilidades[classes.index(1)]) if 1 in classes else 0.0

# ============================================================================
# ALGORITMO DE CÁLCULO DE DESEMPENHO E RECOMENDAÇÃO
# ============================================================================
def analisar_desempenho_e_recomendar(
    notas_obtidas,
    faltas_atuais,
    total_provas=3,
    max_faltas=15,
    media_aprovacao=10.0,
    media_recurso=7.0,
    situacao_financeira=None,
    participacao_atividades=None,
    trabalhos_investigacao=None,
    historico=None,
    probabilidade_aprovacao_ml=None,
):
    provas_realizadas = len(notas_obtidas)
    provas_restantes = max(0, total_provas - provas_realizadas)
    soma_atual = sum(notas_obtidas)
    media_atual = round(soma_atual / provas_realizadas, 2) if provas_realizadas > 0 else 0.0

    percentual_faltas = (faltas_atuais / max_faltas) * 100 if max_faltas > 0 else 0
    risco_faltas = "CRÍTICO" if faltas_atuais >= max_faltas else ("ALTO" if percentual_faltas >= 75 else "BAIXO")

    indicadores_map = {
        "situacao_financeira": {"Regular": 0.0, "Em atraso": 1.5, "Não informado": 0.5, None: 0.0},
        "participacao_atividades": {"Alta": 0.0, "Média": 0.8, "Baixa": 1.8, "Não informado": 0.5, None: 0.0},
        "trabalhos_investigacao": {"Feita": 0.0, "Parcial": 0.9, "Não feita": 1.7, "Não informado": 0.5, None: 0.0},
    }

    penalidade_indicadores = 0.0
    penalidade_indicadores += indicadores_map["situacao_financeira"].get(situacao_financeira, 0.0)
    penalidade_indicadores += indicadores_map["participacao_atividades"].get(participacao_atividades, 0.0)
    penalidade_indicadores += indicadores_map["trabalhos_investigacao"].get(trabalhos_investigacao, 0.0)

    score_risco = 0.0
    if faltas_atuais >= max_faltas:
        score_risco += 3.0
    elif faltas_atuais >= max_faltas * 0.7:
        score_risco += 1.5

    if media_atual < 5.0:
        score_risco += 2.8
    elif media_atual < 7.0:
        score_risco += 2.0
    elif media_atual < 10.0:
        score_risco += 1.2

    if provas_restantes > 0:
        pontos_necessarios = (media_aprovacao * total_provas) - soma_atual
        nota_meta = round(pontos_necessarios / provas_restantes, 2) if provas_restantes > 0 else 0.0
        score_risco += max(0.0, (nota_meta - 8.0) / 8.0)
    else:
        nota_meta = 0.0

    score_risco += penalidade_indicadores

    historico = historico or {}
    historico_disciplina = historico.get("disciplina", {})
    historico_aluno = historico.get("aluno", {})
    taxa_historica = historico_disciplina.get("taxa_aprovacao")
    media_historica = historico_disciplina.get("media")
    amostras_historicas = historico_disciplina.get("amostras", 0)

    # O histórico tem peso progressivo: poucas observações não dominam a previsão.
    confianca_historica = min(0.45, amostras_historicas / 10) if amostras_historicas else 0.0
    if taxa_historica is not None:
        score_risco += (0.5 - taxa_historica) * 3.0 * confianca_historica
    if media_historica is not None:
        score_risco += max(-0.8, min(0.8, (10.0 - media_historica) / 5.0)) * confianca_historica

    if historico_aluno.get("taxa_aprovacao") is not None:
        score_risco += (0.5 - historico_aluno["taxa_aprovacao"]) * 1.5

    if probabilidade_aprovacao_ml is not None:
        if probabilidade_aprovacao_ml < 0.40:
            score_risco += 1.5
        elif probabilidade_aprovacao_ml >= 0.75:
            score_risco -= 0.8

    if score_risco >= 5.5:
        nivel_risco = "ALTO"
    elif score_risco >= 2.8:
        nivel_risco = "MEDIO"
    else:
        nivel_risco = "BAIXO"

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
        if media_atual >= media_aprovacao:
            previsao = "APROVAÇÃO GARANTIDA"
        elif media_atual >= media_recurso:
            previsao = "EM RISCO - APROVAÇÃO POSSÍVEL"
        elif nota_meta > 0:
            previsao = "ENCAMINHADO PARA RECURSO"
        else:
            previsao = "EM RISCO - APROVAÇÃO POSSÍVEL"

    recomendacoes = []
    if risco_faltas == "CRÍTICO":
        recomendacoes.append("⚠️ Limite de faltas atingido!")
    elif risco_faltas == "ALTO":
        recomendacoes.append(f"⚠️ Atenção: consumiu {percentual_faltas:.0f}% das faltas permitidas.")

    if situacao_financeira == "Em atraso":
        recomendacoes.append("💰 Situação financeira em atraso: acompanhar apoio institucional e regularização.")
    if participacao_atividades and str(participacao_atividades).lower() in {"baixa", "média", "media"}:
        recomendacoes.append("🤝 Participação em atividades abaixo do esperado: reforçar envolvimento e acompanhamento.")
    if trabalhos_investigacao and str(trabalhos_investigacao).lower() in {"não feita", "nao feita", "parcial"}:
        recomendacoes.append("📚 Trabalhos de investigação pendentes: priorizar execução e entrega.")

    if provas_restantes > 0 and nota_meta > 0:
        recomendacoes.append(f"🎯 Meta: média de {nota_meta} nas próximas {provas_restantes} prova(s).")

    if taxa_historica is not None and amostras_historicas >= 2:
        recomendacoes.append(
            f"📊 Base histórica da disciplina: {taxa_historica * 100:.0f}% de aprovação em "
            f"{amostras_historicas} registo(s), com média {media_historica:.1f}."
        )
        if taxa_historica < 0.5:
            recomendacoes.append("🔎 Esta disciplina apresenta dificuldade recorrente; priorizar apoio e revisão antecipada.")
        elif taxa_historica >= 0.75 and media_atual >= 10:
            recomendacoes.append("✅ O desempenho atual acompanha um histórico favorável nesta disciplina.")

    taxa_aluno = historico_aluno.get("taxa_aprovacao")
    if taxa_aluno is not None and historico_aluno.get("amostras", 0) >= 3:
        recomendacoes.append(f"📈 Histórico do estudante: {taxa_aluno * 100:.0f}% de aprovação em experiências anteriores.")

    if probabilidade_aprovacao_ml is not None:
        recomendacoes.append(
            f"🤖 Modelo automático estima {probabilidade_aprovacao_ml * 100:.0f}% de probabilidade de aprovação."
        )
        if probabilidade_aprovacao_ml < 0.40:
            recomendacoes.append("🧭 O modelo recomenda intervenção antecipada com base nos padrões aprendidos.")

    return {
        "media_acumulada": media_atual,
        "previsao": previsao,
        "nivel_risco": nivel_risco,
        "nota_meta": max(0.0, nota_meta) if provas_restantes > 0 else None,
        "recomendacoes": json.dumps(recomendacoes, ensure_ascii=False),
        "penalidade_indicadores": round(penalidade_indicadores, 2),
        "score_risco": round(score_risco, 2),
        "taxa_aprovacao_historica": round(taxa_historica, 4) if taxa_historica is not None else None,
        "media_historica": round(media_historica, 2) if media_historica is not None else None,
        "amostras_historicas": amostras_historicas,
        "probabilidade_aprovacao_ml": round(probabilidade_aprovacao_ml, 4) if probabilidade_aprovacao_ml is not None else None,
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
        modelo_ml, amostras_ml = treinar_modelo_historico(cursor)
        print(
            f"🧠 Modelo ML: {'ativo' if modelo_ml else 'fallback'} "
            f"({amostras_ml} exemplos completos)"
        )

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
            situacao_financeira = disc.get("situacao_financeira")
            participacao_atividades = disc.get("participacao_atividades")
            trabalhos_investigacao = disc.get("trabalhos_investigacao")
            historico = obter_contexto_historico(cursor, aluno_id, disciplina_id, ano_letivo)
            probabilidade_aprovacao_ml = prever_com_modelo(
                modelo_ml, p1, p2, exame, faltas, disciplina_id
            )

            # 1. Persistir/Atualizar notas
            cursor.execute("""
                INSERT INTO notas (
                    aluno_id, disciplina_id, parcial1, parcial2, exame, faltas,
                    situacao_financeira, participacao_atividades, trabalhos_investigacao, ano_letivo
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(aluno_id, disciplina_id, ano_letivo) DO UPDATE SET
                    parcial1 = excluded.parcial1,
                    parcial2 = excluded.parcial2,
                    exame = excluded.exame,
                    faltas = excluded.faltas,
                    situacao_financeira = excluded.situacao_financeira,
                    participacao_atividades = excluded.participacao_atividades,
                    trabalhos_investigacao = excluded.trabalhos_investigacao
            """, (aluno_id, disciplina_id, p1, p2, exame, faltas,
                  situacao_financeira, participacao_atividades, trabalhos_investigacao, ano_letivo))

            # 2. Montar lista de notas obtidas para o algoritmo
            notas_obtidas = [n for n in [p1, p2, exame] if n is not None]

            res = analisar_desempenho_e_recomendar(
                notas_obtidas,
                faltas,
                situacao_financeira=situacao_financeira,
                participacao_atividades=participacao_atividades,
                trabalhos_investigacao=trabalhos_investigacao,
                historico=historico,
                probabilidade_aprovacao_ml=probabilidade_aprovacao_ml,
            )
            data_calculo = datetime.now().isoformat()

            media_parcial = round((p1 + p2) / 2, 2) if (p1 is not None and p2 is not None) else None
            media_final = res["media_acumulada"]

            cursor.execute("""
                INSERT INTO previsoes (
                    aluno_id, disciplina_id, ano_letivo, media_parcial, media_final, risco,
                    recomendacao, data_calculo, score_risco, taxa_aprovacao_historica,
                    media_historica, amostras_historicas, probabilidade_aprovacao_ml
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(aluno_id, disciplina_id, ano_letivo) DO UPDATE SET
                    media_parcial = excluded.media_parcial,
                    media_final = excluded.media_final,
                    risco = excluded.risco,
                    recomendacao = excluded.recomendacao,
                    data_calculo = excluded.data_calculo,
                    score_risco = excluded.score_risco,
                    taxa_aprovacao_historica = excluded.taxa_aprovacao_historica,
                    media_historica = excluded.media_historica,
                    amostras_historicas = excluded.amostras_historicas,
                    probabilidade_aprovacao_ml = excluded.probabilidade_aprovacao_ml
            """, (
                aluno_id, disciplina_id, ano_letivo, media_parcial, media_final,
                res["nivel_risco"], res["recomendacoes"], data_calculo,
                res["score_risco"], res["taxa_aprovacao_historica"],
                res["media_historica"], res["amostras_historicas"],
                res["probabilidade_aprovacao_ml"],
            ))

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
            situacao_financeira TEXT,
            participacao_atividades TEXT,
            trabalhos_investigacao TEXT,
            ano_letivo TEXT NOT NULL,
            FOREIGN KEY(aluno_id) REFERENCES users(id),
            FOREIGN KEY(disciplina_id) REFERENCES disciplinas(id),
            UNIQUE(aluno_id, disciplina_id, ano_letivo)
        )
    ''')
    add_column_if_not_exists(conn, "notas", "situacao_financeira TEXT")
    add_column_if_not_exists(conn, "notas", "participacao_atividades TEXT")
    add_column_if_not_exists(conn, "notas", "trabalhos_investigacao TEXT")
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
            score_risco REAL,
            taxa_aprovacao_historica REAL,
            media_historica REAL,
            amostras_historicas INTEGER,
            probabilidade_aprovacao_ml REAL,
            FOREIGN KEY(aluno_id) REFERENCES users(id),
            FOREIGN KEY(disciplina_id) REFERENCES disciplinas(id),
            UNIQUE(aluno_id, disciplina_id, ano_letivo)
        )
    ''')
    add_column_if_not_exists(conn, "previsoes", "score_risco REAL")
    add_column_if_not_exists(conn, "previsoes", "taxa_aprovacao_historica REAL")
    add_column_if_not_exists(conn, "previsoes", "media_historica REAL")
    add_column_if_not_exists(conn, "previsoes", "amostras_historicas INTEGER")
    add_column_if_not_exists(conn, "previsoes", "probabilidade_aprovacao_ml REAL")
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