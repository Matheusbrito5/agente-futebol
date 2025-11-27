import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import poisson

# --- Configuração da Página ---
st.set_page_config(page_title="Agente BetMaster", page_icon="⚽")

st.title("⚽ Agente de Previsão Esportiva")
st.markdown("Este agente utiliza o **Modelo de Poisson** para calcular as probabilidades reais de um jogo.")

# --- 1. Base de Dados (Simulada) ---
# Em produção, isso viria de um CSV ou API (Football-Data.co.uk)
# Valor > 1.0 = Forte | Valor < 1.0 = Fraco
teams_data = {
    'Manchester City': {'atk': 2.5, 'def': 0.6},
    'Liverpool':       {'atk': 2.3, 'def': 0.8},
    'Arsenal':         {'atk': 2.1, 'def': 0.7},
    'Chelsea':         {'atk': 1.6, 'def': 1.2},
    'Man United':      {'atk': 1.4, 'def': 1.4},
    'Tottenham':       {'atk': 1.8, 'def': 1.3},
    'Newcastle':       {'atk': 1.5, 'def': 1.1},
    'Luton Town':      {'atk': 0.8, 'def': 2.2}
}

# --- 2. Interface do Usuário ---
col1, col2 = st.columns(2)

with col1:
    home_team = st.selectbox("Time da Casa (Mandante)", list(teams_data.keys()), index=0)

with col2:
    # Remove o time já selecionado na casa para evitar Time A vs Time A
    away_options = [t for t in teams_data.keys() if t != home_team]
    away_team = st.selectbox("Time Visitante", away_options, index=0)

# --- 3. O Cérebro (Cálculo de Poisson) ---
def calculate_probabilities(home, away):
    # Média da liga (constante fictícia para exemplo)
    avg_goals_home = 1.5
    avg_goals_away = 1.2

    # Força esperada de gols
    home_expectancy = teams_data[home]['atk'] * teams_data[away]['def'] * avg_goals_home
    away_expectancy = teams_data[away]['atk'] * teams_data[home]['def'] * avg_goals_away

    # Simula placares de 0x0 até 5x5
    max_goals = 6
    probs = np.zeros((max_goals, max_goals))

    for i in range(max_goals):
        for j in range(max_goals):
            prob_home = poisson.pmf(i, home_expectancy)
            prob_away = poisson.pmf(j, away_expectancy)
            probs[i][j] = prob_home * prob_away

    # Soma as probabilidades
    prob_home_win = np.sum(np.tril(probs, -1))
    prob_draw = np.sum(np.diag(probs))
    prob_away_win = np.sum(np.triu(probs, 1))

    return prob_home_win, prob_draw, prob_away_win, home_expectancy, away_expectancy

# --- 4. Exibição dos Resultados ---
if st.button("Calcular Probabilidades"):
    p_home, p_draw, p_away, exp_h, exp_a = calculate_probabilities(home_team, away_team)

    st.divider()
    
    # Placar Esperado (xG)
    st.subheader(f"📊 Expectativa de Gols (xG)")
    c1, c2 = st.columns(2)
    c1.metric(home_team, f"{exp_h:.2f} gols")
    c2.metric(away_team, f"{exp_a:.2f} gols")

    st.divider()

    # Probabilidades e Odds Justas
    st.subheader("🎯 Probabilidades & Odds Justas")
    
    # Dataframe para visualização limpa
    results = pd.DataFrame({
        'Resultado': [f"Vitória {home_team}", 'Empate', f"Vitória {away_team}"],
        'Probabilidade (%)': [p_home*100, p_draw*100, p_away*100],
        'Odd Justa (Fair)': [1/p_home, 1/p_draw, 1/p_away]
    })
    
    # Formatação
    st.dataframe(
        results.style.format({
            'Probabilidade (%)': '{:.1f}%',
            'Odd Justa (Fair)': '{:.2f}'
        }), 
        use_container_width=True,
        hide_index=True
    )

    # Dica de Aposta
    st.info("💡 **Como usar:** Se a 'Odd Justa' aqui for MENOR que a Odd da Bet365/Betano, você encontrou uma aposta de valor (+EV).")
