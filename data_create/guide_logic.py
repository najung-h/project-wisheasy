import pandas as pd
from collections import deque
from typing import List, Tuple, Optional, Dict
import os

# 0) CSV 로드
def load_graph(
    nodes_csv: str = "line2_nodes_최종.csv",
    edges_csv: str = "line2_edges_최종.csv",
) -> Tuple[pd.DataFrame, pd.DataFrame]:

    # 현재 파일(guide_logic.py)의 경로 기준으로 output_data 폴더 지정
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, "output_data")

    # CSV 경로 설정
    nodes_path = os.path.join(data_dir, nodes_csv)
    edges_path = os.path.join(data_dir, edges_csv)

    # CSV 로드
    df_nodes = pd.read_csv(nodes_path, encoding="utf-8-sig")
    df_edges = pd.read_csv(edges_path, encoding="utf-8-sig")

    # 가벼운 정규화(양쪽 공백 제거 등)
    for c in ["station", "node_id", "node_name", "type"]:
        if c in df_nodes.columns:
            df_nodes[c] = df_nodes[c].astype(str).str.strip()
    for c in ["station", "source", "target", "relation"]:
        if c in df_edges.columns:
            df_edges[c] = df_edges[c].astype(str).str.strip()

    # 없는 컬럼 대비 기본값
    if "운영이상여부" not in df_edges.columns:
        df_edges["운영이상여부"] = 0
    if "다음역하차_에스컬레이터_유무" not in df_edges.columns:
        df_edges["다음역하차_에스컬레이터_유무"] = 0

    return df_nodes, df_edges


# 1) df_nodes에서 역명(station)과 노드명(node_name)이 모두 일치하는 행을 찾고 그 행의 node_id를 반환
def get_node_id(df_nodes: pd.DataFrame, station: str, node_name: str) -> Optional[str]:
    sub = df_nodes[(df_nodes["station"] == station) & (df_nodes["node_name"] == node_name)]
    if len(sub) == 0:
        return None
    # 여러 개인 경우 첫 개체 사용
    return sub["node_id"].iloc[0]


# 2) BFS: 한 역(station) 내부에서 start_id → goal_id 최단 경로(노드열) 탐색
#    - 엣지는 해당 역으로 필터링된 df_edges_sub를 사용
def bfs_path_node_ids(df_edges_sub: pd.DataFrame, start_id: str, goal_id: str) -> Optional[List[str]]:
    # 인접 리스트 구성 (방향 그래프)
    adj: Dict[str, List[str]] = {}
    for _, r in df_edges_sub.iterrows():
        s = r["source"]
        t = r["target"]
        adj.setdefault(s, []).append(t)

    # BFS
    q = deque([start_id])
    visited = {start_id: None}  # 부모 포인터
    while q:
        cur = q.popleft()
        if cur == goal_id:
            break
        for nxt in adj.get(cur, []):
            if nxt not in visited:
                visited[nxt] = cur
                q.append(nxt)

    if goal_id not in visited:
        return None

    # BFS가 만든‘부모 포인터(visited 딕셔너리)’를 이용해 경로를 되짚어 올라간 뒤, 순서를 뒤집어(start→goal) 돌려주는 코드
    path = []
    node = goal_id
    while node is not None:
        path.append(node)
        node = visited[node]
    path.reverse()
    return path  # [start_id, ..., goal_id]



# 3) 노드 경로 → 엣지 경로로 변환
def to_edge_rows(df_edges_sub: pd.DataFrame, node_path: List[str]) -> pd.DataFrame:
    rows = []
    for a, b in zip(node_path, node_path[1:]):
        hit = df_edges_sub[(df_edges_sub["source"] == a) & (df_edges_sub["target"] == b)]
        if len(hit) == 0:
            continue
        rows.append(hit.iloc[0])
    if not rows:
        return pd.DataFrame(columns=df_edges_sub.columns)
    return pd.DataFrame(rows)


# 4) relation 텍스트 후처리(운영 이상 시 안내 문구 치환)
#    - 운영이상여부 == 1 이면 '에스컬레이터' → '계단/도보(에스컬레이터 점검)'
def render_relation(relation: str, malfunction: int) -> str:
    if int(malfunction) == 1:
        return relation.replace("에스컬레이터", "계단/도보(에스컬레이터 점검)")
    return relation


# 5) 목적지가 승강장인 경우: 탑승구 노드로 1단계 더 연장
#    - df_edges_sub에서 '다음역하차_에스컬레이터_유무' == 1 인 edge를 우선 선택
def extend_platform_to_gate(
    df_nodes_sub: pd.DataFrame,
    df_edges_sub: pd.DataFrame,
    platform_node_id: str,
) -> Optional[pd.DataFrame]:
    # platform_node_id에서 나가는 엣지들 중 탑승구(type=='탑승구')로 연결되는 후보를 찾는다
    out_edges = df_edges_sub[df_edges_sub["source"] == platform_node_id].copy()
    if out_edges.empty:
        return None

    # 후보 타겟이 탑승구인지 필터
    gate_targets = out_edges.merge(
        df_nodes_sub[["node_id", "type"]],
        left_on="target", right_on="node_id", how="left"
    )
    gate_targets = gate_targets[gate_targets["type"] == "탑승구"].copy()
    if gate_targets.empty:
        return None

    # 다음역하차_에스컬레이터_유무 == 1 가 우선, 없으면 0 중 아무거나
    gate_targets = gate_targets.sort_values(by="다음역하차_에스컬레이터_유무", ascending=False)
    chosen = gate_targets.iloc[0:1]  # 하나만 선택
    return chosen[gate_targets.columns.intersection(df_edges_sub.columns)]


