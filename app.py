import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import poisson

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="BetMaster 2025/26", page_icon="⚽", layout="wide")

st.title("⚽ Agente de Apostas - Temporada 25/26")
st.markdown("---")

# --- 1. CARREGAMENTO DE DADOS ---
# Europa: Temporada 25/26
base_url_europa = "https://www.football-data.co.uk/mmz4281/2526/"

# Ligas Automáticas (Europa 25/26)
ligas_auto = {
    '🇬🇧 Premier League (25/26)': {'url': base_url_europa + 'E0.csv', 'peso': 1.00},
    '🇪🇸 La Liga (25/26)':        {'url': base_url_europa + 'SP1.csv', 'peso': 0.95},
    '🇮🇹 Serie A (25/26)':        {'url': base_url_europa + 'I1.csv',  'peso': 0.90},
    '🇩🇪 Bundesliga (25/26)':     {'url': base_url_europa + 'D1.csv',  'peso': 0.92},
    '🇫🇷 Ligue 1 (25/26)':        {'url': base_url_europa + 'F1.csv',  'peso': 0.88},
    '🇵🇹 Liga Portugal (25/26)':  {'url': base_url_europa + 'P1.csv',  'peso': 0.82},
    '🇳🇱 Eredivisie (25/26)':     {'url': base_url_europa + 'N1.csv',  'peso': 0.80},
    '🇹🇷 Turquia (25/26)':        {'url': base_url_europa + 'T1.csv',  'peso': 0.78},
}

