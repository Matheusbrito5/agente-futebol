import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import poisson

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Agente BetMaster Auto", page_icon="🤖", layout="wide")

st.title("🤖 Agente 100% Automático - Banco de Dados Global")
st.markdown("Este agente baixa dados de **11 ligas europeias**, calcula a força de cada time e aplica um **Fator de Correção** para jogos internacionais (Champions/Europa League).")
st.divider()

# --- 1. CONFIGURAÇÃO DAS FONTES DE DADOS (LINKS REAIS) ---
# Temporada atual (24/25). Para 2025/2026, basta mudar o '2425' nos links.
base_url = "https://www.football-data.co.uk/mmz4281/2425/"
extra_url = "https://www.football-data.co.uk/new/" # Ligas menores

data_sources = {
    'Inglaterra 1': {'url': base_url + 'E0.csv', 'peso': 1.00}, # Premier League (Referência)
    'Espanha 1':    {'url': base_url + 'SP1.csv', 'peso': 0.95},
    'Itália 1':     {'url': base_url + 'I1.csv',  'peso': 0.95},
    'Alemanha 1':   {'url': base_url + 'D1.csv',  'peso': 0.92},
    'França 1':     {'url': base_url + 'F1.csv',  'peso': 0.90},
    'Portugal 1':   {'url': base_url + 'P1.csv',  'peso': 0.82}, # Porto, Benfica, Sporting, Braga
    'Holanda 1':    {'url': base_url + 'N1.csv',  'peso': 0.80}, # Ajax, PSV, Feyenoord, Twente
    'Bélgica 1':    {'url': base_url + 'B1.csv',  'peso': 0.78}, # Brugge, Union SG, Anderlecht
    'Turquia 1':    {'url': base_url + 'T1.csv',  'peso': 0.75}, # Galatasaray, Fenerbahce
    'Grécia 1':     {'url': base_url + 'G1.csv',  'peso': 0.72}, # Olympiacos, PAOK
    'Dinamarca 1':  {'url': extra_url + 'DNK.csv', 'peso': 0.70}, # Midtjylland, Copenhague
}

# --- 2. O ROBÔ DE DADOS (ENGINE) ---

@st.cache_data(ttl=3600) # Atualiza a cada 1 hora
def carregar_banco_de_dados():
    todos_times = {}
    status_text = st.empty()
    status_text.text("🔄 Baixando dados das ligas europeias... aguarde.")
    
    progresso = st.progress(0)
    total_ligas = len(data_sources)
    contador = 0

    for liga, info in data_sources.items():
        try:
            # Lê o CSV
            df = pd.read_csv(info['url'], encoding='latin1') # Latin1 evita erro de acentos
            
            # Padroniza colunas (alguns CSVs variam)
            cols = ['HomeTeam', 'AwayTeam', 'FTHG', 'FTAG']
            if all(c in df.columns for c in cols):
                df = df[cols].dropna()
                
                # Calcula médias da liga específica
                media_gols = (df['FTHG'].mean() + df['FTAG'].mean()) / 2
                
                # Lista times únicos dessa liga
                times_liga = set(df['HomeTeam'].unique()) | set(df['AwayTeam'].unique())
                
                for time in times_liga:
                    # Stats do time
                    jogos_h = df[df['HomeTeam'] == time]
                    jogos_a = df[df['AwayTeam'] == time]
                    
                    gols_pro = jogos_h['FTHG'].sum() + jogos_a['FTAG'].sum()
                    gols_sof = jogos_h['FTAG'].sum() + jogos_a['FTHG'].sum()
                    num_jogos = len(jogos_h) + len(jogos_a)
                    
                    if num_jogos > 0:
                        # Força bruta (relativa à própria liga)
                        atk_raw = (gols_pro / num_jogos) / media_gols
                        def_raw = (gols_sof / num_jogos) / media_gols
                        
                        # APLICA O PESO DA LIGA (Crucial para Europa League)
                        # Ex: Ter ataque 2.0 na Dinamarca vale menos que 2.0 na Inglaterra
                        peso = info['peso']
                        atk_real = atk_raw * peso
                        # Defesa: quanto menor melhor. Se a liga é fraca, a defesa "parece" boa, então aumentamos o valor para penalizar
                        def_real = def_raw * (2 - peso) 
                        
                        todos_times[time] = {
                            'atk': atk_real, 
                            'def': def_real, 
                            'liga': liga,
                            'jogos': num_jogos
                        }
        except Exception as e:
            print(f"Erro ao carregar {liga}: {e}")
        
        contador += 1
        progresso.progress(contador / total_ligas)

    status_text.text(f"✅ Concluído! {len(todos_times)} times carregados e analisados.")
    progresso.empty()
    return todos_times

