from __future__ import annotations
from typing import List, Dict, Tuple
from flask import render_template, request, flash
from flask_login import login_required, current_user
from flask_limiter.util import get_remote_address

from . import music_bp
from app.utils.tracing import trace_route
from .services import get_playlists_for_mood, get_cached_recommendations, set_cached_recommendations
from ..ai.tasks import music_rationale, NoMoodSelectedError
from app.utils.mood_resolver import latest_detected_mood_for_current_user
from ..extensions import limiter


# Allowed moods for validation/UI
ALLOWED_MOODS = [
    "anxious","sad","angry","hopeful","tired","stressed","motivated","happy","lonely","confused","grateful","excited","frustrated","guilty","embarrassed","insecure","relieved","proud"
]


@music_bp.route("/music/recommend", methods=["GET", "POST"], endpoint="music_recommend")
@login_required
@limiter.limit("10 per hour", key_func=lambda: str(current_user.id) if current_user.is_authenticated else get_remote_address())
@trace_route("music.music_recommend")
def recommend():
    import time
    start = time.time()
    print(">>> ENTERED /music/recommend")
    print(f"Method={request.method}, User={getattr(current_user, 'id', None)}")

    mood = request.form.get("mood") if request.method == "POST" else None
    auto_mood = latest_detected_mood_for_current_user()
    print(f"Raw form mood={mood}, auto_mood={auto_mood}")

    chosen_mood = None
    error = None

    if mood:
        low = mood.strip().lower()
        if low in ALLOWED_MOODS:
            chosen_mood = low
            print(f"Chosen mood from form: {chosen_mood}")
        else:
            error = "Invalid mood"
            print(f"Invalid mood submitted: {low}")
    elif auto_mood and auto_mood in ALLOWED_MOODS:
        chosen_mood = auto_mood
        print(f"Chosen mood from auto-detect: {chosen_mood}")
    else:
        print("No valid mood found → rendering selection page")
        print(f"<<< EXIT after {round(time.time() - start, 3)}s")
        return render_template(
            "music/recommend.html",
            detected_mood=auto_mood,
            chosen_mood=None,
            payload=None,
            moods=ALLOWED_MOODS,
            error=error,
        )

    # Cache check
    cached, payload = get_cached_recommendations(current_user.id, chosen_mood)
    print(f"Cache hit={cached}, mood={chosen_mood}")

    if not cached:
        try:
            t0 = time.time()
            playlists = get_playlists_for_mood(chosen_mood, limit=3)
            print(f"get_playlists_for_mood returned {len(playlists)} playlists in {round(time.time()-t0,3)}s")

            t0 = time.time()
            rationale_text = music_rationale(chosen_mood, current_user.language_pref or 'en')
            print(f"music_rationale returned {len(rationale_text or '')} chars in {round(time.time()-t0,3)}s")

            payload = {"mood": chosen_mood, "rationale": rationale_text, "playlists": playlists}
            set_cached_recommendations(current_user.id, chosen_mood, payload)
            print("Payload cached successfully")
        except NoMoodSelectedError:
            print("NoMoodSelectedError raised → rendering error page")
            return render_template(
                "music/recommend.html",
                detected_mood=auto_mood,
                chosen_mood=None,
                payload=None,
                moods=ALLOWED_MOODS,
                error="Please choose a mood to continue.",
            )
        except Exception as e:
            print("ERROR in generating recommendations:", type(e).__name__, str(e))
            import traceback; traceback.print_exc()
            payload = None

    if request.method == "POST":
        flash("Updated mood recommendations 🎧", "success")

    print(f"<<< EXIT OK after {round(time.time() - start, 3)}s, mood={chosen_mood}, cache_hit={cached}")
    return render_template(
        "music/recommend.html",
        detected_mood=auto_mood,
        chosen_mood=chosen_mood,
        payload=payload,
        moods=ALLOWED_MOODS,
        error=error,
    )
# def recommend():
#     mood = request.form.get("mood") if request.method == "POST" else None
#     auto_mood = latest_detected_mood_for_current_user()

#     chosen_mood = None
#     error = None
#     if mood:
#         low = mood.strip().lower()
#         if low in ALLOWED_MOODS:
#             chosen_mood = low
#         else:
#             error = "Invalid mood; please choose one of the available options."
#     elif auto_mood and auto_mood in ALLOWED_MOODS:
#         chosen_mood = auto_mood

#     if not chosen_mood:
#         # Render selection UI only
#         return render_template(
#             "music/recommend.html",
#             detected_mood=auto_mood,
#             chosen_mood=None,
#             payload=None,
#             moods=ALLOWED_MOODS,
#             error=error,
#         )

#     # Read cache
#     cached, payload = get_cached_recommendations(current_user.id, chosen_mood)
#     if not cached:
#         try:
#             playlists = get_playlists_for_mood(chosen_mood, limit=3)
#             rationale_text = music_rationale(chosen_mood, current_user.language_pref or "en")
#             payload = {"mood": chosen_mood, "rationale": rationale_text, "playlists": playlists}
#             set_cached_recommendations(current_user.id, chosen_mood, payload)
#         except NoMoodSelectedError:
#             return render_template(
#                 "music/recommend.html",
#                 detected_mood=auto_mood,
#                 chosen_mood=None,
#                 payload=None,
#                 moods=ALLOWED_MOODS,
#                 error="Please choose a mood to continue.",
#             )

#     if request.method == "POST":
#         flash("Updated mood recommendations 🎧", "success")

#     return render_template(
#         "music/recommend.html",
#         detected_mood=auto_mood,
#         chosen_mood=chosen_mood,
#         payload=payload,
#         moods=ALLOWED_MOODS,
#         error=error,
#     )
