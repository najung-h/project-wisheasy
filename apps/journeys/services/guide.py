import pandas as pd
from typing import List, Tuple, Optional, Dict
from collections import deque
import networkx as nx

from apps.journeys.models import Station, Line, Node, Edge, FastGate, Lines
from apps.journeys.management.commands.build_graph import get_graph

class RouteBuildError(Exception):
    """그래프에서 최단 경로를 만들지 못했을 때"""
    pass

class GuidanceBuildError(Exception):
    """노드 간 안내 문장을 만들지 못했을 때"""
    pass

# Lines → dict 로드
def load_lines_from_db() -> dict[str, list[str]]:
    """
    Lines(line, station, order_in_line)에서 노선별 역순서를 dict로 생성
    예: {"7호선": ["장암", "도봉산", ...], "2호선": [...]}
    """
    lines: dict[str, list[str]] = {}
    qs = Lines.objects.values("line", "station", "order_in_line")
    rows = sorted(list(qs), key=lambda r: (r["line"], r["order_in_line"]))
    for r in rows:
        lines.setdefault(r["line"], []).append(r["station"])
    return lines


RING_LINES = {"2호선"}  # 순환선 목록


# DB → DataFrame 로드
# 1) 전체 그래프 로딩 (모든 역 공통으로 쓰는 용도)
def load_graph_from_db() -> tuple[pd.DataFrame, pd.DataFrame]:
    # --- Station ---
    qs_station = Station.objects.values("id", "name")
    df_station = pd.DataFrame(list(qs_station)) if qs_station.exists() else pd.DataFrame(
        columns=["id", "name"]
    )

    # --- Node ---
    qs_node = Node.objects.values("id", "name", "floor", "type", "station_id")
    df_node_raw = pd.DataFrame(list(qs_node)) if qs_node.exists() else pd.DataFrame(
        columns=["id", "name", "floor", "type", "station_id"]
    )

    # --- Line (현재 그래프 구성에는 안 쓰이지만, 필요하면 유지) ---
    qs_line = Line.objects.values("id", "name")
    df_line = pd.DataFrame(list(qs_line)) if qs_line.exists() else pd.DataFrame(
        columns=["id", "name"]
    )

    # Node + Station 조인해서 df_nodes 생성
    df_nodes = df_node_raw.merge(
        df_station.rename(columns={"id": "station_id", "name": "station"}),
        on="station_id",
        how="left",
    )

    df_nodes = df_nodes.rename(
        columns={
            "id": "node_id",
            "name": "node_name",
        }
    )[["node_id", "station", "node_name", "floor", "type", "station_id"]]

    # --- Edge ---
    qs_edge = Edge.objects.values("id", "escalator", "source_node", "target_node")
    df_edge_raw = pd.DataFrame(list(qs_edge)) if qs_edge.exists() else pd.DataFrame(
        columns=["id", "escalator", "source_node", "target_node"]
    )

    df_edges = df_edge_raw.merge(
        df_node_raw[["id", "station_id"]].rename(columns={"id": "source_node"}),
        on="source_node",
        how="left",
    ).merge(
        df_station.rename(columns={"id": "station_id", "name": "station"}),
        on="station_id",
        how="left",
    )

    df_edges = df_edges.rename(
        columns={
            "id": "edge_id",
            "source_node": "source",
            "target_node": "target",
        }
    )[["edge_id", "source", "target", "escalator", "station"]]

    # 문자열 정리
    for c in ["station", "node_id", "node_name", "type"]:
        if c in df_nodes.columns:
            df_nodes[c] = df_nodes[c].astype(str).str.strip()
    for c in ["source", "target", "station"]:
        if c in df_edges.columns:
            df_edges[c] = df_edges[c].astype(str).str.strip()

    return df_nodes, df_edges


def find_station_nodes(G: nx.Graph, name: str) -> list[str]:
    # "역명-호선" 형태라서, 안전하게 name + "-" 로 시작하는 노드를 찾자
    prefix = name + "-"
    return [n for n in G.nodes if n.startswith(prefix)]


def make_direction_str(line: str, towards_station: str) -> str:
    return f"{line} {towards_station} 방면 승강장"


def get_legs(path: List[str]) -> List[Tuple[str, List[str]]]:
    """
    path → [("호선명", ["역1","역2",...]), ...]
    """
    parsed = [node.split("-") for node in path]  # ["역","호선"]
    legs: List[Tuple[str, List[str]]] = []
    i = 0
    while i < len(parsed):
        st, ln = parsed[i]
        stations = [st]
        j = i + 1
        while j < len(parsed) and parsed[j][1] == ln:
            stations.append(parsed[j][0])
            j += 1
        legs.append((ln, stations))
        i = j
    return legs


