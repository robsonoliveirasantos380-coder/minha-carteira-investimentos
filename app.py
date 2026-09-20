import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Comparador B3 & Simulador Pro", page_icon="⚔️", layout="wide")

st.title("⚔️ Comparador de Ativos & Simulador da B3")
st.markdown("Compare cotações, evolução percentual, proventos acumulados e simule seus rendimentos na bolsa de valores.")

# Menu lateral com dois tickers e filtros
st.sidebar.header("Filtros dos Ativos")

col_t1, col_t2 = st.sidebar.columns(2)
with col_t1:
    ticker1 = st.text_input("Ativo 1:", value="MXRF11.SA").upper()
with col_t2:
    ticker2 = st.text_input("Ativo 2:", value="KNCA11.SA").upper()

periodo = st.sidebar.selectbox("Selecione o Período", ["1mo", "6mo", "1y", "5y", "max"], index=2)

st.sidebar.divider()
st.sidebar.header("🧮 Simulador de Investimento")
valor_investido = st.sidebar.number_input(
    "Valor Investido em CADA Ativo (R$):",
    min_value=100.0,
    max_value=1000000.0,
    value=5000.0,
    step=500.0
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
            st.error("Um dos tickers digitados não retornou dados. Certifique-se de usar o sufixo **.SA** (ex: `MXRF11.SA`, `ITSA4.SA`).")
        else:
            # --- PROCESSAMENTO ATIVO 1 ---
            p_init1, p_atual1 = df1['Close'].iloc[0], df1['Close'].iloc[-1]
            var1 = ((p_atual1 - p_init1) / p_init1) * 100
            div1_p = div1[(div1.index >= df1.index[0]) & (div1.index <= df1.index[-1])] if not div1.empty else pd.Series(dtype=float)
            tot_div1_cota = div1_p.sum()
            cotas1 = valor_investido / p_init1
            tot_div1_rec = cotas1 * tot_div1_cota
            cap_atual1 = cotas1 * p_atual1
            patr1 = cap_atual1 + tot_div1_rec
            lucro1 = patr1 - valor_investido

            # --- PROCESSAMENTO ATIVO 2 ---
            p_init2, p_atual2 = df2['Close'].iloc[0], df2['Close'].iloc[-1]
            var2 = ((p_atual2 - p_init2) / p_init2) * 100
            div2_p = div2[(div2.index >= df2.index[0]) & (div2.index <= df2.index[-1])] if not div2.empty else pd.Series(dtype=float)
            tot_div2_cota = div2_p.sum()
            cotas2 = valor_investido / p_init2
            tot_div2_rec = cotas2 * tot_div2_cota
            cap_atual2 = cotas2 * p_atual2
            patr2 = cap_atual2 + tot_div2_rec
            lucro2 = patr2 - valor_investido

            # --- QUADRO COMPARATIVO DAS SIMULAÇÕES ---
            st.subheader(f"📊 Resultado da Simulação para R$ {valor_investido:,.2f} investidos em cada")

            c1, c2 = st.columns(2)

            with c1:
                st.info(f"### 🔵 {ticker1}")
                st.write(f"**Preço Atual:** R$ {p_atual1:.2f} *(Variação no período: {var1:.2f}%)*")
                st.write(f"**Cotas Compradas:** {cotas1:.0f} cotas")
                st.write(f"**Total Recebido em Dividendos:** R$ {tot_div1_rec:,.2f}")
                st.metric(label="Patrimônio Final Total", value=f"R$ {patr1:,.2f}", delta=f"R$ {lucro1:,.2f}")

            with c2:
                st.success(f"### 🟢 {ticker2}")
                st.write(f"**Preço Atual:** R$ {p_atual2:.2f} *(Variação no período: {var2:.2f}%)*")
                st.write(f"**Cotas Compradas:** {cotas2:.0f} cotas")
                st.write(f"**Total Recebido em Dividendos:** R$ {tot_div2_rec:,.2f}")
                st.metric(label="Patrimônio Final Total", value=f"R$ {patr2:,.2f}", delta=f"R$ {lucro2:,.2f}")

            st.divider()

            # --- ABAS ORGANIZADAS ---
            aba_preco, aba_rentabilidade, aba_div, aba_export = st.tabs([
                "📈 Comparativo de Preço", 
                "🚀 Rentabilidade Acumulada (%)", 
                "💵 Proventos Lado a Lado",
                "📥 Exportação de Dados"
            ])

            with aba_preco:
                fig_p = go.Figure()
                fig_p.add_trace(go.Scatter(x=df1.index, y=df1['Close'], mode='lines', name=ticker1, line=dict(color='#2980b9', width=2)))
                fig_p.add_trace(go.Scatter(x=df2.index, y=df2['Close'], mode='lines', name=ticker2, line=dict(color='#2ecc71', width=2)))
                fig_p.update_layout(title="Histórico de Preços (R$)", xaxis_title="Data", yaxis_title="Preço (R$)")
                st.plotly_chart(fig_p, use_container_width=True)

            with aba_rentabilidade:
                # Normalização para largar de 0%
                df1_norm = ((df1['Close'] / p_init1) - 1) * 100
                df2_norm = ((df2['Close'] / p_init2) - 1) * 100

                fig_r = go.Figure()
                fig_r.add_trace(go.Scatter(x=df1.index, y=df1_norm, mode='lines', name=ticker1, line=dict(color='#2980b9', width=2)))
                fig_r.add_trace(go.Scatter(x=df2.index, y=df2_norm, mode='lines', name=ticker2, line=dict(color='#2ecc71', width=2)))
                fig_r.update_layout(title="Evolução Percentual da Cotação (%)", xaxis_title="Data", yaxis_title="Variação (%)")
                st.plotly_chart(fig_r, use_container_width=True)

            with aba_div:
                st.subheader("Comparativo de Proventos e Dividendos")
                d_col1, d_col2 = st.columns(2)
                
                with d_col1:
                    st.write(f"**Pagamentos do {ticker1}**")
                    if not div1_p.empty:
                        df_d1 = div1_p.reset_index()
                        df_d1.columns = ['Data', 'Por Cota (R$)']
                        df_d1['Total Recebido (R$)'] = df_d1['Por Cota (R$)'] * cotas1
                        st.dataframe(df_d1.sort_values(by='Data', ascending=False), use_container_width=True)
                    else:
                        st.info("Sem lançamentos de dividendos no período.")

                with d_col2:
                    st.write(f"**Pagamentos do {ticker2}**")
                    if not div2_p.empty:
                        df_d2 = div2_p.reset_index()
                        df_d2.columns = ['Data', 'Por Cota (R$)']
                        df_d2['Total Recebido (R$)'] = df_d2['Por Cota (R$)'] * cotas2
                        st.dataframe(df_d2.sort_values(by='Data', ascending=False), use_container_width=True)
                    else:
                        st.info("Sem lançamentos de dividendos no período.")

            with aba_export:
                st.subheader("Baixar Relatórios da Comparação em CSV")
                ex_col1, ex_col2 = st.columns(2)

                with ex_col1:
                    st.write(f"**Histórico de Cotações - {ticker1}**")
                    csv1 = df1.to_csv().encode('utf-8')
                    st.download_button(
                        label=f"📥 Baixar CSV - {ticker1}",
                        data=csv1,
                        file_name=f"historico_{ticker1}.csv",
                        mime="text/csv"
                    )

                with ex_col2:
                    st.write(f"**Histórico de Cotações - {ticker2}**")
                    csv2 = df2.to_csv().encode('utf-8')
                    st.download_button(
                        label=f"📥 Baixar CSV - {ticker2}",
                        data=csv2,
                        file_name=f"historico_{ticker2}.csv",
                        mime="text/csv"
                    )

    except Exception as e:
        st.error(f"Ocorreu um erro ao processar a comparação: {e}")