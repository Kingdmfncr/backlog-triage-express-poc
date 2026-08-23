import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.backlog import (
    classify_quadrant,
    load_backlog,
    score_effort_proxy,
    score_impact,
    score_urgence,
    structurer_backlog,
    user_story_template,
)

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "backlog_demo_github_streamlit.json")


def _load_real_backlog():
    with open(DATA_PATH, encoding="utf-8") as f:
        items = json.load(f)
    return load_backlog(items)


def test_load_backlog_real_data():
    df = _load_real_backlog()
    assert len(df) == 30
    assert {"id", "titre", "reactions", "commentaires", "labels"}.issubset(df.columns)


def test_score_impact_is_1_to_5_and_correlates_with_engagement():
    df = _load_real_backlog()
    impact = score_impact(df)
    assert impact.between(1, 5).all()
    # l'item avec le plus d'engagement (issue #611, "Export to standalone HTML file",
    # 285 réactions + 65 commentaires, le plus haut du jeu de données réel) doit être
    # scoré au maximum
    idx_top = (df["reactions"] + df["commentaires"]).idxmax()
    assert impact.loc[idx_top] == 5


def test_score_urgence_boosts_confirmed_and_lowers_unlikely():
    df = _load_real_backlog()
    urgence = score_urgence(df)
    idx_unlikely = df[df["labels"].apply(lambda ls: any("unlikely" in l for l in ls))].index
    idx_confirmed = df[df["labels"].apply(lambda ls: any("confirmed" in l or "likely" in l for l in ls))].index
    assert len(idx_unlikely) > 0 and len(idx_confirmed) > 0
    assert urgence.loc[idx_unlikely].mean() < urgence.loc[idx_confirmed].mean()


def test_score_effort_proxy_in_range():
    df = _load_real_backlog()
    effort = score_effort_proxy(df)
    assert effort.between(1, 5).all()


def test_classify_quadrant_all_four_cases():
    assert classify_quadrant(5, 1) == "Quick win"
    assert classify_quadrant(5, 5) == "Big bet"
    assert classify_quadrant(1, 1) == "Fill-in"
    assert classify_quadrant(1, 5) == "Time sink"


def test_user_story_template_never_invents_role_or_benefit():
    story = user_story_template("Add dark mode support")
    assert story.startswith("En tant que ___")
    assert story.endswith("afin de ___.")
    assert "add dark mode support" in story.lower()


def test_structurer_backlog_end_to_end_on_real_data():
    df = _load_real_backlog()
    result = structurer_backlog(df)
    assert len(result) == len(df)
    assert {"impact", "urgence", "effort_propose", "quadrant", "user_story_scaffold"}.issubset(result.columns)
    assert result["quadrant"].isin(["Quick win", "Big bet", "Fill-in", "Time sink"]).all()
    # trié par impact décroissant
    assert result["impact"].is_monotonic_decreasing or len(result["impact"].unique()) == 1