# Carrega tudo
db_times = carregar_banco_de_dados()

# --- 3. INTERFACE DE SELEÇÃO INTELIGENTE ---

if len(db_times) > 0:
    col_sel1, col_sel2 = st.columns(2)
    
    lista_nomes = sorted(db_times.keys())
    
    # Índices padrão (tenta achar Roma e Midtjylland)
    idx_casa = lista_nomes.index('Roma') if 'Roma' in lista_nomes else 0
    # O CSV da dinamarca as vezes usa nomes como 'Midtjylland' ou 'FC Midtjylland'
    matches = [t for t in lista_nomes if "Midt" in t] 
    idx_fora = lista_nomes.index(matches[0]) if matches else 1

    with col_sel1:
        st.subheader("🏠 Mandante")
        time_casa = st.selectbox("Busque o time:", lista_nomes, index=idx_casa)
        info_c = db_times[time_casa]
        st.caption(f"Liga: {info_c['liga']} | Jogos na base: {info_c['jogos']}")
        
    with col_sel2:
        st.subheader("✈️ Visitante")
        time_visitante = st.selectbox("Busque o time:", lista_nomes, index=idx_fora)
        info_v = db_times[time_visitante]
        st.caption(f"Liga: {info_v['liga']} | Jogos na base: {info_v['jogos']}")

    st.markdown("---")

    # --- 4. CÁLCULO E PREVISÃO ---
    
    # Fator Casa (Padrão UEFA: Mandante tem vantagem leve)
    fator_casa = 1.15 
    media_gols_europa = 1.45 # Média de gols em competições europeias

    # Forças
    tc_atk = db_times[time_casa]['atk']
    tc_def = db_times[time_casa]['def']
    tv_atk = db_times[time_visitante]['atk']
    tv_def = db_times[time_visitante]['def']

    # xG (Expected Goals)
    xg_casa = tc_atk * tv_def * media_gols_europa * fator_casa
    xg_fora = tv_atk * tc_def * media_gols_europa

    # Poisson
    max_gols = 8
    matriz = np.zeros((max_gols, max_gols))
    for i in range(max_gols):
        for j in range(max_gols):
            matriz[i][j] = poisson.pmf(i, xg_casa) * poisson.pmf(j, xg_fora)

    prob_vitoria_casa = np.sum(np.tril(matriz, -1))
    prob_empate = np.sum(np.diag(matriz))
    prob_vitoria_fora = np.sum(np.triu(matriz, 1))

    # --- 5. RESULTADOS VISUAIS ---
    
    st.markdown(f"""
    <div style="background-color: #1e1e1e; padding: 15px; border-radius: 10px; text-align: center; border: 1px solid #444;">
        <span style="font-size: 24px; font-weight: bold; color: #fff;">{time_casa}</span>
        <span style="font-size: 20px; color: #888; margin: 0 15px;">vs</span>
        <span style="font-size: 24px; font-weight: bold; color: #fff;">{time_visitante}</span>
        <br><br>
        <span style="font-size: 16px; color: #00ff88;">xG Estimado: <b>{xg_casa:.2f}</b> - <b>{xg_fora:.2f}</b></span>
    </div>
    """, unsafe_allow_html=True)
    
    st.write("")

    col_res1, col_res2, col_res3 = st.columns(3)
    
    # Cores condicionais
    cor_casa = "normal"
    if prob_vitoria_casa > 0.50: cor_casa = "off" # Streamlit destaca metricas com delta

    col_res1.metric("Vitória Casa", f"{prob_vitoria_casa*100:.1f}%", f"Odd Justa: {1/prob_vitoria_casa:.2f}")
    col_res2.metric("Empate", f"{prob_empate*100:.1f}%", f"Odd Justa: {1/prob_empate:.2f}")
    col_res3.metric("Vitória Fora", f"{prob_vitoria_fora*100:.1f}%", f"Odd Justa: {1/prob_vitoria_fora:.2f}")

    # Tabela de Placares
    st.write("")
    with st.expander("🎲 Ver Placares Mais Prováveis"):
        placares = []
        for i in range(6):
            for j in range(6):
                placares.append({'Placar': f"{i} x {j}", 'Prob': matriz[i][j]})
        
        df_placares = pd.DataFrame(placares).sort_values('Prob', ascending=False).head(5)
        df_placares['Prob'] = (df_placares['Prob'] * 100).map('{:.1f}%'.format)
        st.table(df_placares.reset_index(drop=True))

else:
    st.error("Erro crítico: Não foi possível baixar os dados. Verifique a internet.")
