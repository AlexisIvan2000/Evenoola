"""Tests unitaires du scoring : logique pure, pas d'I/O.

On verifie les 3 paliers du scoring adaptatif et la generation des reasons.
"""
from app.application.services.match_reasons_service import generate_reasons
from app.application.services.scoring_service import score_event, score_events


def _profile(artists=None, genres=None):
    return {"artists": artists or {}, "genres": genres or {}}


def _artist_entry(weight, name="X", followed=False, rank_short=None, rank_medium=None, rank_long=None):
    return {
        "id": "spid",
        "name": name,
        "weight": weight,
        "followed": followed,
        "rank_short": rank_short,
        "rank_medium": rank_medium,
        "rank_long": rank_long,
        "genres": [],
    }


def _event(spotify_ids: list[str], genres: list[str], event_id="ev1"):
    return {
        "id": event_id,
        "attractions": [{"spotify_id": sid, "name": sid} for sid in spotify_ids],
        "genres": genres,
    }


# ---------- Scoring : 3 paliers adaptatifs ----------

def test_strong_artist_match_dominates_genre():
    """artist_score >= 0.7 => genre_score est multiplie par 0.15 seulement."""
    profile = _profile(
        artists={"a1": _artist_entry(0.6)},  # >= 0.7 path declenche, plus simple a verifier
        genres={"rock": 1.0, "indie": 0.4},
    )
    # On force le palier >= 0.7 en mettant 0.7 exact
    profile["artists"]["a1"]["weight"] = 0.7
    event = _event(spotify_ids=["a1"], genres=["rock", "indie"])

    s = score_event(event, profile)

    assert s.artist_score == 0.7
    # genre_sum = 1.0+0.4 = 1.4 ; normalise par 2 genres = 0.7
    assert s.genre_score == 0.7
    # palier 1 : artist*1 + genre*0.15 = 0.7 + 0.105 = 0.805
    assert s.score == round(0.7 + 0.7 * 0.15, 4)
    assert s.score_pct == int(s.score * 100)  # 80, sous le cap


def test_partial_artist_match_uses_medium_genre_weight():
    """0 < artist_score < 0.7 => genre_score x 0.30."""
    profile = _profile(
        artists={"a1": _artist_entry(0.4)},
        genres={"jazz": 1.0},
    )
    event = _event(spotify_ids=["a1"], genres=["jazz"])

    s = score_event(event, profile)

    assert s.artist_score == 0.4
    assert s.genre_score == 1.0  # un seul genre, sum/1
    assert s.score == round(0.4 + 1.0 * 0.30, 4)


def test_no_artist_match_boosts_genre_score():
    """artist_score == 0 => genre_score x 0.80 (le genre devient le seul signal)."""
    profile = _profile(
        artists={"other": _artist_entry(1.0)},
        genres={"techno": 0.9},
    )
    event = _event(spotify_ids=["unknown"], genres=["techno"])

    s = score_event(event, profile)

    assert s.artist_score == 0.0
    assert s.genre_score == 0.9
    assert s.score == round(0.9 * 0.80, 4)


# ---------- Cap a 99% ----------

def test_score_pct_capped_at_99():
    """Meme avec un score brut > 1.0 (plusieurs artistes matches), on capper a 99."""
    profile = _profile(
        artists={
            "a1": _artist_entry(1.0),
            "a2": _artist_entry(1.0),
        },
        genres={"rock": 1.0},
    )
    event = _event(spotify_ids=["a1", "a2"], genres=["rock"])

    s = score_event(event, profile)

    assert s.artist_score == 2.0
    assert s.score_pct == 99


# ---------- Normalisation par nb genres event ----------

def test_genre_score_normalized_by_event_genre_count():
    """Un event avec 5 genres ne doit pas avoir un avantage injuste sur un avec 1 genre."""
    profile = _profile(genres={"a": 1.0, "b": 1.0, "c": 1.0, "d": 1.0, "e": 1.0})

    event_one = _event(spotify_ids=[], genres=["a"])
    event_many = _event(spotify_ids=[], genres=["a", "b", "c", "d", "e"])

    s1 = score_event(event_one, profile)
    s5 = score_event(event_many, profile)

    # Les deux ont 100% de match, donc apres normalisation -> meme score.
    assert s1.genre_score == s5.genre_score == 1.0


# ---------- Tri + filtrage ----------

def test_score_events_sorts_desc_and_filters_zero():
    profile = _profile(artists={"hit": _artist_entry(0.8)})
    events = [
        _event(spotify_ids=["miss"], genres=[], event_id="zero"),    # score = 0, filtre
        _event(spotify_ids=["hit"], genres=[], event_id="hit"),
    ]
    out = score_events(events, profile)
    assert [s.event_id for s in out] == ["hit"]


# ---------- Match reasons ----------

def test_reasons_followed_label_prioritised():
    profile = _profile(
        artists={"a1": _artist_entry(0.9, name="Arctic Monkeys", followed=True, rank_short=3)},
    )
    event = _event(spotify_ids=["a1"], genres=[])

    s = score_event(event, profile)
    reasons = generate_reasons(s)

    assert reasons[0].type == "artist_followed"
    assert "Arctic Monkeys" in reasons[0].label
    # Le rank artist_top doit aussi etre present si dans le top.
    types = [r.type for r in reasons]
    assert "artist_top" in types


def test_reasons_capped_at_three():
    profile = _profile(
        artists={
            "a1": _artist_entry(0.9, name="A1", followed=True, rank_short=1),
            "a2": _artist_entry(0.8, name="A2", followed=True, rank_short=2),
            "a3": _artist_entry(0.7, name="A3", followed=True, rank_short=3),
        },
        genres={"rock": 1.0},
    )
    event = _event(spotify_ids=["a1", "a2", "a3"], genres=["rock"])

    s = score_event(event, profile)
    reasons = generate_reasons(s)

    assert len(reasons) == 3


def test_reasons_genre_only_when_no_artist_match():
    profile = _profile(genres={"techno": 0.9, "house": 0.6})
    event = _event(spotify_ids=[], genres=["techno", "house"])

    s = score_event(event, profile)
    reasons = generate_reasons(s)

    assert len(reasons) == 1
    assert reasons[0].type == "genre_match"
    assert "techno" in reasons[0].label and "house" in reasons[0].label
