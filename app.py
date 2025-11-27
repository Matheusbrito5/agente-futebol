import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import poisson
import requests
from bs4 import BeautifulSoup
import difflib

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="BetMaster Global Elite", page_icon="🌎", layout="wide")

st.title("🌎 Agente Global - Odds & Gols")
st.markdown("""
**Cobertura:** Europa (Automático) + Gigantes do Mundo (Brasil, Argentina, EUA, Arábia).
**Novidade:** Probabilidades de Gols (Over/Under) e Ambos Marcam.
""")

# --- 1. BANCO DE DADOS HÍBRIDO ---
# Links para CSVs da Europa (Temporada 24/25)
base_url = "https://www.football-data.co.uk/mmz4281/2425/"
extra_url = "https://www.football-data.co.uk/new/"

data_sources = {
    '🇬🇧 Premier League': {'url': base_url + 'E0.csv', 'peso': 1.00},
    '🇪🇸 La Liga':        {'url': base_url + 'SP1.csv', 'peso': 0.95},
    '🇮🇹 Serie A':        {'url': base_url + 'I1.csv',  'peso': 0.90},
    '🇩🇪 Bundesliga':     {'url': base_url + 'D1.csv',  'peso': 0.92},
    '🇫🇷 Ligue 1':        {'url': base_url + 'F1.csv',  'peso': 0.88},
    '🇵🇹 Liga Portugal':  {'url': base_url + 'P1.csv',  'peso': 0.82},
    '🇳🇱 Eredivisie':     {'url': base_url + 'N1.csv',  'peso': 0.80},
    '🇹🇷 Turquia':        {'url': base_url + 'T1.csv',  'peso': 0.78},
    '🇧🇪 Bélgica':        {'url': base_url + 'B1.csv',  'peso': 0.78},
    '🇬🇷 Grécia':         {'url': base_url + 'G1.csv',  'peso': 0.75},
}

# --- BANCO DE DADOS MANUAL (RESTO DO MUNDO) ---
# Times calibrados manualmente para 2025. 
# Atk > 1.0 = Bom | Def < 1.0 = Boa
world_giants = {
    # 🇧🇷 BRASIL
    'Botafogo (BRA)': {'atk': 1.85, 'def': 0.75, 'liga': 'Brasileirão'},
    'Palmeiras (BRA)': {'atk': 1.75, 'def': 0.70, 'liga': 'Brasileirão'},
    'Flamengo (BRA)': {'atk': 1.70, 'def': 0.85, 'liga': 'Brasileirão'},
    'Fortaleza (BRA)': {'atk': 1.60, 'def': 0.90, 'liga': 'Brasileirão'},
    'Internacional (BRA)': {'atk': 1.55, 'def': 0.80, 'liga': 'Brasileirão'},
    'São Paulo (BRA)': {'atk': 1.40, 'def': 0.90, 'liga': 'Brasileirão'},
    'Atlético-MG (BRA)': {'atk': 1.50, 'def': 1.10, 'liga': 'Brasileirão'},
    'Corinthians (BRA)': {'atk': 1.45, 'def': 1.05, 'liga': 'Brasileirão'},
    'Cruzeiro (BRA)': {'atk': 1.35, 'def': 0.95, 'liga': 'Brasileirão'},
    'Vasco (BRA)': {'atk': 1.30, 'def': 1.20, 'liga': 'Brasileirão'},
    
    # 🇦🇷 ARGENTINA
    'River Plate (ARG)': {'atk': 1.65, 'def': 0.80, 'liga': 'Argentina'},
    'Boca Juniors (ARG)': {'atk': 1.45, 'def': 0.90, 'liga': 'Argentina'},
    'Racing (ARG)': {'atk': 1.60, 'def': 1.00, 'liga': 'Argentina'},
    
    # 🇺🇸 MLS / 🇲🇽 MÉXICO
    'Inter Miami (USA)': {'atk': 2.10, 'def': 1.40, 'liga': 'MLS'}, # Ataque absurdo, defesa fraca
    'LAFC (USA)': {'atk': 1.80, 'def': 1.10, 'liga': 'MLS'},
    'Club América (MEX)': {'atk': 1.70, 'def': 1.00, 'liga': 'México'},
    'Monterrey (MEX)': {'atk': 1.65, 'def': 0.95, 'liga': 'México'},

    # 🇸🇦 ARÁBIA SAUDITA
    'Al-Hilal (KSA)': {'atk': 2.30, 'def': 0.80, 'liga': 'Saudi Pro'}, # Nível Champions League
    'Al-Nassr (KSA)': {'atk': 2.00, 'def': 1.10, 'liga': 'Saudi Pro'},
    'Al-Ahli (KSA)': {'atk': 1.70, 'def': 1.20, 'liga': 'Saudi Pro'},
    'Al-Ittihad (KSA)': {'atk': 1.80, 'def': 1.15, 'liga': 'Saudi Pro'},

    # 🇪🇺 OUTROS EUROPA (Adicionados Manualmente)
    'Midtjylland (DEN)': {'atk': 1.40, 'def': 1.30, 'liga': 'Dinamarca'},
    'Copenhagen (DEN)': {'atk': 1.35, 'def': 1.10, 'liga': 'Dinamarca'},
    'D. Zagreb (CRO)': {'atk': 1.50, 'def': 1.20, 'liga': 'Croácia'},
    'Sparta Praha (CZE)': {'atk': 1.45, 'def': 1.15, 'liga': 'Rep. Checa'},
    'Salzburg (AUT)': {'atk': 1.70, 'def': 1.30, 'liga': 'Áustria'},
}

