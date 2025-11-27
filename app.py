import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import poisson

# --- Configurações Iniciais ---
st.set_page_config(page_title="Agente BetMaster Global", page_icon="🌍", layout="wide")

st.title("🌍 Agente de Previsão - Multi-Ligas")
st.markdown("---")

# --- 1. SELEÇÃO DE LIGA ---
ligas = {
    '🇬🇧 Premier League (Inglaterra)': 'https://www.football-data.co.uk/mmz4281/2425/E0.csv',
    '🇪🇸 La Liga (Espanha)': 'https://www.football-data.co.uk/mmz4281/2425/SP1.csv',
    '🇮🇹 Serie A (Itália)': 'https://www.football-data.co.uk/mmz4281/2425/I1.csv',
    '🇩🇪 Bundesliga (Alemanha)': 'https://www.football-data.co.uk/mmz4281/2425/D1.csv',
    '🇫🇷 Ligue 1 (França)': 'https://www.football-data.co.uk/mmz4281/2425/F1.csv',
    '🇧🇷 Brasileirão Série A (Manual)': 'BR_MANUAL',
    '🏆 Libertadores (Manual)': 'LIB_MANUAL'
}

liga_selecionada = st.sidebar.selectbox("Escolha o Campeonato", list(ligas.keys()))

# --- 2. CARREGAMENTO DE DADOS ---

@st.cache_data # Isso faz o site ficar rápido, não baixa o arquivo toda hora
def carregar_dados_europa(url):
    try:
        # Lê o CSV direto do link
        df = pd.read_csv(url)
        # Filtra colunas úteis: HomeTeam, AwayTeam, FTHG (Gols Casa), FTAG (Gols Fora)
        df = df[['HomeTeam', 'AwayTeam', 'FTHG', 'FTAG']].dropna()
        return df
    except:
        return None

def calcular_forca_times(df):
    # Médias da Liga
    media_gols_casa = df['FTHG'].mean()
    media_gols_fora = df['FTAG'].mean()

    # Estatísticas por Time
    times = sorted(list(set(df['HomeTeam'].unique()) | set(df['AwayTeam'].unique())))
    stats = {}

    for time in times:
        # Jogos em Casa
        jogos_casa = df[df['HomeTeam'] == time]
        gols_pro_casa = jogos_casa['FTHG'].sum() if len(jogos_casa) > 0 else 0
        gols_sof_casa = jogos_casa['FTAG'].sum() if len(jogos_casa) > 0 else 0
        
        # Jogos Fora
        jogos_fora = df[df['AwayTeam'] == time]
        gols_pro_fora = jogos_fora['FTAG'].sum() if len(jogos_fora) > 0 else 0
        gols_sof_fora = jogos_fora['FTHG'].sum() if len(jogos_fora) > 0 else 0

        num_jogos = len(jogos_casa) + len(jogos_fora)
        
        if num_jogos > 0:
            # Força de Ataque = (Média de gols do time) / (Média da liga)
            atk_rating = ((gols_pro_casa + gols_pro_fora) / num_jogos) / ((media_gols_casa + media_gols_fora) / 2)
            def_rating = ((gols_sof_casa + gols_sof_fora) / num_jogos) / ((media_gols_casa + media_gols_fora) / 2)
        else:
            atk_rating, def_rating = 1.0, 1.0 # Padrão se não tiver dados

        stats[time] = {'atk': atk_rating, 'def': def_rating}
    
    return stats, media_gols_casa, media_gols_fora