# Ligas Manuais (Brasil 2025 + UEFA)
ligas_manual = {
    '🇧🇷 Brasileirão Série A (2025)': {
        # G6 + Gigantes
        'Botafogo': {'atk': 1.85, 'def': 0.75}, 'Palmeiras': {'atk': 1.75, 'def': 0.70},
        'Fortaleza': {'atk': 1.60, 'def': 0.90}, 'Flamengo': {'atk': 1.70, 'def': 0.85},
        'Internacional': {'atk': 1.55, 'def': 0.80}, 'São Paulo': {'atk': 1.40, 'def': 0.90},
        'Corinthians': {'atk': 1.45, 'def': 1.05}, 'Bahia': {'atk': 1.30, 'def': 1.15},
        'Cruzeiro': {'atk': 1.35, 'def': 0.95}, 'Vasco': {'atk': 1.30, 'def': 1.20},
        'Atlético-MG': {'atk': 1.50, 'def': 1.10}, 'Grêmio': {'atk': 1.25, 'def': 1.20},
        'Fluminense': {'atk': 1.35, 'def': 1.15}, 'Santos': {'atk': 1.30, 'def': 1.00},
        'Bragantino': {'atk': 1.25, 'def': 1.15}, 'Athletico-PR': {'atk': 1.20, 'def': 1.10},
        'Vitória': {'atk': 1.15, 'def': 1.30}, 'Criciúma': {'atk': 1.15, 'def': 1.25},
        'Juventude': {'atk': 1.10, 'def': 1.35}, 'Atlético-GO': {'atk': 1.05, 'def': 1.40},
        'Cuiabá': {'atk': 0.90, 'def': 1.30}, 
    },
    
    '🏆 UEFA Europa League (Fase Liga 25/26)': {
        'Tottenham (ENG)': {'atk': 1.85, 'def': 1.20}, 'Man Utd (ENG)': {'atk': 1.60, 'def': 1.30},
        'Roma (ITA)': {'atk': 1.55, 'def': 1.10}, 'Lazio (ITA)': {'atk': 1.65, 'def': 1.05},
        'Athletic Club (ESP)': {'atk': 1.60, 'def': 0.90}, 'Real Sociedad (ESP)': {'atk': 1.40, 'def': 0.95},
        'Porto (POR)': {'atk': 1.70, 'def': 0.95}, 'Frankfurt (GER)': {'atk': 1.75, 'def': 1.25},
        'Lyon (FRA)': {'atk': 1.55, 'def': 1.40}, 'Nice (FRA)': {'atk': 1.40, 'def': 1.00},
        'Ajax (NED)': {'atk': 1.60, 'def': 1.20}, 'AZ Alkmaar (NED)': {'atk': 1.45, 'def': 1.25},
        'Braga (POR)': {'atk': 1.50, 'def': 1.20}, 'Olympiacos (GRE)': {'atk': 1.55, 'def': 1.15},
        'PAOK (GRE)': {'atk': 1.45, 'def': 1.20}, 'Rangers (SCO)': {'atk': 1.40, 'def': 1.35},
        'Galatasaray (TUR)': {'atk': 1.80, 'def': 1.35}, 'Fenerbahce (TUR)': {'atk': 1.65, 'def': 1.15},
        'Besiktas (TUR)': {'atk': 1.45, 'def': 1.50}, 'Midtjylland (DEN)': {'atk': 1.35, 'def': 1.30},
        'Bodo/Glimt (NOR)': {'atk': 1.50, 'def': 1.40}, 'Union SG (BEL)': {'atk': 1.30, 'def': 1.15},
        'Anderlecht (BEL)': {'atk': 1.35, 'def': 1.20}, 'Slavia Praha (CZE)': {'atk': 1.50, 'def': 1.10},
        'Viktoria Plzen (CZE)': {'atk': 1.35, 'def': 1.05}, 'Hoffenheim (GER)': {'atk': 1.50, 'def': 1.60},
        'Dynamo Kyiv (UKR)': {'atk': 1.30, 'def': 1.30}, 'Malmo (SWE)': {'atk': 1.25, 'def': 1.30},
        'Elfsborg (SWE)': {'atk': 1.20, 'def': 1.40}, 'Qarabag (AZE)': {'atk': 1.30, 'def': 1.40},
        'Ludogorets (BUL)': {'atk': 1.25, 'def': 1.35}, 'M. Tel-Aviv (ISR)': {'atk': 1.20, 'def': 1.40},
        'FCSB (ROM)': {'atk': 1.15, 'def': 1.35}, 'RFS (LVA)': {'atk': 0.90, 'def': 1.80},
    },
    
    '🏆 UEFA Champions League (25/26)': {
        'Man City': {'atk': 2.15, 'def': 0.70}, 'Real Madrid': {'atk': 2.00, 'def': 0.80},
        'Liverpool': {'atk': 2.05, 'def': 0.65}, 'Barcelona': {'atk': 2.20, 'def': 0.90},
        'Bayern Munich': {'atk': 2.10, 'def': 0.90}, 'Inter Milan': {'atk': 1.70, 'def': 0.75},
        'Arsenal': {'atk': 1.80, 'def': 0.70}, 'B. Leverkusen': {'atk': 1.75, 'def': 1.05},
        'PSG': {'atk': 1.80, 'def': 1.00}, 'Juventus': {'atk': 1.45, 'def': 0.80},
        'Atl. Madrid': {'atk': 1.50, 'def': 0.85}, 'Sporting CP': {'atk': 1.90, 'def': 0.90},
        'Benfica': {'atk': 1.60, 'def': 1.00}, 'Monaco': {'atk': 1.55, 'def': 1.10},
        'Aston Villa': {'atk': 1.65, 'def': 1.15}, 'Brest': {'atk': 1.25, 'def': 1.10},
        'Milan': {'atk': 1.60, 'def': 1.15}, 'Dortmund': {'atk': 1.70, 'def': 1.25},
        'Atalanta': {'atk': 1.75, 'def': 1.20}, 'Stuttgart': {'atk': 1.50, 'def': 1.30}
    },
    
    '🇸🇦 Arábia Saudita (25/26)': {
        'Al-Hilal': {'atk': 2.30, 'def': 0.80}, 'Al-Nassr': {'atk': 2.00, 'def': 1.10},
        'Al-Ahli': {'atk': 1.70, 'def': 1.20}, 'Al-Ittihad': {'atk': 1.80, 'def': 1.15}
    }
}

