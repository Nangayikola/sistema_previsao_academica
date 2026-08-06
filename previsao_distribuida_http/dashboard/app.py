import streamlit as st
import requests
import pandas as pd

# ---- CONFIGURAÇÃO DA PÁGINA ----
st.set_page_config(
    page_title="Previsão Académica",
    page_icon="📘",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---- CSS PERSONALIZADO ----
st.markdown("""
<style>
    /* Reset e tipografia */
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }
    .main {
        background: #f4f7fc;
    }
    /* Cabeçalho */
    .header {
        background: linear-gradient(135deg, #0b1a33 0%, #1d3b66 50%, #2a5298 100%);
        padding: 1.5rem 2rem;
        border-radius: 16px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 8px 30px rgba(26, 67, 113, 0.25);
        display: flex;
        align-items: center;
        justify-content: space-between;
        flex-wrap: wrap;
        gap: 1rem;
    }
    .header-left {
        display: flex;
        align-items: center;
        gap: 1rem;
    }
    .header-left .icon {
        font-size: 2.8rem;
    }
    .header-left .title-group h1 {
        font-size: 2.2rem;
        font-weight: 600;
        margin: 0;
        letter-spacing: -0.5px;
    }
    .header-left .title-group p {
        font-size: 1rem;
        opacity: 0.85;
        margin: 0;
    }
    .badge {
        background: rgba(255,255,255,0.15);
        padding: 0.3rem 1.2rem;
        border-radius: 30px;
        font-size: 0.8rem;
        font-weight: 500;
        backdrop-filter: blur(4px);
        border: 1px solid rgba(255,255,255,0.1);
        white-space: nowrap;
    }
    /* Cards */
    .card {
        background: white;
        border-radius: 14px;
        padding: 1.6rem 1.8rem;
        margin-bottom: 1.8rem;
        box-shadow: 0 4px 20px rgba(0,20,40,0.06);
        border: 1px solid rgba(0,0,0,0.03);
    }
    .section-title {
        font-size: 1.5rem;
        font-weight: 600;
        color: #0b1a33;
        border-bottom: 3px solid #2a5298;
        padding-bottom: 0.5rem;
        display: inline-block;
        margin-bottom: 1.2rem;
    }
    /* Etiquetas de risco */
    .risco-alto {
        background: linear-gradient(135deg, #fce4e4, #f8d0d0);
        color: #a13024;
        font-weight: 600;
        padding: 0.3rem 1.2rem;
        border-radius: 30px;
        border: 1px solid #f0baba;
    }
    .risco-medio {
        background: linear-gradient(135deg, #fff3e0, #ffe4c4);
        color: #b45f2a;
        font-weight: 600;
        padding: 0.3rem 1.2rem;
        border-radius: 30px;
        border: 1px solid #f5d5a0;
    }
    .risco-baixo {
        background: linear-gradient(135deg, #e3f5e9, #c8e6d9);
        color: #1f6e3b;
        font-weight: 600;
        padding: 0.3rem 1.2rem;
        border-radius: 30px;
        border: 1px solid #9ed5b5;
    }
    /* Botões */
    .stButton>button {
        background: linear-gradient(135deg, #1d3b66, #2a5298);
        color: white;
        border-radius: 30px;
        padding: 0.6rem 2.2rem;
        font-weight: 500;
        border: none;
        transition: all 0.25s ease;
        box-shadow: 0 4px 12px rgba(42,82,152,0.25);
    }
    .stButton>button:hover {
        transform: scale(1.02);
        box-shadow: 0 6px 20px rgba(42,82,152,0.35);
    }
    /* Rodapé */
    .footer {
        margin-top: 3rem;
        text-align: center;
        color: #a0b0c4;
        font-size: 0.85rem;
        border-top: 1px solid #eef2f7;
        padding-top: 1.8rem;
    }
    /* Tela de login (centralizada) */
    .login-container {
        display: flex;
        justify-content: center;
        align-items: center;
        min-height: 70vh;
    }
    .login-box {
        background: white;
        border-radius: 20px;
        padding: 2.5rem 3rem;
        box-shadow: 0 10px 40px rgba(0,0,0,0.08);
        max-width: 450px;
        width: 100%;
        border: 1px solid #eef2f7;
    }
    .login-box h2 {
        color: #0b1a33;
        font-weight: 600;
        margin-top: 0;
        text-align: center;
    }
    .login-box .subtitle {
        text-align: center;
        color: #6c7a8a;
        margin-bottom: 1.5rem;
    }
</style>
""", unsafe_allow_html=True)

API_BASE = "http://localhost:8000"

# ---- FUNÇÕES DE AUTENTICAÇÃO ----
def login(username, password):
    try:
        resp = requests.post(f"{API_BASE}/auth/login", json={"username": username, "password": password})
        if resp.status_code == 200:
            data = resp.json()
            st.session_state.token = data["access_token"]
            st.session_state.role = data["role"]
            st.session_state.nome = data["nome"]
            st.session_state.username = username
            return True
        else:
            st.error("Credenciais inválidas")
            return False
    except Exception as e:
        st.error(f"Erro de conexão: {e}")
        return False

def register(username, password, role, nome, email=""):
    try:
        resp = requests.post(f"{API_BASE}/auth/register", json={
            "username": username,
            "password": password,
            "role": role,
            "nome": nome,
            "email": email
        })
        if resp.status_code == 200:
            st.success("Registo efetuado com sucesso! Faça login.")
            return True
        else:
            st.error(f"Erro no registo: {resp.text}")
            return False
    except Exception as e:
        st.error(f"Erro de conexão: {e}")
        return False

def logout():
    for key in ["token", "role", "nome", "username"]:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()

# ============================================================================
# TELA DE LOGIN / REGISTO (quando não autenticado)
# ============================================================================
if "token" not in st.session_state:
    # Esconde a sidebar completamente
    st.markdown("""
    <style>
        section[data-testid="stSidebar"] {
            display: none !important;
        }
    </style>
    """, unsafe_allow_html=True)

    # Cabeçalho simples (sem sidebar)
    st.markdown("""
    <div class="header">
        <div class="header-left">
            <span class="icon">📘</span>
            <div class="title-group">
                <h1>Previsão Académica</h1>
                <p>Sistema distribuído de previsão de desempenho</p>
            </div>
        </div>
        <div class="badge">🔬 Sistemas Distribuídos</div>
    </div>
    """, unsafe_allow_html=True)

    # Container centralizado
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    col_center = st.columns([1, 1.5, 1])[1]
    with col_center:
        with st.container():
            st.markdown('<div class="login-box">', unsafe_allow_html=True)
            tab1, tab2 = st.tabs(["🔐 Login", "📝 Registo"])

            with tab1:
                st.markdown('<h2 style="text-align:center;">Bem-vindo</h2>', unsafe_allow_html=True)
                st.markdown('<p style="text-align:center; color:#6c7a8a;">Entre com as suas credenciais</p>', unsafe_allow_html=True)
                with st.form("login_form"):
                    username = st.text_input("Username", placeholder="Ex: professor1")
                    password = st.text_input("Password", type="password", placeholder="••••••••")
                    submitted = st.form_submit_button("Entrar", use_container_width=True)
                    if submitted:
                        if login(username, password):
                            st.success("Login bem-sucedido!")
                            st.rerun()

            with tab2:
                st.markdown('<h2 style="text-align:center;">Criar Conta</h2>', unsafe_allow_html=True)
                st.markdown('<p style="text-align:center; color:#6c7a8a;">Registe-se como estudante ou professor</p>', unsafe_allow_html=True)
                with st.form("register_form"):
                    username = st.text_input("Username", placeholder="Escolha um username")
                    password = st.text_input("Password", type="password", placeholder="••••••••")
                    nome = st.text_input("Nome completo", placeholder="Ex: João Silva")
                    role = st.selectbox("Tipo de utilizador", ["estudante", "professor"])
                    email = st.text_input("Email (opcional)", placeholder="seu@email.com")
                    submitted = st.form_submit_button("Registar", use_container_width=True)
                    if submitted:
                        if register(username, password, role, nome, email):
                            st.info("Agora faça login na aba anterior.")

            st.markdown('</div>', unsafe_allow_html=True)  # fim login-box
    st.markdown('</div>', unsafe_allow_html=True)  # fim login-container

    st.markdown("""
    <div class="footer">
        <span>🔬 Sistemas Distribuídos · Mestrado · 2025</span>
    </div>
    """, unsafe_allow_html=True)

# ============================================================================
# APLICAÇÃO PRINCIPAL (após login)
# ============================================================================
else:
    # ---- CABEÇALHO ----
    st.markdown("""
    <div class="header">
        <div class="header-left">
            <span class="icon">📘</span>
            <div class="title-group">
                <h1>Previsão Académica</h1>
                <p>Análise de desempenho por semestre · recomendações personalizadas</p>
            </div>
        </div>
        <div class="badge">🔬 Sistemas Distribuídos · RabbitMQ + SQLite</div>
    </div>
    """, unsafe_allow_html=True)

    # ---- SIDEBAR ----
    with st.sidebar:
        st.markdown("### 🧭 Navegação")
        st.write(f"👤 **{st.session_state.nome}** ({st.session_state.role})")

        if st.session_state.role == "professor":
            menu = st.radio(
                "",
                ["📝 Registar Semestre", "📋 Listar Alunos", "🔍 Consultar Aluno"],
                label_visibility="collapsed"
            )
        else:
            menu = st.radio(
                "",
                ["📊 Meu Boletim"],
                label_visibility="collapsed"
            )

        if st.button("🚪 Logout"):
            logout()

        st.markdown("---")
        st.markdown("""
        <div style="background:#f4f7fc; border-radius:12px; padding:1rem;">
            <p style="font-weight:600; color:#0b1a33;">ℹ️ Sobre</p>
            <p style="font-size:0.85rem; color:#3a4a5e;">
                Sistema distribuído com autenticação JWT.<br>
                <strong>Versão 2.0</strong> · Mestrado SD
            </p>
        </div>
        """, unsafe_allow_html=True)

    headers = {"Authorization": f"Bearer {st.session_state.token}"}

    # ---- PROFESSOR: REGISTAR SEMESTRE ----
    if menu == "📝 Registar Semestre":
        st.markdown('<div class="section-title">📝 Registar Semestre</div>', unsafe_allow_html=True)
        with st.form("registo_semestre"):
            matricula_aluno = st.text_input("Matrícula do aluno (username)")
            semestre = st.text_input("Semestre (ex: 2025.1)", value="2025.1")
            st.markdown("**Disciplinas**")
            num_disciplinas = st.number_input("Número de disciplinas", min_value=1, max_value=10, value=3, step=1)
            disciplinas = []
            for i in range(num_disciplinas):
                with st.expander(f"Disciplina {i+1}"):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        codigo = st.text_input(f"Código {i+1}", value=f"DISC{i+1}")
                    with col2:
                        nota = st.number_input(f"Nota {i+1}", 0.0, 20.0, step=0.5, value=5.0)
                    with col3:
                        faltas = st.number_input(f"Faltas {i+1}", 0, step=1, value=0)
                    disciplinas.append({"codigo": codigo, "nota": nota, "faltas": faltas})
            submitted = st.form_submit_button("Registar Semestre")
            if submitted:
                if not matricula_aluno or not semestre or not disciplinas:
                    st.error("Preencha todos os campos.")
                else:
                    payload = {
                        "matricula": matricula_aluno,
                        "semestre": semestre,
                        "disciplinas": disciplinas
                    }
                    try:
                        resp = requests.post(f"{API_BASE}/aluno/semestre", json=payload, headers=headers)
                        if resp.status_code == 200:
                            st.success(f"Semestre {semestre} registado com sucesso! A previsão será processada.")
                        else:
                            st.error(f"Erro: {resp.status_code} - {resp.text}")
                    except Exception as e:
                        st.error(f"Erro de conexão: {e}")

    # ---- PROFESSOR: LISTAR ALUNOS ----
    elif menu == "📋 Listar Alunos":
        st.markdown('<div class="section-title">📋 Alunos Registados</div>', unsafe_allow_html=True)
        try:
            resp = requests.get(f"{API_BASE}/alunos", headers=headers)
            if resp.status_code == 200:
                alunos = resp.json()
                if alunos:
                    df = pd.DataFrame(alunos)
                    st.dataframe(df, use_container_width=True)
                    st.caption(f"Total: {len(alunos)} alunos")
                else:
                    st.info("Nenhum aluno registado.")
            else:
                st.error("Erro ao listar alunos.")
        except Exception as e:
            st.error(f"Erro: {e}")

    # ---- PROFESSOR: CONSULTAR ALUNO ----
    elif menu == "🔍 Consultar Aluno":
        st.markdown('<div class="section-title">🔍 Consultar Boletim de Aluno</div>', unsafe_allow_html=True)
        matricula = st.text_input("Matrícula do aluno")
        semestre = st.text_input("Semestre (ex: 2025.1)", value="2025.1")
        if st.button("Consultar"):
            if not matricula or not semestre:
                st.warning("Preencha a matrícula e o semestre.")
            else:
                try:
                    resp = requests.get(f"{API_BASE}/aluno/boletim/{semestre}?matricula={matricula}", headers=headers)
                    if resp.status_code == 200:
                        dados = resp.json()
                        if dados["disciplinas"]:
                            st.markdown(f"### 📊 Boletim de {matricula} - {semestre}")
                            df = pd.DataFrame(dados["disciplinas"])
                            st.dataframe(df, use_container_width=True)
                            if dados["resumo"]:
                                st.markdown("### 📈 Resumo do Semestre")
                                resumo = dados["resumo"]
                                col1, col2, col3 = st.columns(3)
                                col1.metric("Média Global", resumo.get("media_global", "N/A"))
                                col2.metric("Total Faltas", resumo.get("total_faltas", 0))
                                col3.metric("Disciplinas em Risco", resumo.get("disciplinas_em_risco", 0))
                                risco_global = resumo.get("risco_global")
                                if risco_global == "alto":
                                    st.error("⚠️ Risco Global: ALTO")
                                elif risco_global == "medio":
                                    st.warning("⚠️ Risco Global: MÉDIO")
                                else:
                                    st.success("✅ Risco Global: BAIXO")
                                if resumo.get("recomendacao_geral"):
                                    st.markdown(f"**Recomendação:** {resumo['recomendacao_geral']}")
                        else:
                            st.info("Nenhuma disciplina encontrada para este semestre.")
                    else:
                        st.error("Erro ao buscar boletim.")
                except Exception as e:
                    st.error(f"Erro: {e}")

    # ---- ESTUDANTE: MEU BOLETIM ----
    elif menu == "📊 Meu Boletim":
        st.markdown('<div class="section-title">📊 Meu Boletim</div>', unsafe_allow_html=True)
        semestre = st.text_input("Semestre (ex: 2025.1)", value="2025.1")
        if st.button("Ver meu boletim"):
            try:
                resp = requests.get(f"{API_BASE}/aluno/boletim/{semestre}", headers=headers)
                if resp.status_code == 200:
                    dados = resp.json()
                    if dados["disciplinas"]:
                        st.markdown(f"### 📊 Boletim de {st.session_state.nome} - {semestre}")
                        df = pd.DataFrame(dados["disciplinas"])
                        st.dataframe(df, use_container_width=True)
                        if dados["resumo"]:
                            st.markdown("### 📈 Resumo do Semestre")
                            resumo = dados["resumo"]
                            col1, col2, col3 = st.columns(3)
                            col1.metric("Média Global", resumo.get("media_global", "N/A"))
                            col2.metric("Total Faltas", resumo.get("total_faltas", 0))
                            col3.metric("Disciplinas em Risco", resumo.get("disciplinas_em_risco", 0))
                            risco_global = resumo.get("risco_global")
                            if risco_global == "alto":
                                st.error("⚠️ Risco Global: ALTO")
                            elif risco_global == "medio":
                                st.warning("⚠️ Risco Global: MÉDIO")
                            else:
                                st.success("✅ Risco Global: BAIXO")
                            if resumo.get("recomendacao_geral"):
                                st.markdown(f"**Recomendação:** {resumo['recomendacao_geral']}")
                    else:
                        st.info("Nenhuma disciplina encontrada para este semestre.")
                else:
                    st.error("Erro ao buscar boletim.")
            except Exception as e:
                st.error(f"Erro: {e}")

    # ---- RODAPÉ ----
    st.markdown("""
    <div class="footer">
        <span>🔬 Sistemas Distribuídos · Mestrado · 2025</span>
    </div>
    """, unsafe_allow_html=True)