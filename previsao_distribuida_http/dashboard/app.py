import streamlit as st
import requests
import pandas as pd

# ---- CONFIGURAÇÃO DA PÁGINA ----
st.set_page_config(
    page_title="Previsão Académica",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---- CSS PREMIUM ----
st.markdown("""
<style>
    /* ----- FONTE ----- */
    @import url('https://fonts.googleapis.com/css2?family=Inter:ital,wght@0,300;0,400;0,500;0,600;0,700;0,800;1,400&display=swap');
    * { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; box-sizing: border-box; }

    /* ----- FUNDO ----- */
    .stApp {
        background: linear-gradient(160deg, #f0f4fb 0%, #e2ecf9 100%);
        min-height: 100vh;
    }

    /* ----- CABEÇALHO GLASS ----- */
    .header {
        background: rgba(10, 25, 55, 0.80);
        backdrop-filter: blur(24px);
        -webkit-backdrop-filter: blur(24px);
        border: 1px solid rgba(255,255,255,0.08);
        padding: 0.6rem 2rem;
        border-radius: 28px;
        color: white;
        margin-bottom: 1.8rem;
        box-shadow: 0 12px 48px rgba(0,20,50,0.08), inset 0 1px 0 rgba(255,255,255,0.04);
        display: flex;
        align-items: center;
        justify-content: space-between;
        flex-wrap: wrap;
        gap: 0.8rem;
        transition: all 0.3s;
    }
    .header:hover { box-shadow: 0 16px 56px rgba(0,20,50,0.12); }

    .header-left { display: flex; align-items: center; gap: 1rem; }
    .header-left .icon {
        font-size: 2rem;
        background: linear-gradient(135deg, #f7b733, #fc4a1a);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        filter: drop-shadow(0 2px 12px rgba(252,74,26,0.25));
    }
    .header-left .title-group h1 {
        font-size: 1.5rem; font-weight: 700; margin: 0; letter-spacing: -0.3px;
        background: linear-gradient(135deg, #fff 30%, #a0c4ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    .header-left .title-group p {
        font-size: 0.8rem; opacity: 0.7; margin: 0; font-weight: 300; color: #c0d8f0;
    }

    .header-right { display: flex; align-items: center; gap: 0.6rem; }

    .user-badge {
        background: rgba(255,255,255,0.06); border-radius: 40px;
        padding: 0.2rem 1rem 0.2rem 0.6rem;
        display: flex; align-items: center; gap: 0.5rem;
        border: 1px solid rgba(255,255,255,0.06);
        backdrop-filter: blur(4px);
        transition: all 0.2s;
    }
    .user-badge:hover { background: rgba(255,255,255,0.10); }
    .user-badge .avatar {
        width: 28px; height: 28px; border-radius: 50%;
        background: linear-gradient(135deg, #f7b733, #fc4a1a);
        display: flex; align-items: center; justify-content: center;
        color: white; font-weight: 600; font-size: 0.7rem;
    }
    .user-badge span { font-weight: 400; color: #e8f0ff; font-size: 0.8rem; }
    .user-badge .role-tag {
        background: rgba(255,255,255,0.10);
        padding: 0.05rem 0.6rem; border-radius: 30px;
        font-size: 0.55rem; font-weight: 500; text-transform: uppercase;
        letter-spacing: 0.5px; color: #b0ccff;
    }

    /* ----- BOTÃO ENTRAR (centralizado e no topo) ----- */
    .login-button-wrapper {
        display: flex;
        justify-content: center;
        margin-top: 0.2rem;
        margin-bottom: 0.5rem;
    }

    /* ----- POPOVER (abre para baixo) ----- */
    .stPopover {
        border: none !important;
        background: transparent !important;
    }
    .stPopover > div {
        background: rgba(255,255,255,0.95) !important;
        backdrop-filter: blur(24px) !important;
        -webkit-backdrop-filter: blur(24px) !important;
        border-radius: 20px !important;
        border: 1px solid rgba(255,255,255,0.4) !important;
        box-shadow: 0 16px 48px rgba(0,20,40,0.10) !important;
        padding: 1.5rem 1.8rem !important;
        min-width: 340px !important;
        max-width: 380px !important;
        animation: fadeUp 0.3s ease-out both;
        margin-top: 0 !important;
    }
    .stPopover h3 {
        color: #0b1a33;
        font-weight: 700;
        font-size: 1.1rem;
        margin-top: 0;
        margin-bottom: 0.2rem;
        letter-spacing: -0.3px;
    }
    .stPopover .subtitle {
        color: #6c7a8a;
        font-size: 0.85rem;
        margin-bottom: 1.2rem;
        font-weight: 400;
    }
    .stPopover .stTextInput>div>div>input {
        height: 36px;
        min-height: 36px;
        font-size: 0.85rem;
        border-radius: 14px;
        border: 1.5px solid rgba(0,0,0,0.04);
        background: rgba(255,255,255,0.70);
        backdrop-filter: blur(4px);
        padding: 0.4rem 1rem;
    }
    .stPopover .stTextInput>div>div>input:focus {
        border-color: #2a5298;
        box-shadow: 0 0 0 4px rgba(42,82,152,0.06);
        background: white;
    }
    .stPopover .stButton>button {
        background: linear-gradient(145deg, #1d3b66, #2a5298);
        color: white;
        border-radius: 40px;
        padding: 0.4rem 1.5rem;
        font-weight: 600;
        border: none;
        transition: all 0.25s;
        box-shadow: 0 4px 16px rgba(42,82,152,0.15);
        width: 100%;
        font-size: 0.9rem;
    }
    .stPopover .stButton>button:hover {
        transform: scale(1.02);
        box-shadow: 0 8px 28px rgba(42,82,152,0.25);
        background: linear-gradient(145deg, #234b7a, #3366aa);
    }
    .stPopover .stDivider {
        margin: 0.8rem 0;
        border-color: rgba(0,0,0,0.04);
    }
    .stPopover .stSelectbox>div>div>select {
        border-radius: 14px;
        border: 1.5px solid rgba(0,0,0,0.04);
        background: rgba(255,255,255,0.70);
        backdrop-filter: blur(4px);
        padding: 0.4rem 1rem;
        font-size: 0.85rem;
        height: 36px;
    }
    .stPopover .register-hint {
        font-size: 0.8rem;
        color: #6c7a8a;
        text-align: center;
        margin-top: 0.5rem;
    }
    .stPopover .register-hint strong {
        color: #2a5298;
        cursor: pointer;
    }

    /* ----- CARDS GLASS ----- */
    .card-glass {
        background: rgba(255,255,255,0.50);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(255,255,255,0.40);
        border-radius: 24px;
        padding: 1.5rem 1.8rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 28px rgba(0,20,40,0.03), inset 0 1px 0 rgba(255,255,255,0.8);
        transition: all 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94);
    }
    .card-glass:hover {
        transform: translateY(-3px);
        box-shadow: 0 16px 56px rgba(0,20,40,0.06), inset 0 1px 0 rgba(255,255,255,0.8);
        background: rgba(255,255,255,0.70);
    }

    /* ----- TÍTULOS ----- */
    .section-title {
        font-size: 1.4rem; font-weight: 700; color: #0b1a33;
        letter-spacing: -0.3px; margin-bottom: 1rem;
        display: inline-block; position: relative;
    }
    .section-title::after {
        content: ""; display: block; width: 60%; height: 3px;
        background: linear-gradient(90deg, #2a5298, #6a9bc7);
        margin-top: 0.2rem; border-radius: 4px; opacity: 0.5;
    }

    /* ----- RISCO ----- */
    .risco-alto, .risco-medio, .risco-baixo {
        font-weight: 600; padding: 0.15rem 1rem; border-radius: 40px;
        display: inline-block; font-size: 0.7rem; letter-spacing: 0.3px;
        border: 1px solid transparent; backdrop-filter: blur(4px);
    }
    .risco-alto { background: rgba(220,60,60,0.08); color: #b34033; border-color: rgba(220,60,60,0.15); }
    .risco-medio { background: rgba(220,160,40,0.08); color: #b45f2a; border-color: rgba(220,160,40,0.15); }
    .risco-baixo { background: rgba(40,180,80,0.08); color: #1f6e3b; border-color: rgba(40,180,80,0.15); }

    /* ----- INPUTS ----- */
    .stTextInput>div>div>input, .stNumberInput>div>div>input, .stSelectbox>div>div>select {
        border-radius: 14px; border: 1.5px solid rgba(0,0,0,0.04);
        padding: 0.4rem 1rem; background: rgba(255,255,255,0.70);
        backdrop-filter: blur(4px); font-size: 0.85rem;
        transition: all 0.25s; height: 38px;
    }
    .stTextInput>div>div>input:focus { border-color: #2a5298; box-shadow: 0 0 0 4px rgba(42,82,152,0.06); background: white; }

    /* ----- BOTÕES ----- */
    .stButton>button {
        background: linear-gradient(145deg, #1d3b66, #2a5298);
        color: white; border-radius: 40px; padding: 0.5rem 2rem;
        font-weight: 600; border: none; transition: all 0.3s;
        box-shadow: 0 4px 20px rgba(42,82,152,0.15); width: 100%; font-size: 0.9rem;
        position: relative; overflow: hidden;
    }
    .stButton>button::before {
        content: ''; position: absolute; top: 0; left: -100%; width: 100%; height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.10), transparent);
        transition: left 0.6s;
    }
    .stButton>button:hover::before { left: 100%; }
    .stButton>button:hover {
        transform: translateY(-2px) scale(1.02);
        box-shadow: 0 8px 32px rgba(42,82,152,0.25);
        background: linear-gradient(145deg, #234b7a, #3366aa);
    }

    /* ----- SIDEBAR ----- */
    section[data-testid="stSidebar"] {
        background: rgba(255,255,255,0.40);
        backdrop-filter: blur(24px);
        -webkit-backdrop-filter: blur(24px);
        border-right: 1px solid rgba(255,255,255,0.30);
        padding: 1rem 0.3rem;
    }
    section[data-testid="stSidebar"] .stRadio label {
        font-weight: 500; color: #1a2a44; padding: 0.4rem 1rem;
        border-radius: 12px; transition: all 0.2s; border: 1px solid transparent; font-size: 0.85rem;
    }
    section[data-testid="stSidebar"] .stRadio label:hover { background: rgba(255,255,255,0.50); border-color: rgba(0,0,0,0.04); }

    .sidebar-footer {
        font-size: 0.65rem; color: #8896a8; margin-top: 2rem;
        text-align: center; border-top: 1px solid rgba(0,0,0,0.04);
        padding-top: 1rem; font-weight: 400; letter-spacing: 0.3px;
    }

    /* ----- DATAFRAME ----- */
    .dataframe {
        border: none !important; border-radius: 18px !important; overflow: hidden;
        box-shadow: 0 2px 16px rgba(0,0,0,0.02); font-size: 0.85rem;
        background: rgba(255,255,255,0.30) !important; backdrop-filter: blur(4px);
    }
    .dataframe thead tr th { background: rgba(15,31,61,0.04) !important; color: #0b1a33; font-weight: 600; border-bottom: 2px solid rgba(0,0,0,0.04) !important; padding: 0.5rem 1rem !important; }
    .dataframe tbody tr td { border-bottom: 1px solid rgba(0,0,0,0.02) !important; padding: 0.4rem 1rem !important; }
    .dataframe tbody tr:hover td { background: rgba(255,255,255,0.40) !important; }

    /* ----- WELCOME CARD ----- */
    .welcome-wrapper {
        display: flex;
        justify-content: center;
        padding: 0.5rem 1rem 2rem;
    }
    .welcome-card {
        background: rgba(255,255,255,0.40);
        backdrop-filter: blur(24px);
        border: 1px solid rgba(255,255,255,0.40);
        border-radius: 32px;
        padding: 2.5rem 2.5rem;
        box-shadow: 0 8px 40px rgba(0,20,40,0.03);
        text-align: center;
        max-width: 620px;
        width: 100%;
        transition: all 0.4s;
        animation: fadeUp 0.6s ease-out both;
    }
    .welcome-card:hover { background: rgba(255,255,255,0.60); box-shadow: 0 16px 64px rgba(0,20,40,0.05); }
    .welcome-card h2 {
        font-size: 2.2rem; font-weight: 700; color: #0b1a33; margin-top: 0;
        letter-spacing: -0.5px;
        background: linear-gradient(135deg, #0b1a33 30%, #2a5298);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    .welcome-card p { color: #3a4a5e; font-size: 1rem; line-height: 1.8; max-width: 480px; margin: 1rem auto; }
    .welcome-card .highlight { color: #2a5298; font-weight: 600; }

    .tag-group { display: flex; justify-content: center; gap: 0.8rem; flex-wrap: wrap; margin-top: 1.5rem; }
    .tag-group .tag {
        background: rgba(255,255,255,0.30); backdrop-filter: blur(4px);
        padding: 0.2rem 1rem; border-radius: 40px; font-size: 0.7rem; font-weight: 500;
        color: #2a5298; border: 1px solid rgba(42,82,152,0.06); transition: all 0.2s;
    }
    .tag-group .tag:hover { background: rgba(255,255,255,0.60); transform: translateY(-2px); }

    /* ----- METRIC CARDS ----- */
    .metric-card {
        background: rgba(255,255,255,0.35); backdrop-filter: blur(8px);
        border: 1px solid rgba(255,255,255,0.40); border-radius: 18px;
        padding: 0.8rem 1rem; text-align: center; transition: all 0.3s;
        box-shadow: 0 2px 12px rgba(0,0,0,0.02);
    }
    .metric-card:hover { background: rgba(255,255,255,0.60); transform: translateY(-2px); box-shadow: 0 8px 28px rgba(0,20,40,0.04); }
    .metric-card .value { font-size: 2rem; font-weight: 700; color: #0b1a33; line-height: 1.2; }
    .metric-card .label { font-size: 0.7rem; color: #6c7a8a; font-weight: 400; margin-top: 0.1rem; letter-spacing: 0.2px; }

    /* ----- EXPANDER ----- */
    .stExpander { border: none !important; box-shadow: none !important; background: transparent !important; }
    .stExpander > div:first-child {
        background: rgba(255,255,255,0.15); border-radius: 14px !important;
        border: 1px solid rgba(255,255,255,0.20); padding: 0.3rem 1rem !important;
        font-weight: 500; font-size: 0.85rem; backdrop-filter: blur(4px);
        transition: all 0.2s;
    }
    .stExpander > div:first-child:hover { background: rgba(255,255,255,0.30); }

    /* ----- RODAPÉ ----- */
    .footer { margin-top: 2.5rem; text-align: center; color: #b0c0d4; font-size: 0.75rem; border-top: 1px solid rgba(0,0,0,0.02); padding-top: 1.2rem; letter-spacing: 0.2px; }
    .footer span { background: rgba(255,255,255,0.30); backdrop-filter: blur(4px); padding: 0.15rem 0.8rem; border-radius: 40px; display: inline-block; }

    /* ----- ANIMAÇÃO ----- */
    @keyframes fadeUp { from { opacity: 0; transform: translateY(12px); } to { opacity: 1; transform: translateY(0); } }
    .welcome-card, .card-glass, .stPopover > div { animation: fadeUp 0.4s ease-out both; }

    /* ----- RESPONSIVO ----- */
    @media (max-width: 768px) {
        .header-left .title-group h1 { font-size: 1.1rem; }
        .header-left .icon { font-size: 1.4rem; }
        .header { padding: 0.6rem 1rem; }
        .welcome-card { padding: 1.8rem 1.2rem; }
        .welcome-card h2 { font-size: 1.6rem; }
        .card-glass { padding: 1rem 1.2rem; }
        .section-title { font-size: 1.1rem; }
        .stPopover > div { min-width: 280px !important; padding: 1.2rem 1.2rem !important; }
    }
</style>
""", unsafe_allow_html=True)

# ---- CONFIGURAÇÕES DA API ----
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
            st.error("❌ Credenciais inválidas")
            return False
    except Exception as e:
        st.error(f"❌ Erro de conexão: {e}")
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
            st.success("✅ Registo efetuado com sucesso! Faça login.")
            return True
        else:
            st.error(f"❌ Erro no registo: {resp.text}")
            return False
    except Exception as e:
        st.error(f"❌ Erro de conexão: {e}")
        return False

def logout():
    for key in ["token", "role", "nome", "username"]:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()

# ---- RENDERIZAÇÃO ----
def render_header():
    st.markdown("""
    <div class="header">
        <div class="header-left">
            <span class="icon">🎓</span>
            <div class="title-group">
                <h1>Previsão Académica</h1>
                <p>Análise de desempenho · recomendações inteligentes</p>
            </div>
        </div>
        <div class="header-right">
    """, unsafe_allow_html=True)

    if "token" in st.session_state:
        avatar = st.session_state.nome[0].upper() if st.session_state.nome else "U"
        st.markdown(f"""
            <div class="user-badge">
                <div class="avatar">{avatar}</div>
                <span>{st.session_state.nome}</span>
                <span class="role-tag">{st.session_state.role}</span>
            </div>
        """, unsafe_allow_html=True)
        if st.button("🚪 Sair", key="logout_btn"):
            logout()
    else:
        st.markdown("""
            <span style="color:rgba(255,255,255,0.6); font-size:0.8rem;">🔒 Não autenticado</span>
        """, unsafe_allow_html=True)

    st.markdown("""
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_public_page():
    # Botão centralizado no topo
    st.markdown('<div class="login-button-wrapper">', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        with st.popover("🔑 Entrar", use_container_width=False):
            # Abas: Login e Registo
            tab1, tab2 = st.tabs(["🔐 Login", "📝 Registo"])

            with tab1:
                st.markdown("### 🔐 Login")
                st.markdown('<p class="subtitle">Entre com as suas credenciais</p>', unsafe_allow_html=True)
                with st.form("login_popover"):
                    username = st.text_input("Username", placeholder="Ex: professor1")
                    password = st.text_input("Password", type="password", placeholder="••••••••")
                    submitted = st.form_submit_button("Entrar")
                    if submitted:
                        if login(username, password):
                            st.success("✅ Login bem-sucedido!")
                            st.rerun()
                # Dica para registo
                st.markdown('<p class="register-hint">Não tem conta? Clique na aba <strong>Registo</strong> acima.</p>', unsafe_allow_html=True)

            with tab2:
                st.markdown("### 📝 Registo")
                st.markdown('<p class="subtitle">Crie a sua conta</p>', unsafe_allow_html=True)
                with st.form("register_popover"):
                    reg_username = st.text_input("Username (registo)", placeholder="Escolha um username")
                    reg_password = st.text_input("Password (registo)", type="password", placeholder="••••••••")
                    reg_nome = st.text_input("Nome completo", placeholder="Ex: João Silva")
                    reg_role = st.selectbox("Tipo de utilizador", ["estudante", "professor"])
                    reg_email = st.text_input("Email (opcional)", placeholder="seu@email.com")
                    reg_submitted = st.form_submit_button("Registar")
                    if reg_submitted:
                        if register(reg_username, reg_password, reg_role, reg_nome, reg_email):
                            st.info("ℹ️ Agora faça login na aba anterior.")
    st.markdown('</div>', unsafe_allow_html=True)

    # Card de boas‑vindas
    st.markdown('<div class="welcome-wrapper">', unsafe_allow_html=True)
    with st.container():
        st.markdown("""
        <div class="welcome-card">
            <h2>📘 Bem-vindo</h2>
            <p>
                Este sistema permite <span class="highlight">prever o risco de reprovação</span> dos alunos 
                com base em <span class="highlight">notas e faltas</span>, gerando recomendações personalizadas 
                de estudo e orientação de carreira.
            </p>
            <div class="tag-group">
                <span class="tag">🎯 Previsão por semestre</span>
                <span class="tag">📊 Resumo agregado</span>
                <span class="tag">🧠 Recomendações personalizadas</span>
                <span class="tag">🔐 Autenticação JWT</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

def render_dashboard():
    headers = {"Authorization": f"Bearer {st.session_state.token}"}

    with st.sidebar:
        st.markdown("### 🧭 Navegação")
        st.write(f"👤 **{st.session_state.nome}**")

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

        st.markdown("---")
        st.markdown("""
        <div style="background:rgba(255,255,255,0.25); backdrop-filter:blur(8px); border-radius:16px; padding:0.8rem 1rem; border:1px solid rgba(255,255,255,0.3);">
            <p style="font-weight:600; color:#0b1a33; margin:0; font-size:0.8rem;">ℹ️ Sobre</p>
            <p style="font-size:0.7rem; color:#3a4a5e; margin:0.2rem 0 0;">
                Sistema distribuído · JWT · RabbitMQ<br>
                <strong>v2.0</strong> · Mestrado SD
            </p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('<div class="sidebar-footer">© 2025 · Todos os direitos reservados</div>', unsafe_allow_html=True)

    # ---- REGISTAR SEMESTRE (COM DROPDOWNS E FILTRO POR SEMESTRE) ----
    if menu == "📝 Registar Semestre":
        st.markdown('<div class="section-title">📝 Registar Semestre</div>', unsafe_allow_html=True)

        # Funções para carregar listas com cache
        @st.cache_data(ttl=60)
        def get_alunos():
            try:
                resp = requests.get(f"{API_BASE}/alunos", headers=headers)
                if resp.status_code == 200:
                    return resp.json()
                else:
                    return []
            except:
                return []

        @st.cache_data(ttl=60)
        def get_disciplinas():
            try:
                resp = requests.get(f"{API_BASE}/disciplinas", headers=headers)
                if resp.status_code == 200:
                    return resp.json()
                else:
                    return []
            except:
                return []

        alunos = get_alunos()
        disciplinas = get_disciplinas()

        if not alunos:
            st.warning("⚠️ Nenhum aluno registado. Crie primeiro um aluno.")
        if not disciplinas:
            st.warning("⚠️ Nenhuma disciplina registada. Crie primeiro uma disciplina.")

        with st.container():
            st.markdown('<div class="card-glass">', unsafe_allow_html=True)
            with st.form("registo_semestre_compacto"):
                # Seleção do aluno (dropdown)
                if alunos:
                    aluno_options = {f"{a['nome']} ({a['username']})": a['username'] for a in alunos}
                    selected_aluno_display = st.selectbox(
                        "Aluno",
                        options=list(aluno_options.keys()),
                        help="Selecione o aluno a registar."
                    )
                    matricula_aluno = aluno_options[selected_aluno_display]
                else:
                    matricula_aluno = st.text_input("Matrícula do aluno (sem alunos disponíveis)", placeholder="Ex: aluno1")

                # ---- Seleção do Semestre (dropdown) ----
                semestre = st.selectbox(
                    "Semestre",
                    options=["I SEMESTRE", "II SEMESTRE"],
                    index=0,
                    help="Selecione o semestre para o qual deseja registar as disciplinas."
                )

                # ---- Número de disciplinas (fixo em 6) ----
                num_disciplinas = st.number_input(
                    "Nº de disciplinas",
                    min_value=6,
                    max_value=6,
                    value=6,
                    step=1,
                    help="Cada semestre tem exatamente 6 disciplinas."
                )

                # ---- Filtra as disciplinas pelo semestre selecionado ----
                disciplinas_filtradas = [d for d in disciplinas if d.get("semestre") == semestre]

                disciplinas_list = []
                for i in range(num_disciplinas):
                    with st.expander(f"Disciplina {i+1}", expanded=False):
                        # Seleção da disciplina (dropdown com filtro)
                        if disciplinas_filtradas:
                            disc_options = {f"{d['codigo']} - {d['nome']}": d['codigo'] for d in disciplinas_filtradas}
                            selected_disc_display = st.selectbox(
                                f"Disciplina {i+1}",
                                options=list(disc_options.keys()),
                                key=f"disc_select_{i}"
                            )
                            codigo = disc_options[selected_disc_display]
                        else:
                            st.warning(f"⚠️ Nenhuma disciplina disponível para o {semestre}.")
                            codigo = st.text_input(f"Código da disciplina {i+1}", value=f"DISC{i+1}", key=f"cod_{i}")

                        nota = st.number_input(f"Nota {i+1}", 0.0, 20.0, step=0.5, value=5.0, key=f"nota_{i}")
                        faltas = st.number_input(f"Faltas {i+1}", 0, step=1, value=0, key=f"faltas_{i}")
                        # ---- CORREÇÃO: usar "disciplina_codigo" em vez de "codigo" ----
                        disciplinas_list.append({"disciplina_codigo": codigo, "nota": nota, "faltas": faltas})

                submitted = st.form_submit_button("📤 Registar Semestre")
                if submitted:
                    if not matricula_aluno or not semestre or not disciplinas_list:
                        st.error("Preencha todos os campos.")
                    else:
                        payload = {
                            "matricula": matricula_aluno,
                            "semestre": semestre,
                            "disciplinas": disciplinas_list
                        }
                        try:
                            resp = requests.post(f"{API_BASE}/aluno/semestre", json=payload, headers=headers)
                            if resp.status_code == 200:
                                st.success(f"✅ Semestre {semestre} registado com sucesso para {matricula_aluno}! A previsão será processada.")
                            else:
                                st.error(f"❌ Erro: {resp.status_code} - {resp.text}")
                        except Exception as e:
                            st.error(f"❌ Erro de conexão: {e}")
            st.markdown('</div>', unsafe_allow_html=True)

    # ---- LISTAR ALUNOS ----
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

    # ---- CONSULTAR ALUNO ----
    elif menu == "🔍 Consultar Aluno":
        st.markdown('<div class="section-title">🔍 Consultar Boletim</div>', unsafe_allow_html=True)
        with st.container():
            st.markdown('<div class="card-glass">', unsafe_allow_html=True)
            col1, col2 = st.columns([2, 1])
            with col1:
                matricula = st.text_input("Matrícula do aluno", placeholder="Ex: aluno1")
                semestre = st.selectbox(
                    "Semestre",
                    options=["I SEMESTRE", "II SEMESTRE"],
                    index=0,
                    key="consult_semestre"
                )
                if st.button("🔎 Consultar"):
                    if not matricula or not semestre:
                        st.warning("Preencha a matrícula e o semestre.")
                    else:
                        try:
                            resp = requests.get(f"{API_BASE}/aluno/boletim/{semestre}?matricula={matricula}", headers=headers)
                            if resp.status_code == 200:
                                dados = resp.json()
                                if dados["disciplinas"]:
                                    st.markdown(f"### 📊 Boletim de **{matricula}** - {semestre}")
                                    df = pd.DataFrame(dados["disciplinas"])
                                    st.dataframe(df, use_container_width=True)
                                    if dados["resumo"]:
                                        st.markdown("### 📈 Resumo do Semestre")
                                        resumo = dados["resumo"]
                                        col_a, col_b, col_c = st.columns(3)
                                        with col_a:
                                            st.markdown(f"""
                                            <div class="metric-card">
                                                <div class="value">{resumo.get('media_global', 'N/A')}</div>
                                                <div class="label">📊 Média Global</div>
                                            </div>
                                            """, unsafe_allow_html=True)
                                        with col_b:
                                            st.markdown(f"""
                                            <div class="metric-card">
                                                <div class="value">{resumo.get('total_faltas', 0)}</div>
                                                <div class="label">📅 Total Faltas</div>
                                            </div>
                                            """, unsafe_allow_html=True)
                                        with col_c:
                                            st.markdown(f"""
                                            <div class="metric-card">
                                                <div class="value">{resumo.get('disciplinas_em_risco', 0)}</div>
                                                <div class="label">⚠️ Disciplinas em Risco</div>
                                            </div>
                                            """, unsafe_allow_html=True)
                                        risco_global = resumo.get("risco_global")
                                        if risco_global == "alto":
                                            st.error("⚠️ Risco Global: ALTO")
                                        elif risco_global == "medio":
                                            st.warning("⚠️ Risco Global: MÉDIO")
                                        else:
                                            st.success("✅ Risco Global: BAIXO")
                                        if resumo.get("recomendacao_geral"):
                                            st.markdown(f"**💡 Recomendação:** {resumo['recomendacao_geral']}")
                                else:
                                    st.info("Nenhuma disciplina encontrada para este semestre.")
                            else:
                                st.error("Erro ao buscar boletim.")
                        except Exception as e:
                            st.error(f"Erro: {e}")
            with col2:
                st.markdown("""
                <div style="background:rgba(255,255,255,0.25); backdrop-filter:blur(8px); border-radius:14px; padding:1rem; border:1px solid rgba(255,255,255,0.3);">
                    <p style="font-weight:600; color:#0b1a33; margin:0; font-size:0.9rem;">📌 Dica</p>
                    <p style="font-size:0.85rem; color:#4a5a6e; margin:0.3rem 0 0;">
                        Utilize a matrícula do aluno (username) para consultar o boletim completo.
                    </p>
                </div>
                """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

    # ---- MEU BOLETIM ----
    elif menu == "📊 Meu Boletim":
        st.markdown('<div class="section-title">📊 Meu Boletim</div>', unsafe_allow_html=True)
        with st.container():
            st.markdown('<div class="card-glass">', unsafe_allow_html=True)
            semestre = st.selectbox(
                "Semestre",
                options=["I SEMESTRE", "II SEMESTRE"],
                index=0,
                key="meu_boletim_semestre"
            )
            if st.button("🔎 Ver meu boletim"):
                try:
                    resp = requests.get(f"{API_BASE}/aluno/boletim/{semestre}", headers=headers)
                    if resp.status_code == 200:
                        dados = resp.json()
                        if dados["disciplinas"]:
                            st.markdown(f"### 📊 Boletim de **{st.session_state.nome}** - {semestre}")
                            df = pd.DataFrame(dados["disciplinas"])
                            st.dataframe(df, use_container_width=True)
                            if dados["resumo"]:
                                st.markdown("### 📈 Resumo do Semestre")
                                resumo = dados["resumo"]
                                col_a, col_b, col_c = st.columns(3)
                                with col_a:
                                    st.markdown(f"""
                                    <div class="metric-card">
                                        <div class="value">{resumo.get('media_global', 'N/A')}</div>
                                        <div class="label">📊 Média Global</div>
                                    </div>
                                    """, unsafe_allow_html=True)
                                with col_b:
                                    st.markdown(f"""
                                    <div class="metric-card">
                                        <div class="value">{resumo.get('total_faltas', 0)}</div>
                                        <div class="label">📅 Total Faltas</div>
                                    </div>
                                    """, unsafe_allow_html=True)
                                with col_c:
                                    st.markdown(f"""
                                    <div class="metric-card">
                                        <div class="value">{resumo.get('disciplinas_em_risco', 0)}</div>
                                        <div class="label">⚠️ Disciplinas em Risco</div>
                                    </div>
                                    """, unsafe_allow_html=True)
                                risco_global = resumo.get("risco_global")
                                if risco_global == "alto":
                                    st.error("⚠️ Risco Global: ALTO")
                                elif risco_global == "medio":
                                    st.warning("⚠️ Risco Global: MÉDIO")
                                else:
                                    st.success("✅ Risco Global: BAIXO")
                                if resumo.get("recomendacao_geral"):
                                    st.markdown(f"**💡 Recomendação:** {resumo['recomendacao_geral']}")
                        else:
                            st.info("Nenhuma disciplina encontrada para este semestre.")
                    else:
                        st.error("Erro ao buscar boletim.")
                except Exception as e:
                    st.error(f"Erro: {e}")
            st.markdown('</div>', unsafe_allow_html=True)

# ---- ESTRUTURA PRINCIPAL ----
render_header()

if "token" in st.session_state:
    render_dashboard()
else:
    render_public_page()

# ---- RODAPÉ ----
st.markdown("""
<div class="footer">
    <span>🔬 Sistemas Distribuídos · Mestrado · 2025</span>
</div>
""", unsafe_allow_html=True)