# --- 2. CARREGAMENTO ---
@st.cache_data(ttl=3600)
def carregar_dados():
    db = {}
    
    # Automático (Europa Ligas Nacionais)
    for nome, info in ligas_auto.items():
        db[nome] = {}
        try:
            df = pd.read_csv(info['url'], encoding='latin1')
            cols = ['HomeTeam', 'AwayTeam', 'FTHG', 'FTAG']
            if all(c in df.columns for c in cols):
                df = df[cols].dropna()
                media = (df['FTHG'].mean() + df['FTAG'].mean()) / 2
                times = set(df['HomeTeam'].unique()) | set(df['AwayTeam'].unique())
                for t in times:
                    h = df[df['HomeTeam'] == t]
                    a = df[df['AwayTeam'] == t]
                    if len(h)+len(a) > 2:
                        gp = h['FTHG'].sum() + a['FTAG'].sum()
                        gs = h['FTAG'].sum() + a['FTHG'].sum()
                        num = len(h)+len(a)
                        atk = ((gp/num)/media) * info['peso']
                        defn = ((gs/num)/media) * (2 - info['peso'])
                        db[nome][t] = {'atk': atk, 'def': defn}
        except: pass
        
    # Manual (Liga Europa, Champions, Brasil)
    for nome, times in ligas_manual.items():
        db[nome] = times
        
    return db

db_completo = carregar_dados()

# --- 3. INTERFACE ---
st.sidebar.header("🏆 Seleção do Jogo")

# Define índices padrão para evitar erro
default_uefa = '🏆 UEFA Europa League (Fase Liga 25/26)'
default_idx = list(db_completo.keys()).index(default_uefa) if default_uefa in db_completo else 0

# CASA
st.sidebar.subheader("🏠 Mandante")
liga_casa = st.sidebar.selectbox("Liga Mandante", sorted(db_completo.keys()), index=default_idx)
time_casa = st.sidebar.selectbox("Time Mandante", sorted(db_completo[liga_casa].keys()))

st.sidebar.markdown("---")

# VISITANTE
st.sidebar.subheader("✈️ Visitante")
liga_fora = st.sidebar.selectbox("Liga Visitante", sorted(db_completo.keys()), index=default_idx)
time_fora = st.sidebar.selectbox("Time Visitante", sorted(db_completo[liga_fora].keys()))

# --- 4. CÁLCULO ---
if st.sidebar.button("📊 Analisar Partida", type="primary"):
    stats_c = db_completo[liga_casa][time_casa]
    stats_v = db_completo[liga_fora][time_fora]
    
    # Parâmetros
    fator_casa = 1.15
    media_gols = 1.50
    rho = -0.13 # Dixon-Coles
    
    xg_h = stats_c['atk'] * stats_v['def'] * media_gols * fator_casa
    xg_a = stats_v['atk'] * stats_c['def'] * media_gols
    
    # Matriz
    probs = np.zeros((8,8))
    for i in range(8):
        for j in range(8):
            probs[i][j] = poisson.pmf(i, xg_h) * poisson.pmf(j, xg_a)
            
    # Ajuste DC
    def adj(i,j,mh,ma):
        if i==0 and j==0: return 1-(mh*ma*rho)
        if i==0 and j==1: return 1+(mh*rho)
        if i==1 and j==0: return 1+(ma*rho)
        if i==1 and j==1: return 1-rho
        return 1.0
        
    for i in range(2):
        for j in range(2):
            probs[i][j] *= adj(i,j,xg_h,xg_a)
            
    probs /= np.sum(probs)
    
    # Resultados
    p1 = np.sum(np.tril(probs, -1))
    px = np.sum(np.diag(probs))
    p2 = np.sum(np.triu(probs, 1))
    
    po25 = np.sum([probs[i][j] for i in range(8) for j in range(8) if (i+j) > 2.5])
    pbtts = np.sum([probs[i][j] for i in range(1,8) for j in range(1,8)])
    
    # Exibição
    st.markdown(f"<h2 style='text-align:center'>{time_casa} x {time_fora}</h2>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align:center'>xG: {xg_h:.2f} - {xg_a:.2f}</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    col1.metric("🏠 Vitória Casa", f"{p1*100:.1f}%", f"Odd: {1/p1:.2f}")
    col2.metric("⚖️ Empate", f"{px*100:.1f}%", f"Odd: {1/px:.2f}")
    col3.metric("✈️ Vitória Fora", f"{p2*100:.1f}%", f"Odd: {1/p2:.2f}")
    
    st.divider()
    st.subheader("Gols e Dicas")
    g1, g2 = st.columns(2)
    g1.metric("Mais de 2.5 Gols", f"{po25*100:.1f}%", f"Odd: {1/po25:.2f}")
    g2.metric("Ambos Marcam", f"{pbtts*100:.1f}%", f"Odd: {1/pbtts:.2f}")
