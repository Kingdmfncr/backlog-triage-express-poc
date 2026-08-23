"""Backlog Triage Express — Streamlit. Voir README.md pour le contexte métier."""
import json

import pandas as pd
import streamlit as st

from src.backlog import load_backlog, structurer_backlog, user_story_ai

st.set_page_config(page_title="Backlog Triage Express", page_icon="🗃️", layout="wide")

C_TEXT = "#1D1D1F"
C_MUTED = "#6E6E73"
QUADRANT_COLOR = {"Quick win": "#00C896", "Big bet": "#F5C842", "Fill-in": "#6E6E73", "Time sink": "#E85D5D"}

st.markdown(f"<h1 style='color:{C_TEXT};'>🗃️ Backlog Triage Express</h1>", unsafe_allow_html=True)
st.markdown(
    f"<p style='color:{C_MUTED};'>Sprint <strong>Structuration de backlog produit</strong> — "
    f"priorisation impact/effort/urgence et reformulation en user stories. "
    f"Voir <code>README.md</code> pour le contexte.</p>",
    unsafe_allow_html=True,
)
st.markdown("---")

mode = st.radio(
    "Backlog à structurer",
    ["Utiliser le backlog de démo (30 vraies issues GitHub streamlit/streamlit)", "Uploader mon propre backlog (CSV/JSON)"],
    horizontal=True,
)

if mode.startswith("Utiliser"):
    st.info(
        "Scénario : 30 vraies demandes d'évolution ouvertes du dépôt open-source **streamlit/streamlit** "
        "(label `type:enhancement`, récupérées via l'API publique GitHub) — un backlog réel, non trié, "
        "exactement comme celui d'un client au démarrage du sprint. Détail dans PROMPT_LOG.md."
    )
    with open("data/backlog_demo_github_streamlit.json", encoding="utf-8") as f:
        items = json.load(f)
    df = load_backlog(items)
else:
    uploaded = st.file_uploader("Fichier backlog (colonnes attendues : id, titre, description, reactions, commentaires, labels)", type=["csv", "json"])
    if not uploaded:
        st.warning("Dépose un fichier pour continuer.")
        st.stop()
    if uploaded.name.endswith(".json"):
        items = json.load(uploaded)
    else:
        items = pd.read_csv(uploaded).to_dict("records")
    df = load_backlog(items)

result = structurer_backlog(df)

tab_matrice, tab_liste, tab_stories, tab_export = st.tabs(
    ["📐 Matrice impact/effort", "📋 Backlog priorisé", "✍️ User stories", "⬇️ Export"]
)

with tab_matrice:
    st.caption(
        "Impact = engagement mesuré (réactions + commentaires, quantiles du backlog chargé) · "
        "Effort = proxy de départ (surface fonctionnelle touchée), **éditable dans l'onglet Backlog priorisé** · "
        "Urgence = labels réels (confirmé/probable, écarté, friction signalée)."
    )
    chart_df = result.rename(columns={"effort_propose": "effort"})
    st.scatter_chart(chart_df, x="effort", y="impact", size="urgence", color="quadrant", height=420)
    cols = st.columns(4)
    for i, (q, color) in enumerate(QUADRANT_COLOR.items()):
        n = (result["quadrant"] == q).sum()
        cols[i].markdown(f"<div style='background:{color}22;border-radius:8px;padding:10px;text-align:center;'>"
                          f"<strong style='color:{color};'>{q}</strong><br>{n} item(s)</div>", unsafe_allow_html=True)

with tab_liste:
    st.caption("Effort = proxy de départ, modifiable ci-dessous avant toute décision finale (colonne éditable).")
    edited = st.data_editor(
        result[["id", "titre", "quadrant", "impact", "urgence", "effort_propose", "reactions", "commentaires", "labels"]],
        column_config={"effort_propose": st.column_config.NumberColumn("Effort (éditable)", min_value=1, max_value=5)},
        disabled=["id", "titre", "quadrant", "impact", "urgence", "reactions", "commentaires", "labels"],
        use_container_width=True,
        height=500,
        key="editor",
    )

with tab_stories:
    st.markdown(
        "Scaffold disponible pour chaque item sans IA (`en tant que ___ / afin de ___`, jamais deviné). "
        "Une clé API Anthropic optionnelle (BYOK, jamais stockée) permet un premier jet automatique à relire."
    )
    api_key = st.text_input("Clé API Anthropic (optionnelle)", type="password")
    n_preview = st.slider("Nombre d'items à afficher", 1, len(result), min(5, len(result)))
    for _, row in result.head(n_preview).iterrows():
        with st.expander(f"#{row['id']} — {row['titre']} · {row['quadrant']}"):
            st.markdown(f"**Scaffold manuel :** {row['user_story_scaffold']}")
            if api_key:
                ai_story = user_story_ai(row["titre"], row["description"], api_key)
                if ai_story:
                    st.markdown(f"**Premier jet IA (à relire) :** {ai_story}")
                else:
                    st.warning("Appel IA indisponible — scaffold manuel affiché ci-dessus.")

with tab_export:
    csv = result.drop(columns=["description"]).to_csv(index=False)
    st.download_button("⬇️ Télécharger le backlog structuré (CSV)", csv, file_name="backlog_structure.csv", mime="text/csv")
    st.dataframe(result.drop(columns=["description"]), use_container_width=True)
