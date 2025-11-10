import pandas as pd
from typing import List, Tuple, Optional, Dict
from collections import deque
import networkx as nx

from apps.journeys.models import Station, Line, Node, Edge, FastGate, Lines
from apps.journeys.management.commands.build_graph import get_graph


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
        G = get_graph()

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


def build_relation_from_edge(row, df_nodes_sub: pd.DataFrame) -> str:
    src_id = row["source"]
    tgt_id = row["target"]
    is_escalator = bool(row.get("escalator", False))

    src = df_nodes_sub[df_nodes_sub["node_id"] == src_id].iloc[0]
    tgt = df_nodes_sub[df_nodes_sub["node_id"] == tgt_id].iloc[0]

    move_str = "에스컬레이터를 이용하여" if is_escalator else "계단/도보를 이용하여"

    return (
        f"{src['node_name']}({src['floor']})에서 "
        f"{move_str} "
        f"{tgt['node_name']}({tgt['floor']})로 이동하세요."
    )

def build_fastgate_message(station_name: str, line_name: str) -> Optional[str]:
    try:
        st = Station.objects.get(name=station_name)
        ln = Line.objects.get(name=line_name)
    except (Station.DoesNotExist, Line.DoesNotExist):
        return None

    qs = FastGate.objects.filter(station=st, line=ln)  # FK 객체로 필터
    if not qs.exists():
        return None

    # escalator=True 우선, 없으면 escalator=False 사용
    if qs.filter(escalator=True).exists():
        chosen = qs.filter(escalator=True)
        move_type = "에스컬레이터 이용 가능"
    else:
        chosen = qs.filter(escalator=False)
        move_type = "계단 이용 가능"

    gates = chosen.values_list("boarding_gate", flat=True).distinct()
    gates = [g for g in gates if g]
    if not gates:
        return None

    gates_str = " / ".join(map(str, gates))
    return f"{gates_str}에서 승차하세요. 하차 시 {move_type}"


def build_guidance_for_segment(
    df_nodes: pd.DataFrame,
    df_edges: pd.DataFrame,
    station: str,
    start_name: str,
    goal_name: str,
    line_name: str,
) -> List[str]:
    # 해당 역만 서브셋
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

    steps: List[str] = []
    for _, r in edges_path.iterrows():
        steps.append(build_relation_from_edge(r, df_nodes_sub))

    # 마지막 노드 타입 확인
    goal_row = df_nodes_sub[df_nodes_sub["node_id"] == goal_id]
    if not goal_row.empty:
        goal_type = goal_row["type"].iloc[0]
        if goal_type == "승강장":
            # FastGate로 탑승구 안내
            msg = build_fastgate_message(station_name=station, line_name=line_name)
            if msg:
                steps.append(msg)
        elif goal_type == "출구":
            steps.append("이용해주셔서 감사합니다.")

    return steps

def build_full_guidance(
    df_nodes: pd.DataFrame,
    df_edges: pd.DataFrame,
    route_with_meta: List[tuple]
) -> List[str]:
    """
    route_with_meta:
      [ (station, start_name, goal_name, (line_name, leg_target_station)), ... ]
    """
    all_steps: List[str] = []

    for (station, start_name, goal_name, line_and_target) in route_with_meta:
        line_name, target_station = line_and_target  # target_station은 지금은 메시지용으로만 필요하면 활용
        seg_steps = build_guidance_for_segment(
            df_nodes, df_edges,
            station=station,
            start_name=start_name,
            goal_name=goal_name,
            line_name=line_name,
        )
        all_steps.extend(seg_steps)

    return all_steps