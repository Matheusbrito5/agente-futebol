import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import poisson

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="BetMaster Global Selector", page_icon="🌐", layout="wide")

st.title("🌐 Agente Global - Seleção por Ligas")
st.markdown("""
**Instruções:** Selecione a liga do mandante e do visitante na barra lateral.
**Recursos:** Dixon-Coles (Ajustado) | Mercado de Gols | Odds Justas.
""")

# --- 1. BANCO DE DADOS (LINKS E TIMES) ---
base_url = "https://www.football-data.co.uk/mmz4281/2425/"

# Dicionário de Ligas Automáticas (Europa)
ligas_auto = {
    '🇬🇧 Premier League': {'url': base_url + 'E0.csv', 'peso': 1.00},
    '🇪🇸 La Liga':        {'url': base_url + 'SP1.csv', 'peso': 0.95},
    '🇮🇹 Serie A':        {'url': base_url + 'I1.csv',  'peso': 0.90},
    '🇩🇪 Bundesliga':     {'url': base_url + 'D1.csv',  'peso': 0.92},
    '🇫🇷 Ligue 1':        {'url': base_url + 'F1.csv',  'peso': 0.88},
    '🇵🇹 Liga Portugal':  {'url': base_url + 'P1.csv',  'peso': 0.82},
    '🇳🇱 Eredivisie':     {'url': base_url + 'N1.csv',  'peso': 0.80},
    '🇹🇷 Turquia':        {'url': base_url + 'T1.csv',  'peso': 0.78},
}

# Dicionário Manual (Resto do Mundo / Times Faltantes)
# Estrutura: 'Nome da Liga': { 'Time': {atk, def} }
ligas_manual = {
    '🇧🇷 Brasileirão': {
        'Botafogo': {'atk': 1.85, 'def': 0.75}, 'Palmeiras': {'atk': 1.75, 'def': 0.70},
        'Flamengo': {'atk': 1.70, 'def': 0.85}, 'Fortaleza': {'atk': 1.60, 'def': 0.90},
        'Internacional': {'atk': 1.55, 'def': 0.80}, 'São Paulo': {'atk': 1.40, 'def': 0.90},
        'Corinthians': {'atk': 1.45, 'def': 1.05}, 'Atlético-MG': {'atk': 1.50, 'def': 1.10},
        'Vasco': {'atk': 1.30, 'def': 1.20}, 'Cruzeiro': {'atk': 1.35, 'def': 0.95},
        'Bahia': {'atk': 1.30, 'def': 1.15}, 'Grêmio': {'atk': 1.25, 'def': 1.20},
    },
    '🇦🇷 Argentina': {
        'River Plate': {'atk': 1.65, 'def': 0.80}, 'Boca Juniors': {'atk': 1.45, 'def': 0.90},
        'Racing': {'atk': 1.60, 'def': 1.00}, 'Velez Sarsfield': {'atk': 1.50, 'def': 0.95}
    },
    '🇺🇸 MLS (EUA)': {
        'Inter Miami': {'atk': 2.10, 'def': 1.40}, 'LA Galaxy': {'atk': 1.80, 'def': 1.20},
        'LAFC': {'atk': 1.75, 'def': 1.15}, 'Columbus Crew': {'atk': 1.70, 'def': 1.25}
    },
    '🇸🇦 Arábia Saudita': {
        'Al-Hilal': {'atk': 2.30, 'def': 0.80}, 'Al-Nassr': {'atk': 2.00, 'def': 1.10},
        'Al-Ahli': {'atk': 1.70, 'def': 1.20}, 'Al-Ittihad': {'atk': 1.80, 'def': 1.15}
    },
    '🇪🇺 Outros Europa (Champions/Europa)': {
        'Midtjylland': {'atk': 1.40, 'def': 1.30}, 'Copenhagen': {'atk': 1.35, 'def': 1.10},
        'Sparta Praha': {'atk': 1.45, 'def': 1.15}, 'D. Zagreb': {'atk': 1.50, 'def': 1.20},
        'Olympiacos': {'atk': 1.50, 'def': 1.10}, 'PAOK': {'atk': 1.45, 'def': 1.15},
        'Red Star Belgrade': {'atk': 1.40, 'def': 1.30}, 'Salzburg': {'atk': 1.60, 'def': 1.25}
    }
}

