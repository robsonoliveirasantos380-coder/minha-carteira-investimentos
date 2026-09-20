import io
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf

# 1. Configuração da página (DEVE SER O PRIMEIRO COMANDO STREAMLIT)
st.set_page_config(
    page_title="Comparador B3 & Simulador Pro",
    page_icon="⚔️",
    layout="wide",
)


# --- ESTILIZAÇÃO CSS CUSTOMIZADA ---
def apply_custom_css():
    st.markdown(
        """
        <style>
        .stApp {
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            color: #f8fafc;
        }

        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}

        .stTextInput > div > div > input {
            background-color: #334155 !important;
            color: #ffffff !important;
            border-radius: 8px !important;
            border: 1px solid #475569 !important;
            padding: 10px 14px !important;
            font-size: 15px !important;
        }

        .stTextInput > div > div > input:focus {
            border-color: #3b82f6 !important;
            box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.3) !important;
        }

        .stTextInput label {
            color: #cbd5e1 !important;
            font-weight: 500 !important;
        }

        .stButton > button, div[data-testid="stFormSubmitButton"] > button {
            width: 100% !important;
            background: linear-gradient(90deg, #2563eb 0%, #1d4ed8 100%) !important;
            color: #ffffff !important;
            font-weight: 600 !important;
            font-size: 16px !important;
            border-radius: 8px !important;
            padding: 10px 0 !important;
            border: none !important;
            transition: all 0.3s ease !important;
            margin-top: 10px !important;
        }

        .stButton > button:hover, div[data-testid="stFormSubmitButton"] > button:hover {
            background: linear-gradient(90deg, #1d4ed8 0%, #1e40af 100%) !important;
            transform: translateY(-1px) !important;
        }

        .stAlert {
            border-radius: 8px !important;
            background-color: rgba(239, 68, 68, 0.15) !important;
            border: 1px solid #ef4444 !important;
        }
        </style>
    """,
        unsafe_allow_html=True,
    )


apply_custom_css()


# --- GERENCIAMENTO DE SESSÃO E AUTH ---
def check_password():
    """Retorna True se o usuário/senha estiverem corretos."""

    def password_entered():
        """Verifica se a senha digitada confere com os secrets."""
        passwords = st.secrets.get("passwords", {})
        user = st.session_state.get("login_username_key", "")
        pwd = st.session_state.get("login_password_key", "")

        if user in passwords and pwd == passwords[user]:
            st.session_state["password_correct"] = True
            del st.session_state["login_password_key"]  # Remove senha da memória
            del st.session_state["login_username_key"]
        else:
            st.session_state["password_correct"] = False

    if st.session_state.get("password_correct", False):
        return True

    # Renderiza formulário de Login
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(
            """
            <div style="text-align: center; padding: 20px 0 10px 0;">
                <h1 style="font-size: 42px; margin-bottom: 0;">📊</h1>
                <h2 style="color: #ffffff; font-size: 24px; font-weight: 700; margin-top: 10px; margin-bottom: 5px;">
                    Portal de Investimentos
                </h2>
                <p style="color: #94a3b8; font-size: 14px; margin-bottom: 25px;">
                    Acesse sua carteira para simular e analisar ativos
                </p>
            </div>
        """,
            unsafe_allow_html=True,
        )

        st.subheader("🔒 Acesso Restrito")
        with st.form("form_login_auth_unique"):
            st.text_input("Usuário", key="login_username_key")
            st.text_input("Senha", type="password", key="login_password_key")
            st.form_submit_button("Entrar", on_click=password_entered)

        if "password_correct" in st.session_state and not st.session_state["password_correct"]:
            st.error("😕 Usuário ou senha incorretos")

    return False


def logout():
    st.session_state["password_correct"] = False
    st.rerun()


# Interrompe a execução caso o usuário não esteja logado
if not check_password():
    st.stop()


# --- FUNÇÕES AUXILIARES DE EXPORTAÇÃO ---
def format_df_for_excel(df):
    df_copy = df.copy()
    if isinstance(df_copy.index, pd.DatetimeIndex):
        df_copy.index = df_copy.index.tz_localize(None)
    for col in df_copy.select_dtypes(
        include=["datetimetz", "datetime64[ns, UTC]"]
    ).columns:
        df_copy[col] = df_copy[col].dt.tz_localize(None)
    return df_copy


def to_excel(df1, df2, ticker1, ticker2):
    output = io.BytesIO()
    df1_clean = format_df_for_excel(df1)
    df2_clean = format_df_for_excel(df2)
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df1_clean.to_excel(writer, sheet_name=ticker1[:10])
        df2_clean.to_excel(writer, sheet_name=ticker2[:10])
    return output.getvalue()