def compute_leg_orientation(
    line_name: str,
    stations: List[str],
    line_data: dict[str, list[str]],
) -> int:
    """
    이 leg에서 역들이 line_list 상에서 정방향(+1)으로 가는지 역방향(-1)으로 가는지 계산
    """
    line_list = line_data[line_name]
    n = len(line_list)
    if len(stations) >= 2:
        a, b = stations[0], stations[1]
        ia, ib = line_list.index(a), line_list.index(b)
        if line_name in RING_LINES:
            # 순환선: 모듈러 연산으로 한 칸 차이 확인
            if (ib - ia) % n == 1:
                return 1
            elif (ia - ib) % n == 1:
                return -1
        else:
            # 비순환선: 단순 index 차이
            if ib - ia == 1:
                return 1
            elif ib - ia == -1:
                return -1
    # 기본값: 정방향
    return 1


def next_station_linear(line_list: list[str], idx: int, step: int) -> str:
    """
    비순환선에서 idx에서 step(+1/-1) 방향으로 한 칸 이동
    - 범위 밖이면 반대쪽 또는 자기 자신으로 fallback
    """
    n = len(line_list)
    j = idx + step
    if 0 <= j < n:
        return line_list[j]
    j2 = idx - step
    if 0 <= j2 < n:
        return line_list[j2]
    return line_list[idx]


def get_subway_route(start_station: str, start_exit: str, end_station: str, end_exit: str) -> List[Tuple[str, str, str]]:
    line_data = load_lines_from_db()
    G = get_graph()

    start_nodes = find_station_nodes(G, start_station)
    end_nodes = find_station_nodes(G, end_station)

    if not start_nodes or not end_nodes:
        raise RouteBuildError("station nodes not found in graph")

    best_path = None
    best_cost = float("inf")

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
        raise RouteBuildError("no path between stations")

    path = best_path
    legs = get_legs(path)
    leg_orient = [compute_leg_orientation(ln, sts, line_data) for ln, sts in legs]

    instructions: List[Tuple[str,str,str]] = []

    # 출발역
    first_line, first_stations = legs[0]
    first_step = leg_orient[0]
    start_station_name = first_stations[0]

    line_list = line_data[first_line]
    if len(first_stations) >= 2:
        dir_station0 = first_stations[1]
    else:
        idx = line_list.index(start_station_name)
        if first_line in RING_LINES:
            dir_station0 = line_list[(idx + first_step) % len(line_list)]
        else:
            dir_station0 = next_station_linear(line_list, idx, first_step)

    instructions.append(
        (start_station_name, start_exit, make_direction_str(first_line, dir_station0))
    )

    # 환승
    for k in range(len(legs)-1):
        prev_line, prev_stations = legs[k]
        next_line, next_stations = legs[k+1]
        prev_step = leg_orient[k]
        next_step = leg_orient[k+1]

        transfer_station = prev_stations[-1]

        # 이전 호선 방면
        prev_list = line_data[prev_line]
        idx_prev = prev_list.index(transfer_station)
        if prev_line in RING_LINES:
            dir_prev = prev_list[(idx_prev + prev_step) % len(prev_list)]
        else:
            dir_prev = next_station_linear(prev_list, idx_prev, prev_step)

        # 다음 호선 방면
        next_list = line_data[next_line]
        if len(next_stations) >= 2:
            dir_next = next_stations[1]
        else:
            idx_next = next_list.index(transfer_station)
            if next_line in RING_LINES:
                dir_next = next_list[(idx_next + next_step) % len(next_list)]
            else:
                dir_next = next_station_linear(next_list, idx_next, next_step)

        instructions.append(
            (transfer_station, make_direction_str(prev_line, dir_prev), make_direction_str(next_line, dir_next))
        )

    # 도착역
    last_line, last_stations = legs[-1]
    last_step = leg_orient[-1]
    arrival_station = last_stations[-1]

    last_list = line_data[last_line]
    idx_last = last_list.index(arrival_station)
    if last_line in RING_LINES:
        dir_last = last_list[(idx_last + last_step) % len(last_list)]
    else:
        dir_last = next_station_linear(last_list, idx_last, last_step)

    instructions.append(
        (arrival_station, make_direction_str(last_line, dir_last), end_exit)
    )

    return instructions


# BFS
def get_node_id(df_nodes: pd.DataFrame, station: str, name: str) -> Optional[str]:
    sub = df_nodes[(df_nodes["station"] == station) & (df_nodes["node_name"] == name)]
    if len(sub) == 0:
        return None
    return sub["node_id"].iloc[0]