@st.cache_data(ttl=3600)
def carregar_banco_de_dados():
    todos_times = {}
    
    # 1. Carrega CSVs da Europa
    for liga, info in data_sources.items():
        try:
            df = pd.read_csv(info['url'], encoding='latin1')
            cols = ['HomeTeam', 'AwayTeam', 'FTHG', 'FTAG']
            if all(c in df.columns for c in cols):
                df = df[cols].dropna()
                media_gols = (df['FTHG'].mean() + df['FTAG'].mean()) / 2
                times_liga = set(df['HomeTeam'].unique()) | set(df['AwayTeam'].unique())
                
                for time in times_liga:
                    # Lógica de cálculo simplificada para robustez
                    jogos_h = df[df['HomeTeam'] == time]
                    jogos_a = df[df['AwayTeam'] == time]
                    num = len(jogos_h) + len(jogos_a)
                    if num > 5: # Mínimo de jogos para ser confiável
                        gp = jogos_h['FTHG'].sum() + jogos_a['FTAG'].sum()
                        gs = jogos_h['FTAG'].sum() + jogos_a['FTHG'].sum()
                        # Normaliza pela média da liga e aplica peso
                        atk = ((gp/num) / media_gols) * info['peso']
                        defn = ((gs/num) / media_gols) * (2 - info['peso'])
                        todos_times[time] = {'atk': atk, 'def': defn, 'liga': liga}
        except: pass

    # 2. Insere os Gigantes do Mundo
    todos_times.update(world_giants)
    
    return todos_times

db_times = carregar_banco_de_dados()
lista_db = sorted(db_times.keys())

# --- 2. CÁLCULOS MATEMÁTICOS ---
def dixon_coles_metrics(xg_home, xg_away):
    rho = -0.13
    max_gols = 10 # Aumentei para pegar Over altos
    probs = np.zeros((max_gols, max_gols))
    
    # Poisson simples
    for i in range(max_gols):
        for j in range(max_gols):
            probs[i][j] = poisson.pmf(i, xg_home) * poisson.pmf(j, xg_away)
            
    # Ajuste Dixon-Coles
    def adjustment(i, j, mu_h, mu_a):
        if i == 0 and j == 0: return 1 - (mu_h * mu_a * rho)
        if i == 0 and j == 1: return 1 + (mu_h * rho)
        if i == 1 and j == 0: return 1 + (mu_a * rho)
        if i == 1 and j == 1: return 1 - rho
        return 1.0

    for i in range(2):
        for j in range(2):
            probs[i][j] *= adjustment(i, j, xg_home, xg_away)
            
    probs = probs / np.sum(probs) # Normaliza
    
    # Métricas de Resultado
    prob_home = np.sum(np.tril(probs, -1))
    prob_draw = np.sum(np.diag(probs))
    prob_away = np.sum(np.triu(probs, 1))
    
    # Métricas de Gols
    prob_over_15 = 0
    prob_over_25 = 0
    prob_btts = 0 # Ambos marcam
    
    for i in range(max_gols):
        for j in range(max_gols):
            total_gols = i + j
            if total_gols > 1.5: prob_over_15 += probs[i][j]
            if total_gols > 2.5: prob_over_25 += probs[i][j]
            if i > 0 and j > 0: prob_btts += probs[i][j]
            
    return {
        '1x2': (prob_home, prob_draw, prob_away),
        'gols': (prob_over_15, prob_over_25, prob_btts),
        'matrix': probs
    }

