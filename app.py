import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import poisson
import requests
from bs4 import BeautifulSoup
import difflib

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Agente BetMaster VIP", page_icon="💎", layout="wide")

st.title("💎 Agente Dixon-Coles (Com Times Extras)")
st.markdown("Agora inclui **Midtjylland, Porto, Ajax** e outros times da Liga Europa forçados no sistema.")

# --- 1. BANCO DE DADOS HÍBRIDO ---
base_url = "https://www.football-data.co.uk/mmz4281/2425/"

data_sources = {
    'Inglaterra 1': {'url': base_url + 'E0.csv', 'peso': 1.00},
    'Espanha 1':    {'url': base_url + 'SP1.csv', 'peso': 0.95},
    'Itália 1':     {'url': base_url + 'I1.csv',  'peso': 0.92},
    'Alemanha 1':   {'url': base_url + 'D1.csv',  'peso': 0.92},
    'França 1':     {'url': base_url + 'F1.csv',  'peso': 0.88},
    'Portugal 1':   {'url': base_url + 'P1.csv',  'peso': 0.82},
    'Holanda 1':    {'url': base_url + 'N1.csv',  'peso': 0.80},
}

@st.cache_data(ttl=3600)
def carregar_banco_de_dados():
    todos_times = {}
    
    # 1. Tenta baixar automático da Europa Principal
    for liga, info in data_sources.items():
        try:
            df = pd.read_csv(info['url'], encoding='latin1')
            cols = ['HomeTeam', 'AwayTeam', 'FTHG', 'FTAG']
            if all(c in df.columns for c in cols):
                df = df[cols].dropna()
                media_gols = (df['FTHG'].mean() + df['FTAG'].mean()) / 2
                times_liga = set(df['HomeTeam'].unique()) | set(df['AwayTeam'].unique())
                
                for time in times_liga:
                    jogos_h = df[df['HomeTeam'] == time]
                    jogos_a = df[df['AwayTeam'] == time]
                    num = len(jogos_h) + len(jogos_a)
                    if num > 0:
                        gp = jogos_h['FTHG'].sum() + jogos_a['FTAG'].sum()
                        gs = jogos_h['FTAG'].sum() + jogos_a['FTHG'].sum()
                        atk = ((gp/num) / media_gols) * info['peso']
                        defn = ((gs/num) / media_gols) * (2 - info['peso'])
                        todos_times[time] = {'atk': atk, 'def': defn, 'liga': liga, 'jogos': num}
        except: pass

    # 2. INJEÇÃO DE TIMES (Correção para Liga Europa/Conference/Brasileirão)
    # Aqui garantimos que Roma e Midtjylland existam mesmo se o CSV falhar
    times_extras = {
        # Liga Europa / Conference (Ajustados Peso da Liga)
        'Roma':        {'atk': 1.45, 'def': 1.15, 'liga': 'Serie A (Force)'}, 
        'Midtjylland': {'atk': 1.25, 'def': 1.30, 'liga': 'Dinamarca (Force)'}, # Ataque bom, defesa fraca pra nível europeu
        'Porto':       {'atk': 1.60, 'def': 0.90, 'liga': 'Portugal (Force)'},
        'Ajax':        {'atk': 1.55, 'def': 1.10, 'liga': 'Holanda (Force)'},
        'Man Utd':     {'atk': 1.45, 'def': 1.35, 'liga': 'Premier (Force)'},
        'Tottenham':   {'atk': 1.70, 'def': 1.25, 'liga': 'Premier (Force)'},
        'Lazio':       {'atk': 1.65, 'def': 1.10, 'liga': 'Serie A (Force)'},
        'Rangers':     {'atk': 1.20, 'def': 1.30, 'liga': 'Escócia (Force)'},
        'Fenerbahce':  {'atk': 1.50, 'def': 1.20, 'liga': 'Turquia (Force)'},
        'Galatasaray': {'atk': 1.75, 'def': 1.40, 'liga': 'Turquia (Force)'},
        'Braga':       {'atk': 1.35, 'def': 1.25, 'liga': 'Portugal (Force)'},
        'Nice':        {'atk': 1.30, 'def': 0.95, 'liga': 'França (Force)'},
        
        # Brasileirão (Fim de temporada)
        'Botafogo':    {'atk': 1.80, 'def': 0.75, 'liga': 'Brasil'},
        'Palmeiras':   {'atk': 1.70, 'def': 0.70, 'liga': 'Brasil'},
        'Flamengo':    {'atk': 1.65, 'def': 0.85, 'liga': 'Brasil'},
        'Fortaleza':   {'atk': 1.50, 'def': 0.85, 'liga': 'Brasil'},
    }
    
    # Atualiza o banco de dados (se já existir, sobrescreve com o manual que é seguro)
    todos_times.update(times_extras)
    
    return todos_times

