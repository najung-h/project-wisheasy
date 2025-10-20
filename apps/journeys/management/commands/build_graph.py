from django.core.management.base import BaseCommand
import networkx as nx
from apps.journeys.models import Lines

GRAPH_CACHE = None  # 서버 실행 후 유지할 전역 그래프

def build_graph():
    """DB 데이터를 기반으로 최소환승 그래프 구성"""
    G = nx.Graph()

    # 1. 호선별 역 목록 불러오기
    line_names = Lines.objects.values_list('line', flat=True).distinct()

    # 2. 호선별 인접역 연결
    for line in line_names:
        stations = (
            Lines.objects.filter(line=line)
            .order_by('order_in_line')
            .values_list('station', flat=True)
        )
        for i in range(len(stations)):
            node = f"{stations[i]}-{line}"
            G.add_node(node)
            if i > 0:
                prev_node = f"{stations[i-1]}-{line}"
                G.add_edge(prev_node, node, weight=0)  # 인접역

    # 3. 환승 연결 (역 이름 동일, 호선 다름)
    all_nodes = list(G.nodes)
    for n1 in all_nodes:
        name1, line1 = n1.split("-")
        for n2 in all_nodes:
            name2, line2 = n2.split("-")
            if name1 == name2 and line1 != line2:
                G.add_edge(n1, n2, weight=1)

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
        self.stdout.write(self.style.SUCCESS(f"Graph built successfully ✅"))
        self.stdout.write(f"노드 수: {len(GRAPH_CACHE.nodes)} / 엣지 수: {len(GRAPH_CACHE.edges)}")