# --- 3. INTERFACE DE USUÁRIO ---
st.sidebar.header("⚽ Configurações")
modo = st.sidebar.radio("Modo:", ["Seleção Manual", "Criar Time"])

if modo == "Seleção Manual":
    c1, c2 = st.columns(2)
    # Índices inteligentes
    idx_h = lista_db.index('Flamengo (BRA)') if 'Flamengo (BRA)' in lista_db else 0
    idx_a = lista_db.index('Al-Hilal (KSA)') if 'Al-Hilal (KSA)' in lista_db else 1
    
    tc = c1.selectbox("Mandante (Casa)", lista_db, index=idx_h)
    tv = c2.selectbox("Visitante (Fora)", lista_db, index=idx_a)
    
    if st.button("📊 Analisar Partida Completa", type="primary"):
        ic = db_times[tc]
        iv = db_times[tv]
        
        # xG Calculation
        xg_h = ic['atk'] * iv['def'] * 1.45 * 1.15
        xg_a = iv['atk'] * ic['def'] * 1.45
        
        # Roda a matemática
        metrics = dixon_coles_metrics(xg_h, xg_a)
        p1, px, p2 = metrics['1x2']
        p_o15, p_o25, p_btts = metrics['gols']
        
        # --- EXIBIÇÃO ---
        st.divider()
        st.markdown(f"<h2 style='text-align:center'>{tc} <small>vs</small> {tv}</h2>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align:center; color:#888'>xG Esperado: {xg_h:.2f} x {xg_a:.2f}</p>", unsafe_allow_html=True)
        
        # 1. RESULTADO FINAL (Match Odds)
        st.subheader("🏆 Probabilidades de Resultado")
        k1, k2, k3 = st.columns(3)
        
        k1.metric(f"Vitória {tc}", f"{p1*100:.1f}%", f"Odd Justa: {1/p1:.2f}")
        k2.metric("Empate", f"{px*100:.1f}%", f"Odd Justa: {1/px:.2f}")
        k3.metric(f"Vitória {tv}", f"{p2*100:.1f}%", f"Odd Justa: {1/p2:.2f}")
        
        if p1 > 0.60: k1.success("Favorito Claro")
        if p2 > 0.60: k3.success("Favorito Claro")
        
        st.divider()
        
        # 2. MERCADO DE GOLS (Over/Under/BTTS)
        st.subheader("⚽ Mercado de Gols")
        g1, g2, g3 = st.columns(3)
        
        # Over 1.5
        cor_o15 = "normal"
        if p_o15 > 0.75: cor_o15 = "off" # Inverte delta para verde se alta prob
        g1.metric("Mais de 1.5 Gols", f"{p_o15*100:.1f}%", f"Odd Justa: {1/p_o15:.2f}")
        
        # Over 2.5
        g2.metric("Mais de 2.5 Gols", f"{p_o25*100:.1f}%", f"Odd Justa: {1/p_o25:.2f}")
        
        # BTTS
        g3.metric("Ambos Marcam (Sim)", f"{p_btts*100:.1f}%", f"Odd Justa: {1/p_btts:.2f}")
        
        # Dica de Gols
        if p_o25 > 0.55:
            st.success("🔥 **Tendência:** Jogo movimentado (Over 2.5 provável)")
        elif p_o15 < 0.60:
            st.warning("❄️ **Tendência:** Jogo truncado (Under 2.5 provável)")
        elif p_btts > 0.55:
            st.info("⚡ **Tendência:** Alta chance de Ambos Marcam")

elif modo == "Criar Time":
    st.info("Crie um time personalizado para simular contra os gigantes.")
    nome = st.text_input("Nome", "Meu Time")
    atk = st.slider("Ataque", 0.5, 3.0, 1.5)
    defn = st.slider("Defesa (Menor é melhor)", 0.5, 3.0, 1.0)
    adv = st.selectbox("Adversário", lista_db)
    
    if st.button("Simular"):
        xg_h = atk * db_times[adv]['def'] * 1.6
        xg_a = db_times[adv]['atk'] * defn * 1.45
        metrics = dixon_coles_metrics(xg_h, xg_a)
        st.write(f"Probabilidade Vitória {nome}: {metrics['1x2'][0]*100:.1f}%")
