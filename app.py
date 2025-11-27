import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import poisson

# --- Configurações Iniciais ---
st.set_page_config(page_title="Agente BetMaster Global", page_icon="🌍", layout="wide")

st.title("🌍 Agente de Previsão - Multi-Ligas & Copas")
st.markdown("---")

# --- 1. SELEÇÃO DE LIGA ---
ligas = {
    '🇬🇧 Premier League (Inglaterra)': 'https://www.football-data.co.uk/mmz4281/2425/E0.csv',
    '🇪🇸 La Liga (Espanha)': 'https://www.football-data.co.uk/mmz4281/2425/SP1.csv',
    '🇮🇹 Serie A (Itália)': 'https://www.football-data.co.uk/mmz4281/2425/I1.csv',
    '🇩🇪 Bundesliga (Alemanha)': 'https://www.football-data.co.uk/mmz4281/2425/D1.csv',
    '🇫🇷 Ligue 1 (França)': 'https://www.football-data.co.uk/mmz4281/2425/F1.csv',
    '🏆 UEFA Champions League (Manual)': 'UCL_MANUAL',
    '🟠 UEFA Europa League (Manual)': 'UEL_MANUAL',
    '🇧🇷 Brasileirão Série A (Manual)': 'BR_MANUAL',
    '🌎 Libertadores (Manual)': 'LIB_MANUAL'
}

liga_selecionada = st.sidebar.selectbox("Escolha o Campeonato", list(ligas.keys()))

# --- 2. CARREGAMENTO DE DADOS ---

@st.cache_data
def carregar_dados_europa(url):
    try:
        df = pd.read_csv(url)
        df = df[['HomeTeam', 'AwayTeam', 'FTHG', 'FTAG']].dropna()
        return df
    except:
        return None

def calcular_forca_times(df):
    media_gols_casa = df['FTHG'].mean()
    media_gols_fora = df['FTAG'].mean()
    times = sorted(list(set(df['HomeTeam'].unique()) | set(df['AwayTeam'].unique())))
    stats = {}

    for time in times:
        jogos_casa = df[df['HomeTeam'] == time]
        jogos_fora = df[df['AwayTeam'] == time]
        
        gols_pro = jogos_casa['FTHG'].sum() + jogos_fora['FTAG'].sum()
        gols_sof = jogos_casa['FTAG'].sum() + jogos_fora['FTHG'].sum()
        num_jogos = len(jogos_casa) + len(jogos_fora)
        
        if num_jogos > 0:
            atk = (gols_pro / num_jogos) / ((media_gols_casa + media_gols_fora) / 2)
            defn = (gols_sof / num_jogos) / ((media_gols_casa + media_gols_fora) / 2)
        else:
            atk, defn = 1.0, 1.0

        stats[time] = {'atk': atk, 'def': defn}
    
    return stats, media_gols_casa, media_gols_fora

# Lógica de Seleção de Dados
if "MANUAL" in ligas[liga_selecionada]:
    # --- CONFIGURAÇÃO MANUAL DE FORÇA (Baseado em Power Rankings 24/25) ---
    league_avg_home = 1.50
    league_avg_away = 1.20
    
    if "Champions" in liga_selecionada:
        # Times de Elite da Europa
        teams_stats = {
            'Man City': {'atk': 2.10, 'def': 0.70}, 'Liverpool': {'atk': 2.00, 'def': 0.65},
            'Real Madrid': {'atk': 1.90, 'def': 0.80}, 'Barcelona': {'atk': 2.20, 'def': 0.85},
            'Bayern Munich': {'atk': 2.10, 'def': 0.90}, 'Arsenal': {'atk': 1.85, 'def': 0.70},
            'Inter Milan': {'atk': 1.70, 'def': 0.75}, 'B. Leverkusen': {'atk': 1.80, 'def': 1.10},
            'PSG': {'atk': 1.75, 'def': 1.00}, 'Atl. Madrid': {'atk': 1.50, 'def': 0.85},
            'Juventus': {'atk': 1.45, 'def': 0.80}, 'Milan': {'atk': 1.60, 'def': 1.20},
            'Dortmund': {'atk': 1.70, 'def': 1.30}, 'Aston Villa': {'atk': 1.60, 'def': 1.10},
            'Sporting CP': {'atk': 1.90, 'def': 0.90}, 'Benfica': {'atk': 1.50, 'def': 1.00},
            'Monaco': {'atk': 1.50, 'def': 1.00}, 'Brest': {'atk': 1.20, 'def': 1.10}
        }
        st.info("ℹ️ Dados da Champions baseados em Power Ranking atual (Out/Nov 2024).")

    elif "Europa League" in liga_selecionada:
        teams_stats = {
            'Tottenham': {'atk': 1.80, 'def': 1.20}, 'Man United': {'atk': 1.40, 'def': 1.40},
            'Lazio': {'atk': 1.60, 'def': 1.10}, 'Roma': {'atk': 1.30, 'def': 1.20},
            'Porto': {'atk': 1.65, 'def': 1.00}, 'Athletic Club': {'atk': 1.50, 'def': 0.90},
            'Real Sociedad': {'atk': 1.20, 'def': 0.90}, 'Frankfurt': {'atk': 1.70, 'def': 1.30},
            'Galatasaray': {'atk': 1.80, 'def': 1.50}, 'Fenerbahce': {'atk': 1.50, 'def': 1.10},
            'Lyon': {'atk': 1.50, 'def': 1.40}, 'Ajax': {'atk': 1.40, 'def': 1.20},
            'Rangers': {'atk': 1.20, 'def': 1.30}, 'Olympiacos': {'atk': 1.30, 'def': 1.20}
        }
        st.info("ℹ️ Dados da Europa League baseados em forma recente.")

    elif "Brasileirão" in liga_selecionada:
        teams_stats = {
            'Botafogo': {'atk': 1.85, 'def': 0.70}, 'Palmeiras': {'atk': 1.70, 'def': 0.65},
            'Fortaleza': {'atk': 1.50, 'def': 0.80}, 'Flamengo': {'atk': 1.60, 'def': 0.85},
            'Internacional': {'atk': 1.45, 'def': 0.75}, 'São Paulo': {'atk': 1.25, 'def': 0.85},
            'Bahia': {'atk': 1.30, 'def': 1.10}, 'Cruzeiro': {'atk': 1.15, 'def': 0.90},
            'Vasco': {'atk': 1.20, 'def': 1.25}, 'Atlético-MG': {'atk': 1.35, 'def': 1.15},
            'Corinthians': {'atk': 1.25, 'def': 1.00}, 'Grêmio': {'atk': 1.15, 'def': 1.20},
            'Vitória': {'atk': 1.10, 'def': 1.35}, 'Fluminense': {'atk': 1.00, 'def': 1.10},
            'Criciúma': {'atk': 1.10, 'def': 1.30}, 'Juventude': {'atk': 1.05, 'def': 1.40},
            'Bragantino': {'atk': 1.05, 'def': 1.25}, 'Athletico-PR': {'atk': 1.05, 'def': 1.20},
            'Cuiabá': {'atk': 0.80, 'def': 1.30}, 'Atlético-GO': {'atk': 0.80, 'def': 1.45}
        }
    else: # Libertadores (Finais/Fases)
        teams_stats = {
            'Atletico-MG': {'atk': 1.6, 'def': 0.8}, 'Botafogo': {'atk': 1.8, 'def': 0.7},
            'River Plate': {'atk': 1.5, 'def': 0.8}, 'Peñarol': {'atk': 1.3, 'def': 0.9}
        }

