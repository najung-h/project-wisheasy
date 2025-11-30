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
)

from apps.journeys.services.services import validate_stations

SESSION_KEY = "journey"

# ------------------ 함수 정의 PART ------------------

# session 초기화 함수 
# def _init_session(request, steps, start_station, start_exit, end_station, end_exit):
#     """Initialize journey session state right after route is created."""
#     request.session[SESSION_KEY] = {
#         "id": str(uuid.uuid4()),
#         "created_at": timezone.now().isoformat(),
#         "steps": list(steps) if not isinstance(steps, list) else steps,
#         "idx": 0,
#         "start_station": start_station,
#         "start_exit": start_exit,
#         "end_station": end_station,
#         "end_exit": end_exit,
#     }
#     request.session.modified = True

def _init_session(request, steps, start_station, start_exit, end_station, end_exit, transfer_stations=None, start_line="", end_line="", transfer_lines=None):
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
        "transfer_stations": transfer_stations or [],
        "start_line": start_line,
        "end_line": end_line,
        "transfer_lines": transfer_lines or {},
    }
    request.session.modified = True

# session에 존재하는 현재 여정 상태 추적 
def _get_state(request):
    """Return current journey session dict or None."""
    return request.session.get(SESSION_KEY)

# index를 늘려서 업데이트 
def _set_idx(request, idx):
    """Update current step index in session."""
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

        # 1) 출발역 or 도착역을 입력하지 않았을 때 
        if not start_station or not end_station:
            messages.error(request, "출발역/도착역은 필수입니다.")
            return redirect("journeys:route")
        
        # 2) 출발역과 도착역에 같은 역을 입력했을 때 
        if start_station == end_station:
            messages.error(request, "같은 역을 입력하셨습니다. 서로 다른 역을 입력해주세요.")
            return redirect("journeys:route")
        
        # services.py에서 역 / 출구 유효성 검사 + 보정
        ok, station_pair_or_msg, norm_start_exit, norm_end_exit = validate_stations(
            start_station, end_station, start_exit, end_exit
        )
        if not ok:
            # station_pair_or_msg 에는 에러 메시지가 들어 있음
            messages.error(request, station_pair_or_msg)
            return redirect("journeys:route")

        # 정상인 경우: 정규화된 역 이름/출구 사용
        start_station, end_station = station_pair_or_msg
        start_exit = norm_start_exit
        end_exit = norm_end_exit
        # ---------- 여기까지 ----------

        try:
            short_path_list = get_subway_route(
                start_station=start_station,
                start_exit=start_exit,
                end_station=end_station,
                end_exit=end_exit,
            )

            if not short_path_list:
                messages.error(request, "경로를 찾지 못했습니다. 역 이름을 확인해 주세요.")
                return redirect("journeys:route")

            df_nodes, df_edges = load_graph_from_db()
            steps = build_full_guidance(df_nodes, df_edges, short_path_list)
            if not isinstance(steps, list):
                steps = list(steps)

            # 각 역의 호선 정보 추출 (프로그레스 바 색상용)
            start_line = short_path_list[0][3][0] if short_path_list else ""
            end_line = short_path_list[-1][3][0] if short_path_list else ""

            # 환승역 추출 및 호선 정보 동시에 수집
            transfer_stations = []
            transfer_lines = {}
            if len(short_path_list) > 2:
                # 첫 출발역과 끝 도착역을 제외하고 순회
                for i in range(1, len(short_path_list) - 1):
                    current_node = short_path_list[i]
                    prev_node = short_path_list[i-1]
                    next_node = short_path_list[i+1]
                    
                    station_name = current_node[0]
                    current_line = current_node[3][0] # 현재 역의 호선
                    
                    # 환승역 판단 로직 (단순 이름 저장이 아니라, 실제 환승이 일어나는지 확인 필요)
                    # 여기서는 간단히 중간에 있는 역들을 환승역으로 간주하고,
                    # 해당 역에서 '이용하는 호선' 정보를 저장합니다.
                    
                    # 이미 저장된 역이면 건너뜀 (한 역에 여러 노드가 있을 수 있음)
                    if station_name not in transfer_stations:
                        transfer_stations.append(station_name)
                        # 환승역의 마커 색상은 '갈아탈 노선' 혹은 '도착한 노선' 중 선택
                        # 여기서는 현재 노드에 할당된 호선을 사용합니다.
                        transfer_lines[station_name] = current_line

            _init_session(
                request,
                steps=steps,
                start_station=start_station,
                start_exit=start_exit,
                end_station=end_station,
                end_exit=end_exit,
                transfer_stations=transfer_stations,
                start_line=start_line,  # 추가
                end_line=end_line,  # 추가
                transfer_lines=transfer_lines,  # 추가
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
    """Clear journey session and return to home."""
    request.session.pop(SESSION_KEY, None)
    request.session.modified = True
    return redirect("common:index")