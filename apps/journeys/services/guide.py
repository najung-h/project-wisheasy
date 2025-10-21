import pandas as pd
from typing import List, Tuple, Optional, Dict
from collections import deque
import networkx as nx

from apps.journeys.models import Nodes, Edges, Lines

# Lines → dict 로드
def load_lines_from_db() -> dict[str, list[str]]:
    """
    Lines(line, station, order_in_line)에서 노선별 역순서를 dict로 생성
    예: {"7호선": ["장암", "도봉산", ...], "2호선": [...]}
    """
    lines = {}
    qs = Lines.objects.values("line", "station", "order_in_line")
    # 정렬 보장
    rows = sorted(list(qs), key=lambda r: (r["line"], r["order_in_line"]))
    for r in rows:
        lines.setdefault(r["line"], []).append(r["station"])
    return lines


# DB → DataFrame 로드
def load_graph_from_db() -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    models에서 Nodes/Edges를 불러와서 df_nodes, df_edges(DataFrame) 반환.
    df_edges.station 은 source 기준으로 Nodes.station을 조인해 생성.
    """
    qs_nodes = Nodes.objects.values("node_id","line","node_name","floor","type","station")
    df_nodes = pd.DataFrame(list(qs_nodes)) if qs_nodes.exists() else pd.DataFrame(
        columns=["node_id","line","node_name","floor","type","station"]
    )

    qs_edges = Edges.objects.values("edge_key","relation","escalator","out_of_order","is_escalator","source","target")
    df_edges = pd.DataFrame(list(qs_edges)) if qs_edges.exists() else pd.DataFrame(
        columns=["edge_key","relation","escalator","out_of_order","is_escalator","source","target"]
    )

    # station 붙이기 (source 기준)
    if not df_edges.empty and not df_nodes.empty:
        df_edges = df_edges.merge(
            df_nodes[["node_id","station"]],
            left_on="source", right_on="node_id", how="left"
        ).drop(columns=["node_id"]).rename(columns={"station":"station"})

    # 가벼운 정리
    for c in ["relation","source","target","station"]:
        if c in df_edges.columns:
            df_edges[c] = df_edges[c].astype(str).str.strip()
    for c in ["station","node_id","node_name","type"]:
        if c in df_nodes.columns:
            df_nodes[c] = df_nodes[c].astype(str).str.strip()
    if "out_of_order" not in df_edges.columns:
        df_edges["out_of_order"] = 0
    if "is_escalator" not in df_edges.columns:
        df_edges["is_escalator"] = 0

    return df_nodes, df_edges


# short_path_list 생성에 필요한 G 빌드
def build_subway_graph(lines: dict[str, list[str]]) -> nx.Graph:
    """
    lines = {"7호선": [...], "2호선": [...]}
    노선 내 인접 역 간 weight=0, 동일역 환승 간선 weight=1
    """
    G = nx.Graph()
    for line_name, stations in lines.items():
        for i, station in enumerate(stations):
            G.add_node(f"{station}-{line_name}")
            if i > 0:
                G.add_edge(f"{stations[i-1]}-{line_name}", f"{station}-{line_name}", weight=0)
    # 환승 연결 (동일 역명, 다른 노선)
    all_nodes = list(G.nodes)
    for n1 in all_nodes:
        name1, line1 = n1.split("-")
        for n2 in all_nodes:
            name2, line2 = n2.split("-")
            if name1 == name2 and line1 != line2:
                G.add_edge(n1, n2, weight=1)
    return G

def find_station_nodes(G: nx.Graph, name: str) -> list[str]:
    return [n for n in G.nodes if n.startswith(name + "-")]

def get_next_station_name(line_list: list[str], curr: str, forward: bool=True) -> Optional[str]:
    if curr not in line_list:
        return None
    idx = line_list.index(curr)
    if forward and idx + 1 < len(line_list):
        return line_list[idx + 1]
    elif not forward and idx - 1 >= 0:
        return line_list[idx - 1]
    return None

def make_direction_str(line: str, next_station: Optional[str]) -> str:
    return f"{line} {next_station} 방면 승강장" if next_station else f"{line} 방면 승강장"

# 사용자 입력 → short_path_list
def get_subway_route(
    start_station: str,
    start_exit: str,
    end_station: str,
    end_exit: str,
    *,
    lines: Optional[dict[str, list[str]]] = None,
    G: Optional[nx.Graph] = None
) -> List[Tuple[str, str, str]]:

    if lines is None:
        lines = load_lines_from_db()
    if G is None:
        G = build_subway_graph(lines)

    # 출발/도착 노드 후보
    start_nodes = find_station_nodes(G, start_station)
    end_nodes   = find_station_nodes(G, end_station)
    if not start_nodes or not end_nodes:
        # 역명이 잘못되었거나 DB에 없음
        return [(start_station, start_exit, f"[오류] 역명 확인 필요"), (end_station, f"[오류] 역명 확인 필요", end_exit)]

    # 최단 경로(환승 가중치=1 최소화)
    best_path, best_cost = None, float("inf")
    for s in start_nodes:
        for e in end_nodes:
            try:
                path = nx.shortest_path(G, s, e, weight="weight")
                cost = nx.path_weight(G, path, weight="weight")
                if cost < best_cost:
                    best_path, best_cost = path, cost
            except nx.NetworkXNoPath:
                continue

    if best_path is None:
        return [(start_station, start_exit, "[오류] 연결 경로 없음")]

    # 경로를 short_path_list로 변환
    output: List[Tuple[str, str, str]] = []
    skip_next = False
    line_data = lines  # {"7호선": [...], "2호선": [...]}

    for i in range(len(best_path)):
        if skip_next:
            skip_next = False
            continue

        station, line = best_path[i].split("-")

        if i == 0:
            # 출발 세그먼트
            next_station_name = best_path[i + 1].split("-")[0]
            direction_station = get_next_station_name(line_data[line], station, forward=True)
            output.append((station, start_exit, make_direction_str(line, direction_station)))

        elif i == len(best_path) - 1:
            # 도착 세그먼트
            line_list = line_data[line]
            direction_station = get_next_station_name(line_list, station, forward=True)
            output.append((station, make_direction_str(line, direction_station), end_exit))

        else:
            # 중간(환승) 판단
            prev_line = best_path[i - 1].split("-")[1]
            next_line = best_path[i + 1].split("-")[1]
            curr_station = station

            if prev_line != next_line:
                prev_dir = get_next_station_name(line_data[prev_line], curr_station, forward=True)
                next_dir = get_next_station_name(line_data[next_line], curr_station, forward=True)
                dir_prev = make_direction_str(prev_line, prev_dir)
                dir_next = make_direction_str(next_line, next_dir)
                output.append((curr_station, dir_prev, dir_next))
                skip_next = True

    return output


# BFS
def get_node_id(df_nodes: pd.DataFrame, station: str, node_name: str) -> Optional[str]:
    sub = df_nodes[(df_nodes["station"] == station) & (df_nodes["node_name"] == node_name)]
    if len(sub) == 0:
        return None
    return sub["node_id"].iloc[0]

def bfs_path_node_ids(df_edges_sub: pd.DataFrame, start_id: str, goal_id: str) -> Optional[List[str]]:
    adj: Dict[str, List[str]] = {}
    for _, r in df_edges_sub.iterrows():
        s = r["source"]; t = r["target"]
        adj.setdefault(s, []).append(t)

    q = deque([start_id])
    visited = {start_id: None}
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

    path = []
    node = goal_id
    while node is not None:
        path.append(node)
        node = visited[node]
    path.reverse()
    return path

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

def render_relation(relation: str, malfunction: int) -> str:
    if int(malfunction) == 1:
        return relation.replace("에스컬레이터", "계단/도보(에스컬레이터 점검)")
    return relation

def extend_platform_to_gate(df_nodes_sub: pd.DataFrame, df_edges_sub: pd.DataFrame, platform_node_id: str) -> Optional[pd.DataFrame]:
    out_edges = df_edges_sub[df_edges_sub["source"] == platform_node_id].copy()
    if out_edges.empty:
        return None
    gate_targets = out_edges.merge(
        df_nodes_sub[["node_id","type"]],
        left_on="target", right_on="node_id", how="left"
    )
    gate_targets = gate_targets[gate_targets["type"] == "탑승구"].copy()
    if gate_targets.empty:
        return None
    gate_targets = gate_targets.sort_values(by="is_escalator", ascending=False)
    chosen = gate_targets.iloc[0:1]
    return chosen[gate_targets.columns.intersection(df_edges_sub.columns)]

def build_guidance_for_segment(df_nodes: pd.DataFrame, df_edges: pd.DataFrame, station: str, start_name: str, goal_name: str) -> List[str]:
    df_nodes_sub = df_nodes[df_nodes["station"] == station].copy()
    df_edges_sub = df_edges[df_edges["station"] == station].copy()

    start_id = get_node_id(df_nodes, station, start_name)
    goal_id  = get_node_id(df_nodes, station, goal_name)
    if start_id is None or goal_id is None:
        return [f"[{station}] 안내 실패: 노드 식별 불가 (start='{start_name}', goal='{goal_name}')"]

    node_path = bfs_path_node_ids(df_edges_sub, start_id, goal_id)
    if node_path is None:
        return [f"[{station}] 안내 실패: 경로 없음 (start='{start_name}', goal='{goal_name}')"]

    edges_path = to_edge_rows(df_edges_sub, node_path)
    steps = [render_relation(r["relation"], r.get("out_of_order", 0)) for _, r in edges_path.iterrows()]

    goal_row = df_nodes_sub[df_nodes_sub["node_id"] == goal_id]
    if not goal_row.empty and goal_row["type"].iloc[0] == "승강장":
        chosen_edge_to_gate = extend_platform_to_gate(df_nodes_sub, df_edges_sub, goal_id)
        if chosen_edge_to_gate is not None and not chosen_edge_to_gate.empty:
            er = chosen_edge_to_gate.iloc[0]
            steps.append(render_relation(er["relation"], er.get("out_of_order", 0)))

    return steps

def build_full_guidance(df_nodes: pd.DataFrame, df_edges: pd.DataFrame, short_path_list: List[Tuple[str, str, str]]) -> List[str]:
    all_steps: List[str] = []
    for (station, start_name, goal_name) in short_path_list:
        seg_steps = build_guidance_for_segment(df_nodes, df_edges, station, start_name, goal_name)
        # all_steps.append(f"--- [{station}] {start_name} → {goal_name} ---")
        all_steps.extend(seg_steps)
    return all_steps
