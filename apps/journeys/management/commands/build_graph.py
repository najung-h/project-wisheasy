from django.core.management.base import BaseCommand
import networkx as nx
from apps.journeys.models import Lines

GRAPH_CACHE = None  # 서버 실행 후 유지할 전역 그래프
RING_LINES = {"2호선"}  # 순환선 목록


def build_graph():
    """DB 데이터를 기반으로 최소환승 그래프 구성"""
    G = nx.Graph()

    # 1. DB에서 노선별 역 순서 dict 생성
    qs = Lines.objects.values("line", "station", "order_in_line")
    rows = sorted(list(qs), key=lambda r: (r["line"], r["order_in_line"]))

    line_data = {}  # {"2호선": ["시청", "을지로입구", ...], ...}
    for r in rows:
        line_data.setdefault(r["line"], []).append(r["station"])

    # 2. 호선별 인접역 연결 + 순환선 처리
    for line_name, stations in line_data.items():
        # 인접역
        for i, station in enumerate(stations):
            node = f"{station}-{line_name}"
            G.add_node(node)
            if i > 0:
                prev_node = f"{stations[i-1]}-{line_name}"
                G.add_edge(prev_node, node, weight=0)  # 인접역

        # 순환선이면 첫 역 ↔ 마지막 역도 연결
        if line_name in RING_LINES and len(stations) > 1:
            first_node = f"{stations[0]}-{line_name}"
            last_node = f"{stations[-1]}-{line_name}"
            G.add_edge(first_node, last_node, weight=0)

    # 3. 환승 연결 (역 이름 동일, 호선 다름)
    all_nodes = list(G.nodes)
    for i, n1 in enumerate(all_nodes):
        name1, line1 = n1.split("-")
        for j in range(i + 1, len(all_nodes)):
            n2 = all_nodes[j]
            name2, line2 = n2.split("-")
            if name1 == name2 and line1 != line2:
                G.add_edge(n1, n2, weight=1)  # 환승 비용 1

    print("✅ Subway graph built successfully.")
    return G


def get_graph():
    """전역 그래프 캐시 반환"""
    global GRAPH_CACHE
    if GRAPH_CACHE is None:
        GRAPH_CACHE = build_graph()
    return GRAPH_CACHE


class Command(BaseCommand):
    help = "서버 실행 시 그래프를 메모리에 빌드합니다."

    def handle(self, *args, **options):
        global GRAPH_CACHE
        self.stdout.write("🚆 Building subway graph from DB...")
        GRAPH_CACHE = build_graph()
        self.stdout.write(self.style.SUCCESS("Graph built successfully ✅"))
        self.stdout.write(
            f"노드 수: {len(GRAPH_CACHE.nodes)} / 엣지 수: {len(GRAPH_CACHE.edges)}"
        )