from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.utils import timezone
import uuid

from apps.journeys.services.guide import (
    load_graph_from_db,
    load_lines_from_db,
    get_subway_route,
    build_full_guidance,
)

# Session namespace for journey progress
SESSION_KEY = "journey"


def _init_session(request, steps, start_station, start_exit, end_station, end_exit):
    """Initialize journey session state right after route is created."""
    request.session[SESSION_KEY] = {
        "id": str(uuid.uuid4()),
        "created_at": timezone.now().isoformat(),
        "steps": list(steps) if not isinstance(steps, list) else steps,
        "idx": 0,
        "start_station": start_station,
        "start_exit": start_exit,
        "end_station": end_station,
        "end_exit": end_exit,
    }
    request.session.modified = True


def _get_state(request):
    """Return current journey session dict or None."""
    return request.session.get(SESSION_KEY)


def _set_idx(request, idx):
    """Update current step index in session."""
    s = _get_state(request)
    if not s:
        return
    s["idx"] = idx
    request.session[SESSION_KEY] = s
    request.session.modified = True


@require_http_methods(["GET", "POST"])
def route(request):
    """
    Single URL handling both:
      - GET: form or guidance view (depends on session)
      - POST: navigation (next/prev/restart) or initial route submission
    Follows PRG: every POST ends with redirect to this view.
    """
    # default context (form mode)
    context = {
        "mode": "form",
        "step_text": None,
        "idx": 0,
        "count": 0,
        "has_prev": False,
        "has_next": False,
        "start_station": None,
        "start_exit": None,
        "end_station": None,
        "end_exit": None,
    }

    # POST: navigation or initial submission (always redirect back here)
    if request.method == "POST":
        action = request.POST.get("action")

        # navigation actions
        if action in ("next", "prev", "restart"):
            state = _get_state(request)
            if not state:
                messages.error(request, "세션이 만료되었어요. 다시 경로를 생성해 주세요.")
                return redirect("journeys:route")

            steps = state.get("steps", [])
            idx = state.get("idx", 0)

            if action == "next":
                idx = min(idx + 1, max(len(steps) - 1, 0))
            elif action == "prev":
                idx = max(idx - 1, 0)
            elif action == "restart":
                idx = 0

            _set_idx(request, idx)
            return redirect("journeys:route")

        # initial submission
        start_station = request.POST.get("start_station", "").strip()
        start_exit = request.POST.get("start_exit", "").strip()
        end_station = request.POST.get("end_station", "").strip()
        end_exit = request.POST.get("end_exit", "").strip()

        if not start_station or not end_station:
            messages.error(request, "출발역/도착역은 필수입니다.")
            return redirect("journeys:route")

        try:
            lines = load_lines_from_db()
            G = build_subway_graph(lines)

            short_path_list = get_subway_route(
                start_station=start_station,
                start_exit=start_exit,
                end_station=end_station,
                end_exit=end_exit,
                lines=lines,
                G=G,
            )

            if not short_path_list:
                messages.error(request, "경로를 찾지 못했습니다. 역 이름을 확인해 주세요.")
                return redirect("journeys:route")

            df_nodes, df_edges = load_graph_from_db()
            steps = build_full_guidance(df_nodes, df_edges, short_path_list)
            if not isinstance(steps, list):
                steps = list(steps)

            _init_session(
                request,
                steps=steps,
                start_station=start_station,
                start_exit=start_exit,
                end_station=end_station,
                end_exit=end_exit,
            )
            return redirect("journeys:route")

        except Exception as e:
            messages.error(request, f"경로 생성 중 오류: {e}")
            return redirect("journeys:route")

    # GET: optional fresh start, then render form/guide depending on session
    if request.GET.get("new") == "1":
        request.session.pop(SESSION_KEY, None)
        request.session.modified = True

    state = _get_state(request)
    if state:
        steps = state.get("steps", [])
        idx = state.get("idx", 0)
        count = len(steps)

        context.update(
            {
                "mode": "guide",
                "start_station": state.get("start_station"),
                "start_exit": state.get("start_exit"),
                "end_station": state.get("end_station"),
                "end_exit": state.get("end_exit"),
                "idx": idx,
                "count": count,
                "step_text": steps[idx] if steps else "(안내 없음)",
                "has_prev": idx > 0,
                "has_next": idx < (count - 1),
            }
        )

    return render(request, "journeys/route.html", context)


def leave(request):
    """Clear journey session and return to home."""
    request.session.pop(SESSION_KEY, None)
    request.session.modified = True
    return redirect("common:index")