# --- BARRA LATERAL (Filtros e Configurações) ---
st.sidebar.write("👋 **Bem-vindo(a)!**")
st.sidebar.button("Sair (Logout)", on_click=logout, key="btn_logout_unique")

st.sidebar.divider()
st.sidebar.header("Filtros dos Ativos")

col_t1, col_t2 = st.sidebar.columns(2)
with col_t1:
    ticker1 = st.sidebar.text_input("Ativo 1:", value="MXRF11.SA", key="ticker1_input").upper()
with col_t2:
    ticker2 = st.sidebar.text_input("Ativo 2:", value="KNCA11.SA", key="ticker2_input").upper()

periodo = st.sidebar.selectbox(
    "Selecione o Período", ["1mo", "6mo", "1y", "5y", "max"], index=2, key="periodo_input"
)

st.sidebar.divider()
st.sidebar.header("🧮 Simulador de Investimento")
valor_investido = st.sidebar.number_input(
    "Valor Investido em CADA Ativo (R$):",
    min_value=100.0,
    max_value=1000000.0,
    value=5000.0,
    step=500.0,
    key="valor_investido_input",
)

# --- CORPO PRINCIPAL DO PAINEL ---
st.title("⚔️ Comparador de Ativos & Simulador da B3")
st.markdown(
    "Compare cotações, evolução percentual, proventos acumulados e simule seus rendimentos na bolsa de valores."
)


@st.cache_data(ttl=3600)
def carregar_dados(ticker, perf):
    ativo = yf.Ticker(ticker)
    df = ativo.history(period=perf)
    div = ativo.dividends
    info = ativo.info
    return df, div, info