# 6) 세그먼트(튜플)별 BFS 경로 안내 생성
#    short_path의 각 원소는 다음 형태를 가정:
#    - 환승 없음: (출발역,  'x번출구',            'A호선 B방면 승강장')
#                  (도착역, 'A호선 B방면 승강장', 'x번출구')
#    - 환승 있음: (출발역, 'x번출구',             'A호선 B방면 승강장'),
#                 (환승역, 'A호선 B방면 승강장', 'C호선 D방면 승강장'),
#                 (도착역, 'C호선 D방면 승강장', 'x번출구')
# 한 역(station) 안에서 시작 노드 → 도착 노드까지의 안내 문구(step)들을 만드는로직
'''
입력: df_nodes, df_edges, station, start_name, goal_name
처리:
1. 해당 역의 서브그래프로 필터링
2. 시작/도착 노드의 node_id 찾기
3. BFS로 최단 경로(노드열) 찾기
4. 노드열 → 엣지열로 바꾸고, relation을 안내문으로 뽑기
5. 도착지가 승강장이면, “승강장→탑승구” 한 단계 추가 확장
'''
def build_guidance_for_segment(
    df_nodes: pd.DataFrame,
    df_edges: pd.DataFrame,
    station: str,
    start_name: str,
    goal_name: str,
) -> List[str]:
    # 해당 역으로 필터링
    df_nodes_sub = df_nodes[df_nodes["station"] == station].copy()
    df_edges_sub = df_edges[df_edges["station"] == station].copy()

    # 시작/도착 node_id 식별
    start_id = get_node_id(df_nodes, station, start_name)
    goal_id  = get_node_id(df_nodes, station, goal_name)
    if start_id is None or goal_id is None:
        return [f"[{station}] 안내 실패: 노드 식별 불가 (start='{start_name}', goal='{goal_name}')"]

    # BFS로 노드 경로 탐색
    node_path = bfs_path_node_ids(df_edges_sub, start_id, goal_id)
    if node_path is None:
        return [f"[{station}] 안내 실패: 경로 없음 (start='{start_name}', goal='{goal_name}')"]

    # 노드경로 → 엣지경로, relation 나열
    edges_path = to_edge_rows(df_edges_sub, node_path)
    steps = []
    for _, r in edges_path.iterrows():
        steps.append(
            render_relation(r["relation"], r.get("운영이상여부", 0))
        )

    # 목적지가 승강장인 경우: 탑승구까지 1단계 연장(우선순위: 다음역하차_에스컬레이터_유무 == 1)
    # goal 노드의 type 확인
    goal_row = df_nodes_sub[df_nodes_sub["node_id"] == goal_id]
    if not goal_row.empty and goal_row["type"].iloc[0] == "승강장":
        chosen_edge_to_gate = extend_platform_to_gate(df_nodes_sub, df_edges_sub, goal_id)
        if chosen_edge_to_gate is not None and not chosen_edge_to_gate.empty:
            er = chosen_edge_to_gate.iloc[0]
            steps.append(
                render_relation(er["relation"], er.get("운영이상여부", 0))
            )

    return steps


# 7) 전체 안내 함수
#    short_path_list: List[Tuple[str, str, str]]
#    → 각 튜플(station, start_name, goal_name)을 순회하며 BFS 안내 단계 생성
def build_full_guidance(
    df_nodes: pd.DataFrame,
    df_edges: pd.DataFrame,
    short_path_list: List[Tuple[str, str, str]],
) -> List[str]:
    all_steps: List[str] = []
    for (station, start_name, goal_name) in short_path_list:
        seg_steps = build_guidance_for_segment(df_nodes, df_edges, station, start_name, goal_name)
        # 구간 헤더(가독성)
        all_steps.append(f"--- [{station}] {start_name} → {goal_name} ---")
        all_steps.extend(seg_steps)
    return all_steps


# 8) 사용 예시
#    - short_path 함수는 '이미 있다'고 가정
#      여기서는 대체로 short_path_list를 직접 만든 예시를 보여줌
if __name__ == "__main__":
    # CSV 로드
    df_nodes, df_edges = load_graph("line2_nodes_최종.csv", "line2_edges_최종.csv")

    short_path_list = [("신도림", "2번출구", "2호선 대림 방면 승강장"), ("강남", "2호선 역삼 방면 승강장", "7번출구")]  # 여기에 short_path 결과를 넣으면 됨 

    steps = build_full_guidance(df_nodes, df_edges, short_path_list)
    for s in steps:
        print(s)