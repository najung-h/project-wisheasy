from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.utils import timezone
import uuid
import re

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

def _extract_line_from_direction(direction_str):
    """
    방면 문자열에서 호선 정보 추출
    예: '2호선 충정로 방면 승강장' -> '2호선'
        '수인분당선 죽전 방면 승강장' -> '수인분당'
    """
    if not direction_str:
        return ""

    # 정규식으로 호선 추출 (숫자호선, 특수노선 등)
    patterns = [
        r'^(\d+호선)',           # 1호선, 2호선 등
        r'^(수인분당)',
        r'^(신분당선)',
        r'^(경의중앙)',
        r'^(공항철도)',
        r'^(우이신설)',
        r'^(경춘)',
    ]

    for pattern in patterns:
        match = re.match(pattern, direction_str)
        if match:
            return match.group(1)

    return ""


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

            # 6) short_path_list에서 호선 및 환승역 정보 추출
            # short_path_list 구조: [(역명, 방면1, 방면2), ...]
            # - 첫 번째: (출발역, 출구, "호선 방면")
            # - 중간: (환승역, "이전호선 방면", "다음호선 방면")
            # - 마지막: (도착역, "호선 방면", 출구)

            start_line = ""
            end_line = ""
            transfer_stations = []
            transfer_lines = {}

            if short_path_list:
                # 출발역 호선 추출 (첫 번째 튜플의 3번째 요소에서)
                if len(short_path_list) > 0 and len(short_path_list[0]) >= 3:
                    start_line = _extract_line_from_direction(short_path_list[0][2])

                # 도착역 호선 추출 (마지막 튜플의 2번째 요소에서)
                if len(short_path_list) > 0 and len(short_path_list[-1]) >= 2:
                    end_line = _extract_line_from_direction(short_path_list[-1][1])

                # 환승역 추출 (첫 번째와 마지막을 제외한 중간 역들)
                if len(short_path_list) > 2:
                    for i in range(1, len(short_path_list) - 1):
                        node = short_path_list[i]
                        if len(node) >= 3:
                            station_name = node[0]
                            # 중간 역의 경우, 3번째 요소(다음 호선 방면)를 환승역의 호선으로 사용
                            next_line = _extract_line_from_direction(node[2])

                            # 중복 방지: 같은 역이 여러 번 나올 수 있음
                            if station_name not in transfer_stations:
                                transfer_stations.append(station_name)
                                transfer_lines[station_name] = next_line

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