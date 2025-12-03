from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.utils import timezone
import uuid

from rest_framework import generics
from .models import FacilityLoc
from .serializers import FacilityLocSerializer

class StationFacilityListView(generics.ListAPIView):
    serializer_class = FacilityLocSerializer

    def get_queryset(self):
        station_id = self.kwargs['station_id']
        line_id = self.request.query_params.get('line_id')

        qs = FacilityLoc.objects.select_related('station', 'line', 'facility').filter(station_id=station_id)

        if line_id:
            qs = qs.filter(line_id=line_id)
        
        return qs

from apps.journeys.services.guide import (
    load_graph_from_db,
    get_subway_route,
    build_full_guidance,
    RouteBuildError, 
    GuidanceBuildError,
)

from apps.journeys.services.services import validate_stations

SESSION_KEY = "journey"

# ------------------ 함수 정의 PART ------------------

def _init_session(
    request,
    steps,
    start_station,
    start_exit,
    end_station,
    end_exit,
    transfer_stations=None,
    start_line="",
    end_line="",
    transfer_lines=None,
):
    """경로 생성 직후 여정 상태를 세션에 저장."""
    request.session[SESSION_KEY] = {
        "id": str(uuid.uuid4()),
        "created_at": timezone.now().isoformat(),
        "steps": list(steps) if not isinstance(steps, list) else steps,
        "idx": 0,
        "start_station": start_station,
        "start_exit": start_exit,
        "end_station": end_station,
        "end_exit": end_exit,
        "transfer_stations": transfer_stations or [],
        "start_line": start_line,
        "end_line": end_line,
        "transfer_lines": transfer_lines or {},
    }
    request.session.modified = True


def _get_state(request):
    """현재 여정 세션 상태 반환 (없으면 None)."""
    return request.session.get(SESSION_KEY)


def _set_idx(request, idx):
    """현재 step index 업데이트."""
    data_ok = _get_state(request)
    if not data_ok:
        return
    data_ok["idx"] = idx
    request.session[SESSION_KEY] = data_ok
    request.session.modified = True

# ------------------ 함수 정의 PART END ------------------

@require_http_methods(["GET", "POST"])
def route(request):
    """
    GET  : 폼 또는 안내 화면 (세션 여부에 따라)
    POST : 경로 생성 또는 next/prev/restart 내비게이션
    """
    # 기본 컨텍스트 (폼 모드)
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

    # POST: 내비게이션 또는 최초 경로 생성
    if request.method == "POST":
        action = request.POST.get("action")

        # next / prev / restart
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

        # 최초 경로 생성
        start_station = request.POST.get("start_station", "").strip()
        start_exit = request.POST.get("start_exit", "").strip()
        end_station = request.POST.get("end_station", "").strip()
        end_exit = request.POST.get("end_exit", "").strip()

        # 1) 출발/도착역 필수 체크
        if not start_station or not end_station:
            messages.error(request, "출발역/도착역은 필수입니다.")
            return redirect("journeys:route")
        
        # 2) 같은 역 입력 방지
        if start_station == end_station:
            messages.error(request, "같은 역을 입력하셨습니다. 서로 다른 역을 입력해주세요.")
            return redirect("journeys:route")
        
        # 3) 역/출구 유효성 검사 + 보정
        ok, station_pair_or_msg, norm_start_exit, norm_end_exit = validate_stations(
            start_station, end_station, start_exit, end_exit
        )
        if not ok:
            messages.error(request, station_pair_or_msg)
            return redirect("journeys:route")

        # 정규화된 값 사용
        start_station, end_station = station_pair_or_msg
        start_exit = norm_start_exit
        end_exit = norm_end_exit

        try:
            # 4) 역 단위 경로 (3-튜플) 생성
            short_path_list = get_subway_route(
                start_station=start_station,
                start_exit=start_exit,
                end_station=end_station,
                end_exit=end_exit,
            )

            # 5) 그래프 로딩 + 전체 안내 문장 생성
            df_nodes, df_edges = load_graph_from_db()
            steps = build_full_guidance(df_nodes, df_edges, short_path_list)
            if not isinstance(steps, list):
                steps = list(steps)

            # 🔹 라인/환승 정보는 지금 구조상 3-튜플만 있어서
            #    별도 메타 없이 기본값으로 둔다 (UI에서 선택적으로 사용)
            start_line = ""
            end_line = ""
            transfer_stations = []
            transfer_lines = {}

            _init_session(
                request,
                steps=steps,
                start_station=start_station,
                start_exit=start_exit,
                end_station=end_station,
                end_exit=end_exit,
                transfer_stations=transfer_stations,
                start_line=start_line,
                end_line=end_line,
                transfer_lines=transfer_lines,
            )
            return redirect("journeys:route")

        except (RouteBuildError, GuidanceBuildError):
            messages.error(
                request,
                "지하철 경로를 만들지 못했어요. "
                "잠시 후 다시 시도하거나, 출발역·도착역/출구를 바꿔서 다시 시도해 주세요."
            )
            return redirect("journeys:route")
        
        except Exception:
            messages.error(
                request,
                "일시적인 오류가 발생했어요. 잠시 후 다시 시도해 주세요."
            )
            return redirect("journeys:route")

    # GET: new=1 이면 세션 초기화
    if request.GET.get("new") == "1":
        request.session.pop(SESSION_KEY, None)
        request.session.modified = True

    # 세션이 있으면 안내 모드
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
                "transfer_stations": state.get("transfer_stations", []),
                "start_line": state.get("start_line", ""),
                "end_line": state.get("end_line", ""),
                "transfer_lines": state.get("transfer_lines", {}),
                "idx": idx,
                "count": count,
                "step_text": steps[idx] if steps else "(안내 없음)",
                "has_prev": idx > 0,
                "has_next": idx < (count - 1),
            }
        )

    return render(request, "journeys/route.html", context)


def leave(request):
    """여정 세션 초기화 후 메인으로 이동."""
    request.session.pop(SESSION_KEY, None)
    request.session.modified = True
    return redirect("common:index")