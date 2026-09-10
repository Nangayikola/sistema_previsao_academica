# dashboard/app.py
import io
import json
import requests
import pandas as pd
import streamlit as st

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import cm

# ---- CONFIGURAÇÃO DA PÁGINA ----
st.set_page_config(
    page_title="Sistema de Previsão Académica",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---- CONFIGURAÇÕES DA API ----
API_BASE = "http://localhost:8000"

# ---- MAPEAMENTO DE CÓDIGOS PARA NOMES DE DISCIPLINAS ----
MAPA_DISCIPLINAS = {
    "25I01": "Sistemas de Informação",
    "25I02": "Engenharia de Requisitos",
    "25I03": "Sistemas Distribuídos",
    "25I04": "Arquitetura de Software",
    "25I05": "Gestão de Projetos de TI",
    "25I06": "Segurança e Auditoria",
    "12II01": "Análise Matemática I",
    "12II02": "Álgebra Linear",
    "12II03": "Programação Orientada a Objetos",
    "12II04": "Bases de Dados",
    "12II05": "Redes de Computadores",
    "12II06": "Engenharia de Software",
    "12II07": "Sistemas Operativos",
    "12II08": "Inteligência Artificial",
    "12II09": "Arquitetura de Computadores",
    "12II10": "Segurança Informática"
}

def obter_nome_disciplina(dados_d):
    """Retorna o nome completo e amigável da disciplina a partir do dicionário ou da API."""
    nome = (
        dados_d.get('disciplina_nome')
        or dados_d.get('disciplina')
        or dados_d.get('nome')
        or dados_d.get('nome_disciplina')
    )
    codigo = str(dados_d.get('codigo') or dados_d.get('disciplina_codigo') or dados_d.get('cod') or "").strip()

    # Normaliza para comparar com o dicionário de mapeamento.
    nome_str = str(nome).strip() if nome is not None else ""
    codigo_str = codigo.upper()

    # Prefere o nome real da disciplina quando a API fornece ambos os campos.
    if nome_str and nome_str not in {codigo_str, codigo}:
        if nome_str.upper() in MAPA_DISCIPLINAS:
            return MAPA_DISCIPLINAS[nome_str.upper()]
        if codigo_str in MAPA_DISCIPLINAS:
            return MAPA_DISCIPLINAS[codigo_str]
        return nome_str

    # Se só existir código, tenta converter para nome amigável.
    if codigo_str in MAPA_DISCIPLINAS:
        return MAPA_DISCIPLINAS[codigo_str]

    return nome_str if nome_str else (codigo if codigo else "Disciplina")


def normalizar_semestre(valor):
    if valor is None:
        return "I"
    texto = str(valor).strip().upper().replace(" SEMESTRE", "")
    return "I" if texto in {"I", "1"} else "II" if texto in {"II", "2"} else "I"

# ---- INJEÇÃO DE CSS GLASSMORPHISM ----
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');
    
    * { 
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif; 
        box-sizing: border-box; 
    }

    .stApp {
        background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 50%, #cbd5e1 100%);
        min-height: 100vh;
    }

    .header {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        border: 1px solid rgba(255, 255, 255, 0.15);
        padding: 1.2rem 2.2rem;
        border-radius: 20px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.25);
        display: flex;
        align-items: center;
        justify-content: space-between;
        flex-wrap: wrap;
    }

    .header-left .icon {
        font-size: 2.2rem;
        background: linear-gradient(135deg, #34d399, #10b981);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .header-left h1 {
        font-size: 1.5rem; 
        font-weight: 800; 
        margin: 0;
        letter-spacing: -0.02em;
        background: linear-gradient(135deg, #ffffff 40%, #cbd5e1);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .user-badge {
        background: #ffffff;
        color: #0f172a;
        border-radius: 30px;
        padding: 0.5rem 1.4rem; 
        display: flex; 
        align-items: center; 
        gap: 0.6rem;
        border: 2px solid #10b981;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        font-weight: 700;
        font-size: 0.95rem;
    }

    .card-glass {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(20px);
        border: 1px solid #cbd5e1;
        border-radius: 20px;
        padding: 1.8rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 8px 20px -4px rgba(15, 23, 42, 0.08);
    }

    .auth-card {
        background: rgba(255, 255, 255, 0.96);
        backdrop-filter: blur(24px);
        border: 1.5px solid #cbd5e1;
        border-radius: 24px;
        padding: 2.5rem 2.2rem;
        box-shadow: 0 25px 50px -12px rgba(15, 23, 42, 0.25);
        margin: 0 auto;
    }

    .auth-header {
        text-align: center;
        margin-bottom: 1.8rem;
    }
    
    .auth-header h2 {
        color: #0f172a;
        font-weight: 800;
        font-size: 1.85rem;
        margin-bottom: 0.3rem;
    }

    .section-title {
        font-size: 1.35rem; 
        font-weight: 800; 
        color: #0f172a;
        margin-bottom: 1.2rem; 
    }

    .risco-alto { background: #fef2f2; color: #991b1b; border: 1px solid #fecaca; padding: 0.2rem 0.6rem; border-radius: 9999px; font-weight: 700; }
    .risco-medio { background: #fffbebfb; color: #92400e; border: 1px solid #fef08a; padding: 0.2rem 0.6rem; border-radius: 9999px; font-weight: 700; }
    .risco-baixo { background: #f0fdf4; color: #166534; border: 1px solid #bbf7d0; padding: 0.2rem 0.6rem; border-radius: 9999px; font-weight: 700; }
</style>
""", unsafe_allow_html=True)

# ---- MOTOR DE CÁLCULO PREDITIVO DE DESEMPENHO ----
def processar_dados_disciplina(d):
    nome_disciplina = obter_nome_disciplina(d)
    p1 = float(d.get('parcial1', d.get('p1', 0.0)) or 0.0)
    p2 = float(d.get('parcial2', d.get('p2', 0.0)) or 0.0)
    exame = float(d.get('exame', 0.0) or 0.0)
    faltas = int(d.get('faltas', 0) or 0)
    situacao_financeira = d.get('situacao_financeira') or 'Não informado'
    participacao_atividades = d.get('participacao_atividades') or 'Não informado'
    trabalhos_investigacao = d.get('trabalhos_investigacao') or 'Não informado'
    
    if d.get('media_final') not in [None, '-']:
        media = float(d['media_final'])
    elif d.get('nota') not in [None, '-']:
        media = float(d['nota'])
    else:
        if exame > 0:
            media = round(((p1 + p2) / 2) * 0.4 + (exame * 0.6), 1)
        else:
            media = round((p1 + p2) / 2 if (p1 > 0 or p2 > 0) else 0.0, 1)

    risco = d.get('risco')
    if not risco or risco == 'N/A':
        if media < 10.0 or faltas >= 5:
            risco = 'ALTO'
        elif 10.0 <= media < 12.0 or faltas in [3, 4]:
            risco = 'MÉDIO'
        else:
            risco = 'BAIXO'
    else:
        risco = str(risco).upper()

    rec = d.get('recomendacao')
    if isinstance(rec, str):
        try:
            rec = " ".join(json.loads(rec))
        except (json.JSONDecodeError, TypeError):
            pass
    if not rec or rec == 'Sem recomendação':
        if risco == 'ALTO':
            if faltas >= 5:
                rec = f"Risco Alto de Reprovação por Faltas ({faltas} faltas). Necessário reforço urgente e comparência às aulas."
            else:
                rec = f"Risco Alto de Reprovação. Média atual de {media:.1f} valores. Obter nota elevada nos próximos exames/recurso."
        elif risco == 'MÉDIO':
            rec = f"Risco Médio de Reprovação. Média de {media:.1f} valores. Recomenda-se acompanhamento nas tutorias."
        else:
            rec = f"Risco Baixo de Reprovação. Média atual de {media:.1f} valores. Mantenha o bom ritmo de estudo."

    d_proc = d.copy()
    d_proc['disciplina_nome'] = nome_disciplina
    d_proc['p1'] = p1
    d_proc['p2'] = p2
    d_proc['exame'] = exame
    d_proc['faltas'] = faltas
    d_proc['situacao_financeira'] = situacao_financeira
    d_proc['participacao_atividades'] = participacao_atividades
    d_proc['trabalhos_investigacao'] = trabalhos_investigacao
    d_proc['media_final'] = media
    d_proc['risco'] = risco
    d_proc['recomendacao'] = rec
    d_proc['score_risco'] = d.get('score_risco')
    d_proc['taxa_aprovacao_historica'] = d.get('taxa_aprovacao_historica')
    d_proc['media_historica'] = d.get('media_historica')
    d_proc['amostras_historicas'] = int(d.get('amostras_historicas') or 0)
    d_proc['probabilidade_aprovacao_ml'] = d.get('probabilidade_aprovacao_ml')
    return d_proc

def processar_resumo_semestre(disciplinas):
    if not disciplinas:
        return {'media_global': 0.0, 'total_faltas': 0, 'disciplinas_em_risco': 0, 'risco_global': 'BAIXO', 'recomendacao_geral': 'Sem dados.'}

    total_media = sum(float(d['media_final']) for d in disciplinas)
    media_global = round(total_media / len(disciplinas), 1)
    total_faltas = sum(int(d['faltas']) for d in disciplinas)
    em_risco = sum(1 for d in disciplinas if d['risco'] in ['ALTO', 'MÉDIO'])

    if em_risco >= 2 or media_global < 10.0:
        risco_global = 'ALTO'
        rec_geral = f"Atenção: Existem {em_risco} disciplinas em risco e média global de {media_global}. Recomenda-se um plano de estudo intensivo."
    elif em_risco == 1 or 10.0 <= media_global < 12.0:
        risco_global = 'MÉDIO'
        rec_geral = f"Desempenho moderado com média de {media_global}. Foque na disciplina com maior fragilidade."
    else:
        risco_global = 'BAIXO'
        rec_geral = f"Risco Global Baixo. Média global satisfatória de {media_global}. Continue com o bom trabalho!"

    return {
        'media_global': media_global,
        'total_faltas': total_faltas,
        'disciplinas_em_risco': em_risco,
        'risco_global': risco_global,
        'recomendacao_geral': rec_geral
    }

# ---- CLIENTE HTTP E AUTENTICAÇÃO ----
def get_http_session():
    session = requests.Session()
    if "token" in st.session_state:
        session.headers.update({"Authorization": f"Bearer {st.session_state.token}"})
    return session

def login(username, password):
    try:
        resp = requests.post(f"{API_BASE}/auth/login", json={"username": username, "password": password}, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            st.session_state.token = data["access_token"]
            st.session_state.role = data["role"]
            st.session_state.nome = data["nome"]
            st.session_state.username = username
            st.session_state.aluno_id = data.get("id")
            return True
        st.error("❌ Credenciais inválidas.")
        return False
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Erro de conexão com a API: {e}")
        return False

def register(username, password, role, nome, email="", curso_id=None, ano_curso=None, semestre=None, ano_letivo=None):
    try:
        payload = {
            "username": username,
            "password": password,
            "role": role,
            "nome": nome,
            "email": email,
            "curso_id": curso_id,
            "ano_curso": ano_curso,
            "semestre": semestre,
            "ano_letivo": ano_letivo,
        }
        resp = requests.post(f"{API_BASE}/auth/register", json=payload, timeout=10)
        if resp.status_code in (200, 201):
            st.success("✅ Conta criada com sucesso!")
            return True
        st.error(f"❌ Erro no registo: {resp.text}")
        return False
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Erro de conexão com a API: {e}")
        return False

def logout():
    for key in ["token", "role", "nome", "username", "aluno_id"]:
        st.session_state.pop(key, None)
    st.rerun()

# ---- GERADOR DE PDF ----
def gerar_pdf_boletim(aluno_nome, ano_letivo, semestre, disciplinas, resumo):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=1.2*cm, leftMargin=1.2*cm, topMargin=1.5*cm, bottomMargin=1.5*cm)
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('DocTitle', parent=styles['Heading1'], fontSize=16, leading=20, textColor=colors.HexColor('#0f172a'), fontName='Helvetica-Bold')
    subtitle_style = ParagraphStyle('DocSubtitle', parent=styles['Normal'], fontSize=9, leading=13, textColor=colors.HexColor('#64748b'))
    section_heading = ParagraphStyle('SecHeading', parent=styles['Heading2'], fontSize=11, leading=15, textColor=colors.HexColor('#0f172a'), spaceBefore=8, spaceAfter=4, fontName='Helvetica-Bold')
    cell_style = ParagraphStyle('Cell', parent=styles['Normal'], fontSize=8, leading=11, fontName='Helvetica')
    cell_bold = ParagraphStyle('CellBold', parent=cell_style, fontName='Helvetica-Bold')

    elements = [
        Paragraph("Boletim Académico & Relatório Preditivo", title_style),
        Paragraph(f"<b>Estudante:</b> {aluno_nome} | <b>Ano / Semestre:</b> {ano_letivo} - {semestre}", subtitle_style),
        Spacer(1, 0.3*cm),
        HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#0f172a'), spaceAfter=10)
    ]

    headers = ["Disciplina", "P1", "P2", "Exame", "Faltas", "Média", "Risco"]
    table_data = [[Paragraph(f"<b>{h}</b>", ParagraphStyle('H', parent=cell_bold, textColor=colors.whitesmoke)) for h in headers]]

    for d in disciplinas:
        disc_nome = d.get('disciplina_nome') or obter_nome_disciplina(d) or 'Disciplina'
        table_data.append([
            Paragraph(disc_nome, cell_bold),
            Paragraph(str(d['p1']), cell_style),
            Paragraph(str(d['p2']), cell_style),
            Paragraph(str(d['exame']), cell_style),
            Paragraph(str(d['faltas']), cell_style),
            Paragraph(str(d['media_final']), cell_bold),
            Paragraph(str(d['risco']), cell_bold)
        ])

    t_disc = Table(table_data, colWidths=[6.0*cm, 1.7*cm, 1.7*cm, 1.7*cm, 1.7*cm, 2.2*cm, 2.2*cm], repeatRows=1)
    t_disc.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0f172a')),
        ('ALIGN', (1,0), (-1,-1), 'CENTER'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    elements.append(t_disc)
    elements.append(Spacer(1, 0.4*cm))

    elements.append(Paragraph("Diagnóstico Preditivo e Recomendações", section_heading))
    for d in disciplinas:
        disc_nome = d.get('disciplina_nome') or obter_nome_disciplina(d) or 'Disciplina'
        elements.append(Paragraph(f"• <b>{disc_nome}:</b> {d['recomendacao']}", cell_style))

    doc.build(elements)
    buffer.seek(0)
    return buffer

# ---- COMPONENTES DE INTERFACE ----
def fetch_api_data(endpoint):
    session = requests.Session()
    if "token" in st.session_state:
        session.headers.update({"Authorization": f"Bearer {st.session_state.token}"})
    try:
        resp = session.get(f"{API_BASE}/{endpoint}", timeout=5)
        return resp.json() if resp.status_code == 200 else []
    except Exception:
        return []


def render_header():
    st.markdown("""
    <div class="header">
        <div class="header-left" style="display:flex; align-items:center; gap:1rem;">
            <span class="icon">🎓</span>
            <div>
                <h1>Sistema de Previsão Académica</h1>
                <p style="margin:0; font-size:0.85rem; color:#cbd5e1;">Portal Académico & Diagnóstico Preditivo</p>
            </div>
        </div>
    """, unsafe_allow_html=True)
    if "token" in st.session_state:
        st.markdown(f'''
        <div class="user-badge">
            <span>👤</span>
            <span>{st.session_state.nome} <span style="color:#64748b; font-weight:500;">({st.session_state.role.capitalize()})</span></span>
        </div>
        ''', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

def render_auth_page():
    _, col_center, _ = st.columns([1, 2, 1])
    with col_center:
        st.markdown("""
        <div class="auth-card">
            <div class="auth-header">
                <h2>Acesso ao Portal</h2>
                <p>Introduza as suas credenciais para continuar</p>
            </div>
        """, unsafe_allow_html=True)
        tab_login, tab_register = st.tabs(["🔐 Entrar", "📝 Criar Conta"])
        
        with tab_login:
            st.write("")
            with st.form("form_login"):
                username = st.text_input("Username / Matrícula")
                password = st.text_input("Palavra-passe", type="password")
                if st.form_submit_button("🚀 Entrar", use_container_width=True):
                    if username and password and login(username, password):
                        st.rerun()

        with tab_register:
            st.write("")
            with st.form("form_register"):
                reg_nome = st.text_input("Nome Completo")
                reg_username = st.text_input("Username / Matrícula")
                reg_email = st.text_input("Email")
                reg_role = st.selectbox("Perfil", options=["estudante", "professor"])
                reg_password = st.text_input("Palavra-passe", type="password")

                cursos = fetch_api_data("cursos")
                if reg_role == "estudante":
                    curso_opts = {f"{c['nome']}": c['id'] for c in cursos}
                    selected_curso_display = st.selectbox("Curso", options=list(curso_opts.keys()) or ["Selecionar curso"], index=0)
                    reg_curso_id = curso_opts.get(selected_curso_display)
                    anos = fetch_api_data(f"anos_curso/{reg_curso_id}") if reg_curso_id else []
                    ano_values = [a['numero'] for a in anos] if anos else [1, 2, 3, 4]
                    reg_ano_curso = st.selectbox("Ano", options=ano_values, index=0)
                    reg_semestre = st.selectbox("Semestre", options=["I", "II"], index=0)
                    reg_ano_letivo = st.text_input("Ano Letivo", value="2025-2026")
                else:
                    reg_curso_id = None
                    reg_ano_curso = None
                    reg_semestre = None
                    reg_ano_letivo = None

                if st.form_submit_button("✨ Registar", use_container_width=True):
                    register(
                        reg_username,
                        reg_password,
                        reg_role,
                        reg_nome,
                        reg_email,
                        reg_curso_id,
                        reg_ano_curso,
                        reg_semestre,
                        reg_ano_letivo,
                    )
        st.markdown('</div>', unsafe_allow_html=True)

# ---- DASHBOARD PRINCIPAL ----
def render_dashboard():
    http = get_http_session()

    # NAVEGAÇÃO DE ACORDO COM O PERFIL (ROLE)
    with st.sidebar:
        st.markdown("### 🧭 Navegação")
        if st.session_state.role == "professor":
            menu = st.radio(
                "Menu Professor",
                ["📝 Registar Semestre", "📋 Listar Alunos", "📊 Consultar Boletim & Previsão"],
                label_visibility="collapsed"
            )
        else:
            menu = st.radio(
                "Menu Estudante",
                ["📊 Meu Boletim & Previsão"],
                label_visibility="collapsed"
            )
        st.write("---")
        if st.button("🚪 Encerrar Sessão", use_container_width=True):
            logout()

    # AUXILIAR PARA CONSULTAR API COM CACHE
    @st.cache_data(ttl=30)
    def fetch_api_data_cached(endpoint):
        return fetch_api_data(endpoint)

    # -------------------------------------------------------------
    # 1. PERFIL PROFESSOR: REGISTAR SEMESTRE E NOTAS
    # -------------------------------------------------------------
    if menu == "📝 Registar Semestre":
        st.markdown('<div class="section-title">📝 Registar Semestre e Notas</div>', unsafe_allow_html=True)

        cursos = fetch_api_data_cached("cursos")
        alunos = fetch_api_data_cached("alunos")

        st.markdown('<div class="card-glass">', unsafe_allow_html=True)
        col_aluno, col_curso = st.columns(2)
        
        with col_aluno:
            if alunos:
                aluno_opts = {f"{a['nome']} ({a['username']})": a for a in alunos}
                aluno_sel_name = st.selectbox("Aluno", options=list(aluno_opts.keys()), index=0)
                aluno_obj = aluno_opts.get(aluno_sel_name, {})
                matricula_aluno = aluno_obj.get('username') or ""
            else:
                matricula_aluno = st.text_input("Matrícula/Username do Aluno", value="aluno1")
                aluno_obj = {}

        disciplinas_plano = []
        ano_num = 1
        semestre = "I"
        curso_id = None
        aluno_ano_letivo = "2025-2026"

        if aluno_obj:
            curso_id = aluno_obj.get('curso_id')
            ano_num = aluno_obj.get('ano_curso') or 1
            semestre = aluno_obj.get('semestre') or "I"
            aluno_ano_letivo = aluno_obj.get('ano_letivo') or "2025-2026"

        if aluno_obj and (aluno_obj.get('curso_id') is None or aluno_obj.get('ano_curso') is None or not aluno_obj.get('semestre') or not aluno_obj.get('ano_letivo')):
            st.warning("Este aluno ainda não tem curso, ano, semestre e ano académico registados. Refaça o registo do estudante com esses dados.")

        st.markdown("### Dados do aluno carregados")
        curso_nome = ""
        if cursos and curso_id is not None:
            curso_nome = next((c.get('nome', '') for c in cursos if c.get('id') == curso_id), "")

        resumo_cols = st.columns(4)
        with resumo_cols[0]:
            st.text_input("Curso", value=curso_nome, disabled=True, key="curso_auto_prof")
        with resumo_cols[1]:
            ano_display = str(aluno_obj.get('ano_curso')) if aluno_obj and aluno_obj.get('ano_curso') is not None else str(ano_num)
            st.text_input("Ano", value=ano_display, disabled=True, key="ano_auto_prof")
        with resumo_cols[2]:
            semestre_display = str(aluno_obj.get('semestre') or semestre)
            st.text_input("Semestre", value=semestre_display, disabled=True, key="semestre_auto_prof")
        with resumo_cols[3]:
            ano_letivo_display = str(aluno_obj.get('ano_letivo') or aluno_ano_letivo)
            st.text_input("Ano Académico", value=ano_letivo_display, disabled=True, key="ano_letivo_auto_prof")

        if cursos and curso_id is not None:
            disciplinas_plano = fetch_api_data_cached(f"disciplinas_plano/{curso_id}/{ano_num}/{semestre}")
        ano_letivo = ano_letivo_display

        st.markdown("---")

        with st.form("form_insercao_notas"):
            st.markdown("#### 📚 Lançamento de Notas e Faltas")
            disciplinas_payload = []
            total_cards = len(disciplinas_plano) if disciplinas_plano else 5

            st.markdown("#### Indicadores Complementares do Semestre")
            ind_cols = st.columns(3)
            with ind_cols[0]:
                situacao_financeira = st.selectbox(
                    "Situação Financeira",
                    options=["Regular", "Em atraso", "Não informado"],
                    index=0,
                    key="fin_semestre",
                )
            with ind_cols[1]:
                participacao_atividades = st.selectbox(
                    "Participação nas atividades",
                    options=["Alta", "Média", "Baixa", "Não informado"],
                    index=1,
                    key="part_semestre",
                )
            with ind_cols[2]:
                trabalhos_investigacao = st.selectbox(
                    "Trabalhos de investigação",
                    options=["Feita", "Não feita", "Parcial", "Não informado"],
                    index=0,
                    key="trab_semestre",
                )

            st.markdown("---")

            for i in range(total_cards):
                if disciplinas_plano and i < len(disciplinas_plano):
                    disc_info = disciplinas_plano[i]
                    nome_disciplina = disc_info.get('nome', f'Disciplina {i+1}')
                    codigo_disciplina = disc_info.get('codigo', f'DISC_{i+1}')
                else:
                    nome_disciplina = f"Disciplina {i+1}"
                    codigo_disciplina = f"DISC_{i+1}"

                with st.container():
                    st.markdown(f"### 📘 {nome_disciplina} ({codigo_disciplina})")
                    if not disciplinas_plano:
                        codigo_disciplina = st.text_input(f"Código ({i+1})", value=f"DISC_{i+1}", key=f"cod_{i}")

                    st.markdown("#### Notas")
                    col1, col2, col3, col4 = st.columns(4)
                    with col1: p1 = st.number_input("Iª Parcial", 0.0, 20.0, value=10.0, step=0.5, key=f"p1_in_{i}")
                    with col2: p2 = st.number_input("IIª Parcial", 0.0, 20.0, value=10.0, step=0.5, key=f"p2_in_{i}")
                    with col3: exame = st.number_input("Exame", 0.0, 20.0, value=10.0, step=0.5, key=f"ex_in_{i}")
                    with col4: faltas = st.number_input("Faltas", 0, 100, value=2, step=1, key=f"f_in_{i}")

                    st.markdown("---")
                    disciplinas_payload.append({
                        "disciplina_codigo": codigo_disciplina,
                        "parcial1": p1,
                        "parcial2": p2,
                        "exame": exame,
                        "faltas": faltas,
                        "situacao_financeira": situacao_financeira,
                        "participacao_atividades": participacao_atividades,
                        "trabalhos_investigacao": trabalhos_investigacao,
                    })

            submitted = st.form_submit_button("🚀 Enviar Notas para Previsão", use_container_width=True)
            
            if submitted:
                payload = {
                    "matricula": matricula_aluno,
                    "ano_letivo": ano_letivo,
                    "semestre": semestre,
                    "disciplinas": disciplinas_payload
                }
                try:
                    resp = http.post(f"{API_BASE}/aluno/semestre", json=payload, timeout=10)
                    if resp.status_code in (200, 201, 202):
                        st.success("✅ Notas registradas e enviadas para o sistema com sucesso!")
                    else:
                        st.error(f"❌ Erro na requisição ({resp.status_code}): {resp.text}")
                except Exception as e:
                    st.error(f"❌ Erro de conexão com a API: {e}")

        st.markdown('</div>', unsafe_allow_html=True)

    # -------------------------------------------------------------
    # 2. PERFIL PROFESSOR: LISTAR ALUNOS REGISTADOS
    # -------------------------------------------------------------
    elif menu == "📋 Listar Alunos":
        st.markdown('<div class="section-title">📋 Lista de Alunos Registados</div>', unsafe_allow_html=True)
        try:
            resp = http.get(f"{API_BASE}/alunos", timeout=10)
            if resp.status_code == 200:
                alunos_data = resp.json()
                if alunos_data:
                    df_alunos = pd.DataFrame(alunos_data)
                    st.dataframe(df_alunos, use_container_width=True)
                else:
                    st.info("Nenhum aluno cadastrado.")
            else:
                st.error(f"Erro ao buscar alunos: {resp.text}")
        except Exception as e:
            st.error(f"Erro de conexão: {e}")

    # -------------------------------------------------------------
    # 3. BOLETIM & PREVISÃO (ESTUDANTE E PROFESSOR)
    # -------------------------------------------------------------
    elif menu in ["📊 Meu Boletim & Previsão", "📊 Consultar Boletim & Previsão"]:
        st.markdown('<div class="section-title">📜 Boletim Escolar e Diagnóstico Preditivo</div>', unsafe_allow_html=True)
        
        c1, c2, c3 = st.columns([2, 1, 1])
        with c1:
            target_user = st.session_state.username if st.session_state.role != "professor" else st.text_input("Matrícula do Aluno", value="Isabel")
        with c2:
            ano_letivo = st.text_input("Ano Letivo", value="2025-2026")
        with c3:
            semestre = normalizar_semestre(st.selectbox("Semestre", ["I", "II"], index=0, help="Filtra as disciplinas do semestre selecionado."))

        try:
            url = f"{API_BASE}/aluno/boletim/{ano_letivo}/{semestre}"
            params = {"matricula": target_user} if st.session_state.role == "professor" else {}
            resp = http.get(url, params=params, timeout=10)

            if resp.status_code == 200:
                dados = resp.json()
                raw_disciplinas = dados.get("disciplinas", [])
                raw_disciplinas = [
                    d for d in raw_disciplinas
                    if normalizar_semestre(d.get("semestre") or d.get("semestre_nome") or semestre) == semestre
                ]
                disciplinas_proc = [processar_dados_disciplina(d) for d in raw_disciplinas]
                resumo_real = processar_resumo_semestre(disciplinas_proc)
                disciplinas_com_historico = sum(
                    1 for d in disciplinas_proc if d.get('amostras_historicas', 0) > 0
                )

                st.caption(f"Mostrando disciplinas do {semestre}º semestre para {target_user}.")
                if disciplinas_proc and disciplinas_com_historico == 0:
                    st.info(
                        "Ainda não há histórico comparável para estas disciplinas. "
                        "A previsão atual usa as notas e indicadores do semestre; "
                        "o componente histórico será ativado após existirem registos anteriores."
                    )
                if not disciplinas_proc:
                    st.info(f"Não existem disciplinas registadas para o {semestre}º semestre neste ano letivo.")

                # --- TABELA DE NOTAS ---
                st.markdown('<div class="card-glass">', unsafe_allow_html=True)
                st.markdown("#### 📄 Notas Lançadas no Boletim")
                
                # Garante a exibição estrita do NOME da disciplina na coluna
                df_boletim = pd.DataFrame([
                    {
                        "Disciplina": d.get('disciplina_nome') or d.get('nome') or d.get('disciplina') or "Disciplina Sem Nome",
                        "P1": f"{d['p1']:.1f}",
                        "P2": f"{d['p2']:.1f}",
                        "Exame": f"{d['exame']:.1f}" if d['exame'] > 0 else "-",
                        "Faltas": d['faltas'],
                        "Situação Financeira": d.get('situacao_financeira', 'Não informado'),
                        "Participação": d.get('participacao_atividades', 'Não informado'),
                        "Trabalhos": d.get('trabalhos_investigacao', 'Não informado'),
                        "Média Final": f"{d['media_final']:.1f}",
                        "Histórico": (
                            f"{d['taxa_aprovacao_historica'] * 100:.0f}% aprovação / "
                            f"média {d['media_historica']:.1f} ({d['amostras_historicas']} reg.)"
                            if d.get('taxa_aprovacao_historica') is not None and d.get('media_historica') is not None
                            else "Sem histórico"
                        ),
                        "Probabilidade ML": (
                            f"{d['probabilidade_aprovacao_ml'] * 100:.0f}%"
                            if d.get('probabilidade_aprovacao_ml') is not None else "Fallback"
                        ),
                        "Estado / Risco": d['risco']
                    } for d in disciplinas_proc
                ])

                st.dataframe(
                    df_boletim,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Disciplina": st.column_config.TextColumn("Disciplina", width="large"),
                        "P1": st.column_config.TextColumn("P1", width="small"),
                        "P2": st.column_config.TextColumn("P2", width="small"),
                        "Exame": st.column_config.TextColumn("Exame", width="small"),
                        "Faltas": st.column_config.NumberColumn("Faltas", width="small"),
                        "Situação Financeira": st.column_config.TextColumn("Situação Financeira", width="small"),
                        "Participação": st.column_config.TextColumn("Participação", width="small"),
                        "Trabalhos": st.column_config.TextColumn("Trabalhos", width="small"),
                        "Média Final": st.column_config.TextColumn("Média Final", width="small"),
                        "Histórico": st.column_config.TextColumn("Histórico", width="medium"),
                        "Probabilidade ML": st.column_config.TextColumn("Probabilidade ML", width="small"),
                        "Estado / Risco": st.column_config.TextColumn("Estado / Risco", width="medium"),
                    }
                )

                col_m1, col_m2, col_m3 = st.columns(3)
                col_m1.metric("Média Global Atual", f"{resumo_real['media_global']} val")
                col_m2.metric("Total de Faltas", resumo_real['total_faltas'])
                col_m3.metric("Disciplinas em Risco", resumo_real['disciplinas_em_risco'])
                st.markdown('</div>', unsafe_allow_html=True)

                # --- PREVISÃO ACADÉMICA ---
                st.markdown('<div class="card-glass">', unsafe_allow_html=True)
                st.markdown(f"#### 🤖 Previsão Académica com Dados Existentes")
                st.markdown(f"**Risco Global Calculado:** <span class='risco-{resumo_real['risco_global'].lower()}'>{resumo_real['risco_global']}</span>", unsafe_allow_html=True)
                
                if resumo_real.get('recomendacao_geral'):
                    st.info(f"💡 **Diagnóstico Geral:** {resumo_real['recomendacao_geral']}")

                st.markdown("##### 📌 Recomendações Individuais por Disciplina:")
                for d in disciplinas_proc:
                    st.write(f"- **{d['disciplina_nome']}:** {d['recomendacao']}")
                st.markdown('</div>', unsafe_allow_html=True)

                # --- SIMULAÇÃO INTERATIVA ---
                with st.expander("🔮 Simular Notas / Testar Novos Cenários", expanded=False):
                    st.write("Ajuste as notas abaixo para ver como possíveis classificações futuras alteram a média e a previsão de risco:")
                    
                    simulacoes = []
                    for i, d in enumerate(disciplinas_proc):
                        st.markdown(f"**📖 {d['disciplina_nome']}**")
                        col_s1, col_s2, col_s3, col_s4 = st.columns(4)
                        sim_p1 = col_s1.number_input(f"P1", min_value=0.0, max_value=20.0, value=float(d['p1']), step=0.5, key=f"p1_sim_{i}")
                        sim_p2 = col_s2.number_input(f"P2", min_value=0.0, max_value=20.0, value=float(d['p2']), step=0.5, key=f"p2_sim_{i}")
                        sim_ex = col_s3.number_input(f"Exame", min_value=0.0, max_value=20.0, value=float(d['exame']), step=0.5, key=f"ex_sim_{i}")
                        sim_ft = col_s4.number_input(f"Faltas", min_value=0, max_value=30, value=int(d['faltas']), key=f"ft_sim_{i}")
                        
                        d_sim = d.copy()
                        d_sim['p1'] = sim_p1
                        d_sim['p2'] = sim_p2
                        d_sim['exame'] = sim_ex
                        d_sim['faltas'] = sim_ft
                        d_sim['media_final'] = round(((sim_p1 + sim_p2)/2)*0.4 + (sim_ex*0.6), 1) if sim_ex > 0 else round((sim_p1+sim_p2)/2, 1)
                        simulacoes.append(processar_dados_disciplina(d_sim))

                    resumo_sim = processar_resumo_semestre(simulacoes)
                    st.success(f"🎯 **Média Global Simulada:** {resumo_sim['media_global']} valores | **Risco Global Previsto:** {resumo_sim['risco_global']}")
                    st.info(f"💡 **Diagnóstico Simulado:** {resumo_sim['recomendacao_geral']}")

                # --- DOWNLOAD DO PDF ---
                pdf_bytes = gerar_pdf_boletim(target_user, ano_letivo, semestre, disciplinas_proc, resumo_real)
                st.download_button(
                    label="📥 Baixar Boletim e Previsão Completa (PDF)",
                    data=pdf_bytes,
                    file_name=f"boletim_previsao_{target_user}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            else:
                st.warning("⚠️ Nenhum boletim localizado para os dados informados.")
        except Exception as e:
            st.error(f"❌ Não foi possível realizar a consulta: {e}")

def main():
    render_header()
    if "token" not in st.session_state:
        render_auth_page()
    else:
        render_dashboard()

if __name__ == "__main__":
    main()