def bfs_path_node_ids(df_edges_sub: pd.DataFrame, start_id: str, goal_id: str) -> Optional[List[str]]:
    adj: Dict[str, List[str]] = {}
    for _, r in df_edges_sub.iterrows():
        adj.setdefault(r["source"], []).append(r["target"])

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
    for a,b in zip(node_path, node_path[1:]):
        hit = df_edges_sub[(df_edges_sub["source"]==a)&(df_edges_sub["target"]==b)]
        if not hit.empty:
            rows.append(hit.iloc[0])
    if not rows:
        return pd.DataFrame(columns=df_edges_sub.columns)
    return pd.DataFrame(rows)


def build_relation_from_edge(row, df_nodes_sub: pd.DataFrame) -> str:
    src_id = row["source"]
    tgt_id = row["target"]
    esc_val = bool(row.get("escalator", False))

    src = df_nodes_sub[df_nodes_sub["node_id"]==src_id].iloc[0]
    tgt = df_nodes_sub[df_nodes_sub["node_id"]==tgt_id].iloc[0]

    move_str = "에스컬레이터를 이용하여" if esc_val else "계단/도보를 이용하여"
    return f"{src['node_name']}({src['floor']})에서 {move_str} {tgt['node_name']}({tgt['floor']})로 이동하세요."


def build_fastgate_message_new(platform: str, is_transfer: bool) -> Optional[str]:
    qs = FastGate.objects.filter(platform=platform, transfer=is_transfer)
    if not qs.exists():
        return None

    # escalator=True 우선
    if qs.filter(escalator=True).exists():
        chosen = qs.filter(escalator=True)
    else:
        chosen = qs

    gate = chosen.values_list("boarding_gate", flat=True).first()
    if not gate:
        return None

    if chosen.filter(escalator=True).exists():
        return f"{gate}에서 승차하세요. (에스컬레이터와 가까운 칸입니다.)"
    else:
        return f"{gate}에서 승차하세요."

    gates_str = " / ".join(map(str, gates))
    return f"{gates_str}에서 승차하세요. 하차 시 {move_type}"


def build_guidance_for_segment(
    df_nodes: pd.DataFrame,
    df_edges: pd.DataFrame,
    station: str,
    start_name: str,
    goal_name: str,
) -> List[str]:

    df_nodes_sub = df_nodes[df_nodes["station"] == station].copy()
    df_edges_sub = df_edges[df_edges["station"] == station].copy()

    start_id = get_node_id(df_nodes_sub, station, start_name)
    goal_id  = get_node_id(df_nodes_sub, station, goal_name)

    if start_id is None or goal_id is None:
        raise GuidanceBuildError(
            f"node not found for station={station}, start={start_name}, goal={goal_name}"
        )

    node_path = bfs_path_node_ids(df_edges_sub, start_id, goal_id)
    if node_path is None:
        raise GuidanceBuildError(
            f"no bfs path for station={station}, start={start_name}, goal={goal_name}"
        )

    edges_path = to_edge_rows(df_edges_sub, node_path)

    steps = []
    for _, r in edges_path.iterrows():
        steps.append(build_relation_from_edge(r, df_nodes_sub))

    return steps


def build_full_guidance(
    df_nodes: pd.DataFrame,
    df_edges: pd.DataFrame,
    route: List[Tuple[str,str,str]]
) -> List[str]:

    all_steps: List[str] = []

    for i in range(len(route)):
        station, start_name, goal_name = route[i]

        # 1) 역 내부 이동 안내
        seg_steps = build_guidance_for_segment(
            df_nodes, df_edges,
            station=station,
            start_name=start_name,
            goal_name=goal_name
        )
        all_steps.extend(seg_steps)

        # 2) 다음 세그먼트가 있다면 → FastGate 안내 삽입
        if i < len(route) - 1:
            next_station, next_start, next_goal = route[i+1]

            # next_goal의 node type 조회
            df_nodes_sub = df_nodes[df_nodes["station"] == next_station]
            next_goal_row = df_nodes_sub[df_nodes_sub["node_name"] == next_goal]

            if next_goal_row.empty:
                continue  # 타입 모르면 패스

            node_type = next_goal_row["type"].iloc[0]

            if node_type == "승강장":
                # 환승
                msg = build_fastgate_message_new(next_start, is_transfer=True)
                if msg:
                    all_steps.append(msg)

            elif node_type == "출구":
                # 하차 후 출구 이동
                msg = build_fastgate_message_new(next_start, is_transfer=False)
                if msg:
                    all_steps.append(msg)

    # 3) 마지막 안내 후
    all_steps.append("이용해주셔서 감사합니다.")

    return all_steps