# --- 2. CARREGAMENTO E ORGANIZAÇÃO ---
@st.cache_data(ttl=3600)
def carregar_tudo():
    # Estrutura final: { 'Nome Liga': { 'TimeA': stats, 'TimeB': stats } }
    dados_organizados = {}

    # 1. Carrega Europa Automática
    for nome_liga, info in ligas_auto.items():
        dados_organizados[nome_liga] = {}
        try:
            df = pd.read_csv(info['url'], encoding='latin1')
            cols = ['HomeTeam', 'AwayTeam', 'FTHG', 'FTAG']
            if all(c in df.columns for c in cols):
                df = df[cols].dropna()
                media_gols = (df['FTHG'].mean() + df['FTAG'].mean()) / 2
                times = set(df['HomeTeam'].unique()) | set(df['AwayTeam'].unique())
                
                for time in times:
                    jogos_h = df[df['HomeTeam'] == time]
                    jogos_a = df[df['AwayTeam'] == time]
                    num = len(jogos_h) + len(jogos_a)
                    if num > 3:
                        gp = jogos_h['FTHG'].sum() + jogos_a['FTAG'].sum()
                        gs = jogos_h['FTAG'].sum() + jogos_a['FTHG'].sum()
                        atk = ((gp/num) / media_gols) * info['peso']
                        defn = ((gs/num) / media_gols) * (2 - info['peso'])
                        dados_organizados[nome_liga][time] = {'atk': atk, 'def': defn}
        except:
            dados_organizados[nome_liga] = {'Erro': {'atk':1, 'def':1}}

    # 2. Carrega Manuais
    for nome_liga, times in ligas_manual.items():
        dados_organizados[nome_liga] = times
        
    return dados_organizados

# Carrega o banco de dados
db_completo = carregar_tudo()

# --- 3. BARRA LATERAL (SELEÇÃO) ---
st.sidebar.header("🕹️ Seleção de Times")

st.sidebar.markdown("### 🏠 Mandante (Casa)")
liga_casa = st.sidebar.selectbox("Liga do Mandante", sorted(db_completo.keys()), index=sorted(db_completo.keys()).index('🇬🇧 Premier League'))
times_casa_disp = sorted(db_completo[liga_casa].keys())
time_casa = st.sidebar.selectbox("Time da Casa", times_casa_disp)

st.sidebar.markdown("---")

st.sidebar.markdown("### ✈️ Visitante (Fora)")
# Tenta selecionar a mesma liga por padrão para facilitar
idx_liga_fora = sorted(db_completo.keys()).index(liga_casa)
liga_fora = st.sidebar.selectbox("Liga do Visitante", sorted(db_completo.keys()), index=idx_liga_fora)
times_fora_disp = sorted(db_completo[liga_fora].keys())
time_fora = st.sidebar.selectbox("Time Visitante", times_fora_disp, index=min(1, len(times_fora_disp)-1))

