
import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy.stats import poisson

st.set_page_config(
    page_title="Arbitrage Engine v6",
    page_icon="⚽",
    layout="wide"
)

st.title("⚽ Arbitrage Engine v6")
st.caption("Analyse de matchs • Probabilités • Value betting")

st.sidebar.header("Configuration du match")

home = st.sidebar.text_input("Équipe à domicile", "PSG")
away = st.sidebar.text_input("Équipe extérieure", "Lyon")

hxg = st.sidebar.number_input(
    "xG domicile", 0.1, 5.0, 1.8, 0.1
)
axg = st.sidebar.number_input(
    "xG extérieur", 0.1, 5.0, 1.2, 0.1
)

bankroll = st.sidebar.number_input(
    "Bankroll (€)", 10.0, 100000.0, 500.0, 10.0
)

st.subheader("Cotes décimales")

c1, c2, c3 = st.columns(3)

with c1:
    odds1 = st.number_input(
        "Victoire domicile", 1.01, 100.0, 2.0, 0.05
    )

with c2:
    oddsn = st.number_input(
        "Match nul", 1.01, 100.0, 3.5, 0.05
    )

with c3:
    odds2 = st.number_input(
        "Victoire extérieur", 1.01, 100.0, 3.8, 0.05
    )

# Modèle de Poisson
goals = np.arange(11)

ph = poisson.pmf(goals, hxg)
pa = poisson.pmf(goals, axg)

matrix = np.outer(ph, pa)

p1 = float(np.tril(matrix, -1).sum())
pn = float(np.trace(matrix))
p2 = float(np.triu(matrix, 1).sum())

total = p1 + pn + p2
p1, pn, p2 = p1 / total, pn / total, p2 / total

st.subheader("Probabilités estimées")

a, b, c = st.columns(3)
a.metric(f"Victoire {home}", f"{p1:.1%}")
b.metric("Match nul", f"{pn:.1%}")
c.metric(f"Victoire {away}", f"{p2:.1%}")

# Calcul de la valeur attendue et des mises
markets = [
    (f"Victoire {home}", p1, odds1),
    ("Match nul", pn, oddsn),
    (f"Victoire {away}", p2, odds2)
]

results = []

for name, prob, odds in markets:
    ev = prob * odds - 1
    fair = 1 / prob if prob > 0 else 0

    kelly = max(
        0.0,
        (prob * odds - 1) / (odds - 1)
    )

    stake = min(
        bankroll * kelly * 0.25,
        bankroll * 0.05
    )

    results.append({
        "Marché": name,
        "Probabilité": f"{prob:.1%}",
        "Cote": odds,
        "Cote juste": round(fair, 2),
        "EV": f"{ev:+.1%}",
        "Mise indicative (€)": round(stake, 2),
        "Analyse": "EV positive" if ev > 0 else "Pas de value"
    })

df = pd.DataFrame(results)

st.subheader("Analyse des marchés")
st.dataframe(df, use_container_width=True, hide_index=True)

st.subheader("Matrice des scores")

score_data = matrix[:6, :6] * 100

fig = go.Figure(
    data=go.Heatmap(
        z=score_data,
        x=list(range(6)),
        y=list(range(6)),
        colorscale="Blues",
        text=np.round(score_data, 1),
        texttemplate="%{text}%",
        hovertemplate=(
            "Buts domicile : %{y}<br>"
            "Buts extérieur : %{x}<br>"
            "Probabilité : %{z:.2f}%"
            "<extra></extra>"
        )
    )
)

fig.update_layout(
    xaxis_title=f"Buts de {away}",
    yaxis_title=f"Buts de {home}",
    height=450
)

st.plotly_chart(fig, use_container_width=True)

st.subheader("Scores les plus probables")

scores = []

for h in range(6):
    for a in range(6):
        scores.append({
            "Score": f"{home} {h} - {a} {away}",
            "Probabilité": matrix[h, a]
        })

top = sorted(
    scores,
    key=lambda x: x["Probabilité"],
    reverse=True
)[:5]

st.dataframe(
    pd.DataFrame([
        {
            "Score": x["Score"],
            "Probabilité": f"{x['Probabilité']:.2%}"
        }
        for x in top
    ]),
    use_container_width=True,
    hide_index=True
)

st.download_button(
    "Exporter les analyses en CSV",
    df.to_csv(index=False).encode("utf-8-sig"),
    "analyses_arbitrage.csv",
    "text/csv"
)

st.warning(
    "Les cotes sont saisies manuellement. "
    "Aucune API en direct n'est connectée. "
    "Les estimations ne garantissent aucun gain."
)
