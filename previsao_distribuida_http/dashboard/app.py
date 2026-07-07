import streamlit as st
import requests
import pandas as pd
import time

# ---- CONFIGURAÇÃO DA PÁGINA ----
st.set_page_config(
    page_title="Previsão de Desempenho Académico",
    page_icon="📘",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---- CSS PERSONALIZADO (PROFISSIONAL E ELEGANTE) ----
st.markdown("""
<style>
    /* ----- TIPOGRAFIA E RESET ----- */
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }
    .main {
        background: #f4f7fc;
    }

    /* ----- CABEÇALHO COM GRADIENTE E SOMBRA ----- */
    .header {
        background: linear-gradient(135deg, #0b1a33 0%, #1d3b66 50%, #2a5298 100%);
        padding: 1.5rem 2rem;
        border-radius: 16px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 8px 30px rgba(26, 67, 113, 0.25);
        position: relative;
        overflow: hidden;
        display: flex;
        align-items: center;
        justify-content: space-between;
        flex-wrap: wrap;
        gap: 1rem;
    }
    .header::after {
        content: "";
        position: absolute;
        top: -50%;
        right: -10%;
        width: 300px;
        height: 300px;
        background: rgba(255, 255, 255, 0.05);
        border-radius: 50%;
        pointer-events: none;
    }
    .header-left {
        display: flex;
        align-items: center;
        gap: 1rem;
        z-index: 1;
    }
    .header-left .icon {
        font-size: 2.8rem;
        line-height: 1;
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
        margin: 0.2rem 0 0;
        font-weight: 300;
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
        z-index: 1;
    }

    /* ----- CARDS COM SOMBRA E BORDA SUTIL ----- */
    .card {
        background: #ffffff;
        border-radius: 14px;
        padding: 1.6rem 1.8rem;
        margin-bottom: 1.8rem;
        box-shadow: 0 4px 20px rgba(0, 20, 40, 0.06);
        border: 1px solid rgba(0, 0, 0, 0.03);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 35px rgba(0, 20, 40, 0.10);
    }

    /* ----- TÍTULOS DAS SECÇÕES ----- */
    .section-title {
        font-size: 1.5rem;
        font-weight: 600;
        color: #0b1a33;
        letter-spacing: -0.3px;
        margin-bottom: 1.2rem;
        padding-bottom: 0.5rem;
        border-bottom: 3px solid #2a5298;
        display: inline-block;
    }

    /* ----- ETIQUETAS DE RISCO (MAIS ELABORADAS) ----- */
    .risco-alto {
        background: linear-gradient(135deg, #fce4e4, #f8d0d0);
        color: #a13024;
        font-weight: 600;
        padding: 0.3rem 1.2rem;
        border-radius: 30px;
        display: inline-block;
        border: 1px solid #f0baba;
        box-shadow: 0 2px 6px rgba(190, 50, 30, 0.08);
    }
    .risco-medio {
        background: linear-gradient(135deg, #fff3e0, #ffe4c4);
        color: #b45f2a;
        font-weight: 600;
        padding: 0.3rem 1.2rem;
        border-radius: 30px;
        display: inline-block;
        border: 1px solid #f5d5a0;
        box-shadow: 0 2px 6px rgba(200, 120, 40, 0.08);
    }
    .risco-baixo {
        background: linear-gradient(135deg, #e3f5e9, #c8e6d9);
        color: #1f6e3b;
        font-weight: 600;
        padding: 0.3rem 1.2rem;
        border-radius: 30px;
        display: inline-block;
        border: 1px solid #9ed5b5;
        box-shadow: 0 2px 6px rgba(30, 120, 60, 0.08);
    }

    /* ----- LINHAS DE PREVISÃO (cards internos) ----- */
    .previsao-item {
        display: flex;
        align-items: center;
        gap: 1.2rem;
        background: #fafcff;
        padding: 0.8rem 1.2rem;
        border-radius: 10px;
        border: 1px solid #eaedf2;
        margin-top: 0.6rem;
        transition: background 0.15s;
    }
    .previsao-item:hover {
        background: #f0f4fa;
    }
    .previsao-item .disciplina {
        font-weight: 600;
        color: #0b1a33;
        min-width: 100px;
    }
    .previsao-item .recomendacao {
        color: #2e3b4e;
        font-size: 0.95rem;
    }

    /* ----- FORMULÁRIO E INPUTS ----- */
    .stForm {
        background: transparent;
        padding: 0;
    }
    .stTextInput>div>div>input,
    .stNumberInput>div>div>input,
    .stSelectbox>div>div>select {
        border-radius: 10px;
        border: 1.5px solid #e2e8f0;
        padding: 0.6rem 1rem;
        background: white;
        font-size: 0.95rem;
        transition: border 0.2s, box-shadow 0.2s;
    }
    .stTextInput>div>div>input:focus,
    .stNumberInput>div>div>input:focus {
        border-color: #2a5298;
        box-shadow: 0 0 0 3px rgba(42, 82, 152, 0.12);
    }

    /* ----- BOTÕES COM GRADIENTE E EFEITO ----- */
    .stButton>button {
        background: linear-gradient(135deg, #1d3b66, #2a5298);
        color: white;
        border-radius: 30px;
        padding: 0.6rem 2.2rem;
        font-weight: 500;
        border: none;
        transition: all 0.25s ease;
        box-shadow: 0 4px 12px rgba(42, 82, 152, 0.25);
        letter-spacing: 0.3px;
    }
    .stButton>button:hover {
        transform: scale(1.02);
        box-shadow: 0 6px 20px rgba(42, 82, 152, 0.35);
        background: linear-gradient(135deg, #234b7a, #3366aa);
    }
    .stButton>button:active {
        transform: scale(0.97);
    }

    /* ----- SIDEBAR MODERNA ----- */
    .css-1d391kg {
        background: #ffffff;
        border-right: 1px solid #eef2f7;
        padding: 1.5rem 0.5rem;
    }
    .css-1d391kg .stRadio label {
        font-weight: 500;
        color: #1a2a44;
        padding: 0.5rem 1rem;
        border-radius: 10px;
        transition: background 0.15s;
    }
    .css-1d391kg .stRadio label:hover {
        background: #f0f4fc;
    }
    .css-1d391kg .stRadio label[data-baseweb="radio"] {
        background: transparent;
    }
    .sidebar-footer {
        font-size: 0.8rem;
        color: #8896a8;
        margin-top: 2.5rem;
        text-align: center;
        border-top: 1px solid #eef2f7;
        padding-top: 1.2rem;
        font-weight: 400;
    }
    .sidebar-footer strong {
        color: #1d3b66;
        font-weight: 600;
    }

    /* ----- DATAFRAME (ESTILIZADO) ----- */
    .dataframe {
        border: none !important;
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 2px 10px rgba(0,0,0,0.02);
    }
    .dataframe thead tr th {
        background: #f4f7fc !important;
        color: #1a2a44;
        font-weight: 600;
        border-bottom: 2px solid #dce3ec !important;
        padding: 0.6rem 1rem !important;
    }
    .dataframe tbody tr td {
        border-bottom: 1px solid #eef2f7 !important;
        padding: 0.6rem 1rem !important;
    }
    .dataframe tbody tr:hover td {
        background: #f8faff !important;
    }

    /* ----- ALERTAS E CAIXAS DE INFORMAÇÃO ----- */
    .stAlert {
        border-radius: 10px;
        border: none;
        background: #f8faff;
        border-left: 4px solid #2a5298;
        padding: 0.8rem 1.2rem;
        box-shadow: 0 2px 10px rgba(0,0,0,0.02);
    }
    .stAlert .stAlertContent {
        color: #1a2a44;
    }

    /* ----- RODAPÉ ----- */
    .footer {
        margin-top: 3rem;
        text-align: center;
        color: #a0b0c4;
        font-size: 0.85rem;
        border-top: 1px solid #eef2f7;
        padding-top: 1.8rem;
        letter-spacing: 0.2px;
    }
    .footer span {
        background: #f4f7fc;
        padding: 0.2rem 0.8rem;
        border-radius: 20px;
    }

    /* ----- SPINNER PERSONALIZADO (mantido) ----- */
    .stSpinner > div {
        border-color: #2a5298 !important;
    }

    /* ----- RESPONSIVO (ajustes pequenos) ----- */
    @media (max-width: 768px) {
        .header-left .title-group h1 { font-size: 1.6rem; }
        .header-left .icon { font-size: 2rem; }
        .previsao-item { flex-direction: column; align-items: flex-start; gap: 0.3rem; }
        .badge { font-size: 0.65rem; padding: 0.2rem 0.8rem; }
    }
</style>
""", unsafe_allow_html=True)

# ---- CABEÇALHO (moderno, título e subtítulo na mesma linha) ----
st.markdown("""
<div class="header">
    <div class="header-left">
        <span class="icon">📘</span>
        <div class="title-group">
            <h1>Previsão de Desempenho Académico</h1>
            <p>Análise inteligente de notas e faltas · recomendações personalizadas</p>
        </div>
    </div>
    <div class="badge">🔬 Sistemas Distribuídos · RabbitMQ + SQLite</div>
</div>
""", unsafe_allow_html=True)

# ---- SIDEBAR ----
with st.sidebar:
    st.markdown("### 🧭 Navegação")
    menu = st.radio(
        "",
        ["📝 Registar Dados", "🔍 Consultar Aluno", "📋 Listar Alunos"],
        index=0,
        label_visibility="collapsed"
    )
    st.markdown("---")
    st.markdown("""
    <div style="background:#f4f7fc; border-radius:12px; padding:1rem; margin:0.5rem 0;">
        <p style="font-weight:600; color:#0b1a33; margin:0;">ℹ️ Sobre</p>
        <p style="font-size:0.85rem; color:#3a4a5e; margin:0.3rem 0 0;">
            Sistema distribuído com processamento assíncrono.<br>
            <strong>Versão 1.0</strong> · Mestrado SD
        </p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('<div class="sidebar-footer">© 2025 · Desenvolvido para fins académicos</div>', unsafe_allow_html=True)

API_BASE = "http://localhost:8000"

# ---- MENU 1: REGISTAR ----
if menu == "📝 Registar Dados":
    st.markdown('<div class="section-title">📥 Registar dados do aluno</div>', unsafe_allow_html=True)

    with st.container():
        col_form, col_tip = st.columns([2, 1])
        with col_form:
            with st.form("form_registo", clear_on_submit=False):
                matricula = st.text_input("Matrícula", placeholder="Ex: 2024001")
                nome = st.text_input("Nome completo", placeholder="Ex: Ana Silva")
                disciplina = st.text_input("Código da disciplina", value="MAT101")
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    nota = st.number_input("Nota (0-20)", 0.0, 20.0, step=0.5, value=5.0)
                with col_b:
                    faltas = st.number_input("Faltas", 0, step=1, value=0)
                with col_c:
                    data = st.date_input("Data da avaliação")
                submitted = st.form_submit_button("📤 Registar e prever")

        with col_tip:
            st.markdown("""
            <div class="card" style="padding:1.2rem; background:#f8faff;">
                <p style="font-weight:600; margin:0; color:#0b1a33;">💡 Como funciona</p>
                <ul style="font-size:0.9rem; color:#2e3b4e; padding-left:1.2rem; margin-top:0.3rem;">
                    <li>Média < 5,0 ou faltas > 25% → <strong>risco alto</strong></li>
                    <li>Média entre 5,0 e 6,5 → <strong>risco médio</strong></li>
                    <li>Média ≥ 6,5 → <strong>risco baixo</strong></li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

    if submitted:
        if not matricula or not nome:
            st.error("❌ Preencha a matrícula e o nome.")
        else:
            payload = {
                "matricula": matricula,
                "nome": nome,
                "notas": [{"disciplina_codigo": disciplina, "nota": nota, "faltas": faltas, "data": str(data)}]
            }
            try:
                resp = requests.post(f"{API_BASE}/aluno/dados", json=payload)
                if resp.status_code == 200:
                    st.success("✅ Dados registados com sucesso. A previsão está a ser processada...")

                    with st.spinner("⏳ A calcular a previsão..."):
                        previsao = None
                        timeout = 10
                        interval = 1
                        elapsed = 0
                        while elapsed < timeout:
                            time.sleep(interval)
                            elapsed += interval
                            try:
                                resp_previsao = requests.get(f"{API_BASE}/previsoes/{matricula}")
                                if resp_previsao.status_code == 200:
                                    dados_previsao = resp_previsao.json()
                                    if dados_previsao:
                                        previsao = dados_previsao
                                        break
                            except:
                                pass

                    if previsao:
                        st.markdown("---")
                        st.markdown('<div class="section-title" style="font-size:1.3rem;">🔮 Resultado da previsão</div>', unsafe_allow_html=True)

                        df = pd.DataFrame(previsao)
                        st.dataframe(df, use_container_width=True)

                        for item in previsao:
                            risco = item["risco"].lower()
                            if risco == "alto":
                                st.markdown(f"""
                                <div class="previsao-item">
                                    <span class="risco-alto">⚠️ Alto</span>
                                    <span class="disciplina">{item['disciplina']}</span>
                                    <span class="recomendacao">{item['recomendacao']}</span>
                                </div>
                                """, unsafe_allow_html=True)
                            elif risco == "medio":
                                st.markdown(f"""
                                <div class="previsao-item">
                                    <span class="risco-medio">📊 Médio</span>
                                    <span class="disciplina">{item['disciplina']}</span>
                                    <span class="recomendacao">{item['recomendacao']}</span>
                                </div>
                                """, unsafe_allow_html=True)
                            else:
                                st.markdown(f"""
                                <div class="previsao-item">
                                    <span class="risco-baixo">✅ Baixo</span>
                                    <span class="disciplina">{item['disciplina']}</span>
                                    <span class="recomendacao">{item['recomendacao']}</span>
                                </div>
                                """, unsafe_allow_html=True)
                    else:
                        st.info("⏳ A previsão ainda não está disponível. Consulte mais tarde no menu 'Consultar Aluno'.")
                else:
                    st.error(f"❌ Erro: {resp.status_code} - {resp.text}")
            except Exception as e:
                st.error(f"❌ Erro de conexão: {e}")

# ---- MENU 2: CONSULTAR ----
elif menu == "🔍 Consultar Aluno":
    st.markdown('<div class="section-title">🔍 Consultar previsões de um aluno</div>', unsafe_allow_html=True)

    with st.container():
        col1, col2 = st.columns([2, 1])
        with col1:
            matricula = st.text_input("Matrícula do aluno", placeholder="Ex: 2024001")
            if st.button("🔎 Consultar", type="primary"):
                if not matricula:
                    st.warning("⚠️ Digite uma matrícula.")
                else:
                    try:
                        resp = requests.get(f"{API_BASE}/previsoes/{matricula}")
                        if resp.status_code == 200:
                            dados = resp.json()
                            if dados:
                                st.markdown(f"### 📊 Previsões para a matrícula **{matricula}**")
                                df = pd.DataFrame(dados)
                                st.dataframe(df, use_container_width=True)

                                for item in dados:
                                    risco = item["risco"].lower()
                                    if risco == "alto":
                                        st.markdown(f"""
                                        <div class="previsao-item">
                                            <span class="risco-alto">⚠️ Alto</span>
                                            <span class="disciplina">{item['disciplina']}</span>
                                            <span class="recomendacao">{item['recomendacao']}</span>
                                        </div>
                                        """, unsafe_allow_html=True)
                                    elif risco == "medio":
                                        st.markdown(f"""
                                        <div class="previsao-item">
                                            <span class="risco-medio">📊 Médio</span>
                                            <span class="disciplina">{item['disciplina']}</span>
                                            <span class="recomendacao">{item['recomendacao']}</span>
                                        </div>
                                        """, unsafe_allow_html=True)
                                    else:
                                        st.markdown(f"""
                                        <div class="previsao-item">
                                            <span class="risco-baixo">✅ Baixo</span>
                                            <span class="disciplina">{item['disciplina']}</span>
                                            <span class="recomendacao">{item['recomendacao']}</span>
                                        </div>
                                        """, unsafe_allow_html=True)
                            else:
                                st.info("ℹ️ Nenhuma previsão encontrada para este aluno.")
                        else:
                            st.error("❌ Erro ao buscar previsões.")
                    except Exception as e:
                        st.error(f"❌ Erro: {e}")
        with col2:
            st.markdown("""
            <div class="card" style="padding:1.2rem; background:#f8faff;">
                <p style="font-weight:600; margin:0; color:#0b1a33;">📌 Dica</p>
                <p style="font-size:0.9rem; margin:0.3rem 0 0; color:#2e3b4e;">
                    Se registou um aluno com matrícula <strong>2024001</strong>, digite essa matrícula para ver a previsão.
                </p>
            </div>
            """, unsafe_allow_html=True)

# ---- MENU 3: LISTAR ALUNOS ----
elif menu == "📋 Listar Alunos":
    st.markdown('<div class="section-title">📋 Alunos registados</div>', unsafe_allow_html=True)

    try:
        resp = requests.get(f"{API_BASE}/alunos")
        if resp.status_code == 200:
            alunos = resp.json()
            if alunos:
                df = pd.DataFrame(alunos)
                st.dataframe(df, use_container_width=True)
                st.caption(f"Total de alunos registados: {len(alunos)}")
            else:
                st.info("ℹ️ Nenhum aluno registado ainda.")
        else:
            st.error("❌ Erro ao listar alunos.")
    except Exception as e:
        st.error(f"❌ Erro de conexão: {e}")

# ---- RODAPÉ ----
st.markdown("""
<div class="footer">
    <span>🔬 Sistemas Distribuídos · Mestrado · 2025</span>
</div>
""", unsafe_allow_html=True)