# --- 4. CÁLCULOS (DIXON-COLES) ---
def calcular_metricas(tc_nome, tv_nome, stats_c, stats_v):
    # Fatores globais
    fator_casa = 1.15
    media_gols_global = 1.50 # Média unificada para comparações globais
    
    xg_home = stats_c['atk'] * stats_v['def'] * media_gols_global * fator_casa
    xg_away = stats_v['atk'] * stats_c['def'] * media_gols_global
    
    # Poisson + Dixon-Coles
    rho = -0.13
    max_gols = 8
    probs = np.zeros((max_gols, max_gols))
    
    for i in range(max_gols):
        for j in range(max_gols):
            probs[i][j] = poisson.pmf(i, xg_home) * poisson.pmf(j, xg_away)
            
    # Ajuste Dixon-Coles (Correção de empate 0x0, 1x1)
    def adj(i, j, mu_h, mu_a):
        if i==0 and j==0: return 1 - (mu_h*mu_a*rho)
        if i==0 and j==1: return 1 + (mu_h*rho)
        if i==1 and j==0: return 1 + (mu_a*rho)
        if i==1 and j==1: return 1 - rho
        return 1.0
        
    for i in range(2):
        for j in range(2):
            probs[i][j] *= adj(i, j, xg_home, xg_away)
            
    probs = probs / np.sum(probs) # Normaliza
    
    # Probabilidades Totais
    p_home = np.sum(np.tril(probs, -1))
    p_draw = np.sum(np.diag(probs))
    p_away = np.sum(np.triu(probs, 1))
    
    # Gols
    p_o15 = np.sum([probs[i][j] for i in range(8) for j in range(8) if (i+j) > 1.5])
    p_o25 = np.sum([probs[i][j] for i in range(8) for j in range(8) if (i+j) > 2.5])
    p_btts = np.sum([probs[i][j] for i in range(1,8) for j in range(1,8)])
    
    return p_home, p_draw, p_away, p_o15, p_o25, p_btts, xg_home, xg_away

# --- 5. EXIBIÇÃO ---
if st.sidebar.button("🔮 Calcular Odds", type="primary"):
    stats_c = db_completo[liga_casa][time_casa]
    stats_v = db_completo[liga_fora][time_fora]
    
    p1, px, p2, po15, po25, pbtts, xgh, xga = calcular_metricas(time_casa, time_fora, stats_c, stats_v)
    
    # Cabeçalho
    st.markdown(f"""
    <div style="background-color:#111; padding:20px; border-radius:10px; text-align:center; border: 1px solid #333">
        <h1 style="margin:0; color:white">{time_casa} <span style="color:#666">vs</span> {time_fora}</h1>
        <p style="color:#bbb; font-size:18px; margin-top:5px">xG Esperado: <span style="color:#4caf50">{xgh:.2f}</span> - <span style="color:#2196f3">{xga:.2f}</span></p>
    </div>
    """, unsafe_allow_html=True)
    
    st.write("")
    
    # Odds Principais
    col1, col2, col3 = st.columns(3)
    col1.metric("🏠 Vitória Casa", f"{p1*100:.1f}%", f"Odd: {1/p1:.2f}")
    col2.metric("⚖️ Empate", f"{px*100:.1f}%", f"Odd: {1/px:.2f}")
    col3.metric("✈️ Vitória Fora", f"{p2*100:.1f}%", f"Odd: {1/p2:.2f}")
    
    if p1 > 0.6: col1.success("Provável")
    if p2 > 0.6: col3.success("Provável")
    
    st.markdown("---")
    
    # Mercado de Gols
    st.subheader("🥅 Mercado de Gols")
    g1, g2, g3 = st.columns(3)
    
    g1.metric("Over 1.5 Gols", f"{po15*100:.1f}%", f"Odd: {1/po15:.2f}")
    g2.metric("Over 2.5 Gols", f"{po25*100:.1f}%", f"Odd: {1/po25:.2f}")
    g3.metric("Ambos Marcam", f"{pbtts*100:.1f}%", f"Odd: {1/pbtts:.2f}")
    
    # Insights
    st.info("💡 **Análise:**")
    if po25 > 0.55: st.write("- 🟢 Jogo com tendência para gols (Over 2.5).")
    else: st.write("- 🔴 Jogo com tendência a ser fechado (Under 2.5).")
    
    if pbtts > 0.55: st.write("- 🟢 Alta probabilidade de ambas as equipes marcarem.")
    
    if abs(p1 - p2) < 0.1: st.write("- ⚠️ Jogo muito equilibrado. Cuidado com apostas secas (1x2).")

else:
    st.info("👈 Selecione as ligas e times na barra lateral e clique em 'Calcular Odds'.")
