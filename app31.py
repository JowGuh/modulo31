import numpy as np
import pandas as pd
import streamlit as st
from datetime import datetime
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import plotly.express as px
import io


@st.cache_data
def load_data(file):
    return pd.read_csv(file, infer_datetime_format=True, parse_dates=['DiaCompra'])


def recencia_class(x, q_dict):
    if x <= q_dict[0.25]:
        return 'A'
    elif x <= q_dict[0.50]:
        return 'B'
    elif x <= q_dict[0.75]:
        return 'C'
    else:
        return 'D'


def freq_val_class(x, q_dict):
    if x <= q_dict[0.25]:
        return 'D'
    elif x <= q_dict[0.50]:
        return 'C'
    elif x <= q_dict[0.75]:
        return 'B'
    else:
        return 'A'

st.title('Análise RFV (Recência, Frequência, Valor) com K-Means')

uploaded_file = st.file_uploader("Escolha o arquivo CSV", type="csv")

if uploaded_file is not None:
    df_compras = load_data(uploaded_file)

    st.subheader("Pré-visualização dos dados:")
    st.dataframe(df_compras.head())

    cliente_coluna = 'ID_cliente'

    if cliente_coluna in df_compras.columns:
        df_RFV = df_compras.copy()

        
        df_RFV['Recencia'] = (datetime.now() - df_RFV['DiaCompra']).dt.days
        df_RFV['Frequencia'] = df_RFV.groupby(cliente_coluna)['DiaCompra'].transform('count')
        df_RFV['Valor'] = df_RFV.groupby(cliente_coluna)['ValorTotal'].transform('sum')

        df_RFV = df_RFV[[cliente_coluna, 'Recencia', 'Frequencia', 'Valor']].drop_duplicates()

        quartis = df_RFV[['Recencia', 'Frequencia', 'Valor']].quantile([0.25, 0.50, 0.75])

        df_RFV['R_quartil'] = df_RFV['Recencia'].apply(recencia_class, args=(quartis['Recencia'],))
        df_RFV['F_quartil'] = df_RFV['Frequencia'].apply(freq_val_class, args=(quartis['Frequencia'],))
        df_RFV['V_quartil'] = df_RFV['Valor'].apply(freq_val_class, args=(quartis['Valor'],))

        df_RFV['RFV_Score'] = df_RFV['R_quartil'] + df_RFV['F_quartil'] + df_RFV['V_quartil']

        
        dict_acoes = {
            'AAA': 'Enviar cupons, pedir indicação, enviar amostras grátis.',
            'DDD': 'Churn! Pouco valor/frequência. Não fazer nada.',
            'DAA': 'Churn! Gasto alto, tentar recuperar com desconto.',
            'CAA': 'Churn! Gasto alto, tentar recuperar com desconto.'
        }
        df_RFV['ações de marketing/crm'] = df_RFV['RFV_Score'].map(dict_acoes)

        st.subheader("Tabela RFV com recomendações:")
        st.dataframe(df_RFV)

        
        st.subheader("Clustering com K-Means")
        n_clusters = st.slider("Escolha o número de clusters", 2, 10, 4)

        
        scaler = StandardScaler()
        rfv_scaled = scaler.fit_transform(df_RFV[['Recencia', 'Frequencia', 'Valor']])

        
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        df_RFV['Cluster'] = kmeans.fit_predict(rfv_scaled)

        
        fig = px.scatter_3d(
            df_RFV, x='Recencia', y='Frequencia', z='Valor',
            color=df_RFV['Cluster'].astype(str),
            title="Clusters de Clientes (K-Means)",
            hover_data=[cliente_coluna, 'RFV_Score']
        )
        st.plotly_chart(fig)

        
        st.subheader("Download dos resultados")
        output = io.BytesIO()
        df_RFV.to_excel(output, index=False, engine='openpyxl')
        st.download_button(
            label="Baixar Excel com clusters",
            data=output,
            file_name="RFV_com_Clusters.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.error(f"A coluna '{cliente_coluna}' não foi encontrada no arquivo.")