else:
    # Automático Ligas Nacionais (Europa)
    url = ligas[liga_selecionada]
    df = carregar_dados_europa(url)
    if df is not None:
        teams_stats, league_avg_home, league_avg_away = calcular_forca_times(df)
        st.success(f"✅ Dados atualizados carregados com sucesso!")
    else:
        st.error("Erro ao carregar dados.")
        teams_stats = {}

# --- 3. INTERFACE DE PREVISÃO ---

if teams_stats:
    st.sidebar.markdown("---")
    st.sidebar.header("⚖️ Ajuste Fino")
    
    # Seleção de Times
    sorted_teams = sorted(teams_stats.keys())
    c_s1, c_s2 = st.sidebar.columns(2)
    home_team = c_s1.selectbox("Mandante", sorted_teams, index=0)
    # Tenta selecionar um rival diferente para o visitante
    idx_away = 1 if len(sorted_teams) > 1 else 0
    away_team = c_s2.selectbox("Visitante", sorted_teams, index=idx_away)

    # Ajuste de Força (Importante para Copas)
    home_form = st.sidebar.slider(f"Ajuste {home_team}", 0.8, 1.2, 1.0, help="1.0 = Normal. >1.0 = Fase Boa.")
    away_form = st.sidebar.slider(f"Ajuste {away_team}", 0.8, 1.2, 1.0)

    # --- CÁLCULO ---
    def calculate_match(home, away):
        # Pega stats base
        h_atk = teams_stats[home]['atk'] * home_form
        h_def = teams_stats[home]['def'] # Defesa costuma ser mais estável
        a_atk = teams_stats[away]['atk'] * away_form
        a_def = teams_stats[away]['def']

        # xG
        xg_home = h_atk * a_def * league_avg_home
        xg_away = a_atk * h_def * league_avg_away

        # Poisson
        max_goals = 8
        probs = np.zeros((max_goals, max_goals))
        for i in range(max_goals):
            for j in range(max_goals):
                probs[i][j] = poisson.pmf(i, xg_home) * poisson.pmf(j, xg_away)

        p_h = np.sum(np.tril(probs, -1))
        p_d = np.sum(np.diag(probs))
        p_a = np.sum(np.triu(probs, 1))
        return p_h, p_d, p_a, xg_home, xg_away

    if st.sidebar.button("🔮 Prever Resultado", type="primary"):
        ph, pd_raw, pa, xgh, xga = calculate_match(home_team, away_team)

        # Layout de Placar
        st.markdown(f"""
        <div style="text-align: center; background-color: #0e1117; padding: 20px; border-radius: 10px; border: 1px solid #303030;">
            <h1 style="margin:0;">{home_team} <span style="color:#aaa; font-size:20px;">vs</span> {away_team}</h1>
            <h3 style="color: #00ff00;">xG: {xgh:.2f} <span style="color:white; margin:0 20px;">-</span> {xga:.2f}</h3>
        </div>
        """, unsafe_allow_html=True)

        st.divider()

        # Odds e Probabilidades
        c1, c2, c3 = st.columns(3)
        
        c1.metric("🏠 Vitória Casa", f"{ph*100:.1f}%", f"Odd Justa: {1/ph:.2f}")
        c2.metric("⚖️ Empate", f"{pd_raw*100:.1f}%", f"Odd Justa: {1/pd_raw:.2f}")
        c3.metric("✈️ Vitória Fora", f"{pa*100:.1f}%", f"Odd Justa: {1/pa:.2f}")

        # Dica
        st.info("💡 **Dica de Champions:** Em jogos de mata-mata, times jogando a segunda partida em casa tendem a ser mais agressivos se estiverem perdendo no agregado.")

else:
    st.warning("Selecione uma liga válida na barra lateral.")