# Lógica de Seleção de Dados
if "MANUAL" in ligas[liga_selecionada]:
    # Dados Manuais para Brasil/Liberta (Pois dados grátis em CSV são raros)
    if "Brasileirão" in liga_selecionada:
        teams_stats = {
            'Palmeiras': {'atk': 1.70, 'def': 0.60}, 'Botafogo': {'atk': 1.85, 'def': 0.70},
            'Flamengo': {'atk': 1.65, 'def': 0.80}, 'Fortaleza': {'atk': 1.45, 'def': 0.85},
            'Sao Paulo': {'atk': 1.25, 'def': 0.90}, 'Corinthians': {'atk': 1.15, 'def': 1.00},
            'Vasco': {'atk': 1.25, 'def': 1.30}, 'Atletico-MG': {'atk': 1.40, 'def': 1.10}
        }
    else: # Libertadores (Principais times)
        teams_stats = {
            'River Plate': {'atk': 1.6, 'def': 0.7}, 'Atletico-MG': {'atk': 1.5, 'def': 0.9},
            'Botafogo': {'atk': 1.7, 'def': 0.8}, 'Penarol': {'atk': 1.2, 'def': 1.1},
            'Flamengo': {'atk': 1.6, 'def': 0.8}, 'Palmeiras': {'atk': 1.6, 'def': 0.7}
        }
    league_avg_home = 1.5
    league_avg_away = 1.2
    st.info("ℹ️ Usando base de dados manual (estimada) para esta liga.")
else:
    # Automático Europa
    url = ligas[liga_selecionada]
    df = carregar_dados_europa(url)
    if df is not None:
        teams_stats, league_avg_home, league_avg_away = calcular_forca_times(df)
        st.success(f"✅ Dados atualizados carregados da {liga_selecionada}! ({len(df)} jogos analisados)")
    else:
        st.error("Erro ao carregar dados. O campeonato pode estar em pausa.")
        teams_stats = {}

# --- 3. INTERFACE DE PREVISÃO ---

if teams_stats:
    col1, col2 = st.sidebar.columns(2)
    sorted_teams = sorted(teams_stats.keys())
    
    home_team = col1.selectbox("Mandante", sorted_teams, index=0)
    away_team = col2.selectbox("Visitante", sorted_teams, index=min(1, len(sorted_teams)-1))

    # --- CÁLCULO DE POISSON ---
    def calculate_match(home, away):
        h_atk = teams_stats[home]['atk']
        h_def = teams_stats[home]['def']
        a_atk = teams_stats[away]['atk']
        a_def = teams_stats[away]['def']

        # Fator Casa simples (1.10x)
        xg_home = h_atk * a_def * league_avg_home * 1.10
        xg_away = a_atk * h_def * league_avg_away

        max_goals = 8
        probs = np.zeros((max_goals, max_goals))
        for i in range(max_goals):
            for j in range(max_goals):
                probs[i][j] = poisson.pmf(i, xg_home) * poisson.pmf(j, xg_away)

        p_h = np.sum(np.tril(probs, -1))
        p_d = np.sum(np.diag(probs))
        p_a = np.sum(np.triu(probs, 1))
        return p_h, p_d, p_a, xg_home, xg_away

    if st.sidebar.button("Calcular Previsão"):
        ph, pd_raw, pa, xgh, xga = calculate_match(home_team, away_team)

        # Exibição
        c1, c2, c3 = st.columns([1, 0.2, 1])
        c1.markdown(f"### {home_team}")
        c1.metric("xG", f"{xgh:.2f}")
        c2.markdown("## x")
        c3.markdown(f"### {away_team}")
        c3.metric("xG", f"{xga:.2f}")

        st.divider()

        # Odds
        odd_h, odd_d, odd_a = 1/ph, 1/pd_raw, 1/pa
        
        cols = st.columns(3)
        cols[0].success(f"Vitória Casa: {ph*100:.1f}%\n\nOdd Justa: **{odd_h:.2f}**")
        cols[1].warning(f"Empate: {pd_raw*100:.1f}%\n\nOdd Justa: **{odd_d:.2f}**")
        cols[2].error(f"Vitória Fora: {pa*100:.1f}%\n\nOdd Justa: **{odd_a:.2f}**")

else:
    st.warning("Selecione uma liga válida.")
