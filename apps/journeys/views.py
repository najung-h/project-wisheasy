from django.shortcuts import render
# 뷰 데코레이터(특정 요청만 처리하도록 제한)
from django.views.decorators.http import require_http_methods
from apps.journeys.services.guide import (
    load_graph_from_db,
    load_lines_from_db,
    get_subway_route,
    build_full_guidance,
)


# Create your views here.
# 사용자의 경로 안내 우선 순위를 설정한다.
@require_http_methods(["GET", "POST"])
def route(request):
    context = {"steps": None}

    if request.method == "POST":
        start_station = request.POST.get("start_station", "").strip()
        start_exit    = request.POST.get("start_exit", "").strip()       # 예: "2번출구"
        end_station   = request.POST.get("end_station", "").strip()
        end_exit      = request.POST.get("end_exit", "").strip()         # 예: "4번출구"

        # 1) Lines → G (DB 기반)
        lines = load_lines_from_db()
        G = build_subway_graph(lines)

        # 2) 유저 입력 → short_path_list
        short_path_list = get_subway_route(
            start_station=start_station,
            start_exit=start_exit,
            end_station=end_station,
            end_exit=end_exit,
            lines=lines,
            G=G,
        )

        # 3) Nodes/Edges(ORM) → DataFrame
        df_nodes, df_edges = load_graph_from_db()

        # 4) 안내 스텝 생성
        steps = build_full_guidance(df_nodes, df_edges, short_path_list)

        context.update({
            "steps": steps,
            "start_station": start_station,
            "start_exit": start_exit,
            "end_station": end_station,
            "end_exit": end_exit,
        })

    return render(request, "journeys/route.html", context)