if ticker1 and ticker2:
    try:
        with st.spinner(f"Buscando dados de {ticker1} e {ticker2}..."):
            df1, div1, info1 = carregar_dados(ticker1, periodo)
            df2, div2, info2 = carregar_dados(ticker2, periodo)

        if df1.empty or df2.empty:
            st.error(
                "Um dos tickers digitados não retornou dados. Certifique-se de usar o sufixo **.SA** (ex: `MXRF11.SA`, `ITSA4.SA`)."
            )
        else:
            p_init1, p_atual1 = df1["Close"].iloc[0], df1["Close"].iloc[-1]
            var1 = ((p_atual1 - p_init1) / p_init1) * 100
            div1_p = (
                div1[(div1.index >= df1.index[0]) & (div1.index <= df1.index[-1])]
                if not div1.empty
                else pd.Series(dtype=float)
            )
            tot_div1_cota = div1_p.sum()
            cotas1 = valor_investido / p_init1
            tot_div1_rec = cotas1 * tot_div1_cota
            cap_atual1 = cotas1 * p_atual1
            patr1 = cap_atual1 + tot_div1_rec
            lucro1 = patr1 - valor_investido

            p_init2, p_atual2 = df2["Close"].iloc[0], df2["Close"].iloc[-1]
            var2 = ((p_atual2 - p_init2) / p_init2) * 100
            div2_p = (
                div2[(div2.index >= df2.index[0]) & (div2.index <= df2.index[-1])]
                if not div2.empty
                else pd.Series(dtype=float)
            )
            tot_div2_cota = div2_p.sum()
            cotas2 = valor_investido / p_init2
            tot_div2_rec = cotas2 * tot_div2_cota
            cap_atual2 = cotas2 * p_atual2
            patr2 = cap_atual2 + tot_div2_rec
            lucro2 = patr2 - valor_investido

            st.subheader(
                f"📊 Resultado da Simulação para R$ {valor_investido:,.2f} investidos em cada"
            )

            c1, c2 = st.columns(2)

            with c1:
                st.info(f"### 🔵 {ticker1}")
                st.write(
                    f"**Preço Atual:** R$ {p_atual1:.2f} *(Variação no período: {var1:.2f}%)*"
                )
                st.write(f"**Cotas Compradas:** {cotas1:.0f} cotas")
                st.write(
                    f"**Total Recebido em Dividendos:** R$ {tot_div1_rec:,.2f}"
                )
                st.metric(
                    label="Patrimônio Final Total",
                    value=f"R$ {patr1:,.2f}",
                    delta=f"R$ {lucro1:,.2f}",
                )

            with c2:
                st.success(f"### 🟢 {ticker2}")
                st.write(
                    f"**Preço Atual:** R$ {p_atual2:.2f} *(Variação no período: {var2:.2f}%)*"
                )
                st.write(f"**Cotas Compradas:** {cotas2:.0f} cotas")
                st.write(
                    f"**Total Recebido em Dividendos:** R$ {tot_div2_rec:,.2f}"
                )
                st.metric(
                    label="Patrimônio Final Total",
                    value=f"R$ {patr2:,.2f}",
                    delta=f"R$ {lucro2:,.2f}",
                )

            st.divider()

            aba_preco, aba_rentabilidade, aba_div, aba_export = st.tabs([
                "📈 Comparativo de Preço",
                "🚀 Rentabilidade Acumulada (%)",
                "💵 Proventos Lado a Lado",
                "📥 Exportação de Dados",
            ])

            with aba_preco:
                fig_p = go.Figure()
                fig_p.add_trace(
                    go.Scatter(
                        x=df1.index,
                        y=df1["Close"],
                        mode="lines",
                        name=ticker1,
                        line=dict(color="#2980b9", width=2),
                    )
                )
                fig_p.add_trace(
                    go.Scatter(
                        x=df2.index,
                        y=df2["Close"],
                        mode="lines",
                        name=ticker2,
                        line=dict(color="#2ecc71", width=2),
                    )
                )
                fig_p.update_layout(
                    title="Histórico de Preços (R$)",
                    xaxis_title="Data",
                    yaxis_title="Preço (R$)",
                )
                st.plotly_chart(fig_p, use_container_width=True)

            with aba_rentabilidade:
                df1_norm = ((df1["Close"] / p_init1) - 1) * 100
                df2_norm = ((df2["Close"] / p_init2) - 1) * 100

                fig_r = go.Figure()
                fig_r.add_trace(
                    go.Scatter(
                        x=df1.index,
                        y=df1_norm,
                        mode="lines",
                        name=ticker1,
                        line=dict(color="#2980b9", width=2),
                    )
                )
                fig_r.add_trace(
                    go.Scatter(
                        x=df2.index,
                        y=df2_norm,
                        mode="lines",
                        name=ticker2,
                        line=dict(color="#2ecc71", width=2),
                    )
                )
                fig_r.update_layout(
                    title="Evolução Percentual da Cotação (%)",
                    xaxis_title="Data",
                    yaxis_title="Variação (%)",
                )
                st.plotly_chart(fig_r, use_container_width=True)

            with aba_div:
                st.subheader("Comparativo de Proventos e Dividendos")
                d_col1, d_col2 = st.columns(2)

                with d_col1:
                    st.write(f"**Pagamentos do {ticker1}**")
                    if not div1_p.empty:
                        df_d1 = div1_p.reset_index()
                        df_d1.columns = ["Data", "Por Cota (R$)"]
                        df_d1["Total Recebido (R$)"] = (
                            df_d1["Por Cota (R$)"] * cotas1
                        )
                        st.dataframe(
                            df_d1.sort_values(by="Data", ascending=False),
                            use_container_width=True,
                        )
                    else:
                        st.info(
                            "Sem lançamentos de dividendos no período."
                        )

                with d_col2:
                    st.write(f"**Pagamentos do {ticker2}**")
                    if not div2_p.empty:
                        df_d2 = div2_p.reset_index()
                        df_d2.columns = ["Data", "Por Cota (R$)"]
                        df_d2["Total Recebido (R$)"] = (
                            df_d2["Por Cota (R$)"] * cotas2
                        )
                        st.dataframe(
                            df_d2.sort_values(by="Data", ascending=False),
                            use_container_width=True,
                        )
                    else:
                        st.info(
                            "Sem lançamentos de dividendos no período."
                        )

            with aba_export:
                st.subheader("Baixar Relatórios da Comparação")
                ex_col1, ex_col2, ex_col3 = st.columns(3)

                with ex_col1:
                    st.write(f"**Histórico CSV - {ticker1}**")
                    csv1 = df1.to_csv().encode("utf-8")
                    st.download_button(
                        label=f"📥 Baixar CSV - {ticker1}",
                        data=csv1,
                        file_name=f"historico_{ticker1}.csv",
                        mime="text/csv",
                    )

                with ex_col2:
                    st.write(f"**Histórico CSV - {ticker2}**")
                    csv2 = df2.to_csv().encode("utf-8")
                    st.download_button(
                        label=f"📥 Baixar CSV - {ticker2}",
                        data=csv2,
                        file_name=f"historico_{ticker2}.csv",
                        mime="text/csv",
                    )

                with ex_col3:
                    st.write("**Relatório Completo Excel (.xlsx)**")
                    excel_data = to_excel(df1, df2, ticker1, ticker2)
                    st.download_button(
                        label="📥 Baixar Excel Completo",
                        data=excel_data,
                        file_name="relatorio_investimentos.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )

    except Exception as e:
        st.error(f"Ocorreu um erro ao processar a comparação: {e}")