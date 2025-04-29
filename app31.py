import numpy as np
import pandas as pd
import streamlit as st
from datetime import datetime
import os


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


st.title('Análise RFV (Recência, Frequência, Valor)')


uploaded_file = st.file_uploader("Escolha o arquivo CSV", type="csv")

if uploaded_file is not None:
    df_compras = load_data(uploaded_file)
    
    st.write("Exibindo as primeiras 20 linhas dos dados:")
    st.dataframe(df_compras.head(20))

    
    st.write("Colunas disponíveis no arquivo CSV:")
    st.write(df_compras.columns.tolist())

    
    cliente_coluna = st.selectbox('Selecione a coluna de identificação do cliente:', df_compras.columns)
    valor_coluna = st.selectbox('Selecione a coluna de valor da compra:', df_compras.columns)

    if cliente_coluna and valor_coluna:
        
        df_RFV = df_compras.copy()

        
        df_RFV['Recencia'] = (datetime.now() - df_RFV['DiaCompra']).dt.days
        df_RFV['Frequencia'] = df_RFV.groupby(cliente_coluna)['DiaCompra'].transform('count')
        df_RFV['Valor'] = df_RFV.groupby(cliente_coluna)[valor_coluna].transform('sum')

        
        quartis = df_RFV[['Recencia', 'Frequencia', 'Valor']].quantile([0.25, 0.50, 0.75])

        
        df_RFV['R_quartil'] = df_RFV['Recencia'].apply(recencia_class, args=(quartis['Recencia'],))
        df_RFV['F_quartil'] = df_RFV['Frequencia'].apply(freq_val_class, args=(quartis['Frequencia'],))
        df_RFV['V_quartil'] = df_RFV['Valor'].apply(freq_val_class, args=(quartis['Valor'],))

        
        dict_acoes = {
            'AAA': 'Enviar cupons de desconto, pedir indicações e enviar amostras grátis.',
            'DDD': 'Churn! Pouco gasto e poucas compras, provavelmente não vale o esforço.',
            'DAA': 'Churn! Gastou bastante e comprou bastante, tentar recuperar com desconto.',
            'CAA': 'Churn! Gastou bastante e comprou bastante, tentar recuperar com desconto.'
        }

        df_RFV['RFV_Score'] = df_RFV['R_quartil'] + df_RFV['F_quartil'] + df_RFV['V_quartil']
        df_RFV['ações de marketing/crm'] = df_RFV['RFV_Score'].map(dict_acoes)

       
        st.write("Resultados da análise RFV:")
        st.dataframe(df_RFV[[cliente_coluna, 'Recencia', 'Frequencia', 'Valor', 'R_quartil', 'F_quartil', 'V_quartil', 'RFV_Score', 'ações de marketing/crm']].drop_duplicates(subset=[cliente_coluna]).head(20))

        
        os.makedirs('./output', exist_ok=True)

        
        output_path = './output/RFV.xlsx'
        df_saida = df_RFV[[cliente_coluna, 'Recencia', 'Frequencia', 'Valor', 'R_quartil', 'F_quartil', 'V_quartil', 'RFV_Score', 'ações de marketing/crm']].drop_duplicates(subset=[cliente_coluna])
        df_saida.to_excel(output_path, index=False)

        with open(output_path, 'rb') as f:
            st.download_button(
                label="Baixar resultados em Excel",
                data=f,
                file_name="RFV_Analisados.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    else:
        st.error("Por favor, selecione as colunas corretamente.")