db_times = carregar_banco_de_dados()
lista_db = sorted(db_times.keys())

# --- 2. DIXON-COLES (Matemática) ---
def dixon_coles_simulator(xg_home, xg_away):
    rho = -0.13 
    max_gols = 8
    probs = np.zeros((max_gols, max_gols))
    for i in range(max_gols):
        for j in range(max_gols):
            probs[i][j] = poisson.pmf(i, xg_home) * poisson.pmf(j, xg_away)
    
    def adjustment(i, j, mu_h, mu_a):
        if i == 0 and j == 0: return 1 - (mu_h * mu_a * rho)
        if i == 0 and j == 1: return 1 + (mu_h * rho)
        if i == 1 and j == 0: return 1 + (mu_a * rho)
        if i == 1 and j == 1: return 1 - rho
        return 1.0

    for i in range(2):
        for j in range(2):
            factor = adjustment(i, j, xg_home, xg_away)
            probs[i][j] = probs[i][j] * factor
            
    return probs / np.sum(probs)

# --- 3. INTERFACE ---
st.sidebar.header("🕹️ Opções")
modo = st.sidebar.radio("Escolha o Modo:", ["Seleção Manual", "Criar Time Novo"])

if modo == "Seleção Manual":
    c1, c2 = st.columns(2)
    
    # Tenta pré-selecionar Roma e Midtjylland
    idx_roma = lista_db.index('Roma') if 'Roma' in lista_db else 0
    # Procura algo parecido com Midtjylland
    matches_midt = [t for t in lista_db if "Midt" in t]
    idx_midt = lista_db.index(matches_midt[0]) if matches_midt else 1

    with c1:
        tc = st.selectbox("Time da Casa", lista_db, index=idx_roma)
    with c2:
        tv = st.selectbox("Time Visitante", lista_db, index=idx_midt)

    if st.button("🔮 Simular Jogo", type="primary"):
        ic = db_times[tc]
        iv = db_times[tv]
        
        # Fator Casa 1.15 e Média Gols 1.45 (Padrão Europa)
        xg_h = ic['atk'] * iv['def'] * 1.45 * 1.15
        xg_a = iv['atk'] * ic['def'] * 1.45
        
        matriz = dixon_coles_simulator(xg_h, xg_a)
        ph = np.sum(np.tril(matriz, -1))
        pd = np.sum(np.diag(matriz))
        pa = np.sum(np.triu(matriz, 1))
        
        # Exibição
        st.divider()
        st.markdown(f"<h2 style='text-align: center'>{tc} x {tv}</h2>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align: center; color: gray'>xG: {xg_h:.2f} - {xg_a:.2f}</p>", unsafe_allow_html=True)
        
        col_odds1, col_odds2, col_odds3 = st.columns(3)
        col_odds1.metric(f"Vitória {tc}", f"{ph*100:.1f}%", f"Odd: {1/ph:.2f}")
        col_odds2.metric("Empate", f"{pd*100:.1f}%", f"Odd: {1/pd:.2f}")
        col_odds3.metric(f"Vitória {tv}", f"{pa*100:.1f}%", f"Odd: {1/pa:.2f}")

elif modo == "Criar Time Novo":
    st.warning("Não achou o time na lista? Crie ele aqui rapidinho.")
    nome_novo = st.text_input("Nome do Time", "Ludogorets")
    f_atk = st.slider("Força de Ataque (1.0 = Média)", 0.5, 3.0, 1.2)
    f_def = st.slider("Força de Defesa (Quanto MENOR melhor)", 0.1, 2.0, 1.1)
    
    st.markdown("---")
    st.markdown(f"**Adversário (Existente no Banco de Dados):**")
    adv = st.selectbox("Escolha o oponente", lista_db, index=lista_db.index('Roma') if 'Roma' in lista_db else 0)
    
    if st.button("Simular com Time Criado"):
        # Dados do time criado
        xg_h = f_atk * db_times[adv]['def'] * 1.45 * 1.15 # Novo time em CASA
        xg_a = db_times[adv]['atk'] * f_def * 1.45       # Oponente FORA
        
        matriz = dixon_coles_simulator(xg_h, xg_a)
        ph = np.sum(np.tril(matriz, -1))
        
        st.success(f"Simulação: {nome_novo} (Casa) vs {adv} (Fora)")
        st.metric(f"Vitória {nome_novo}", f"{ph*100:.1f}%", f"Odd Justa: {1/ph:.2f}")
