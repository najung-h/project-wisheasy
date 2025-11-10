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


def get_legs(path: List[str]) -> List[Tuple[str, List[str], List[int]]]:
    """
    path: ["신도림-2호선", "문래-2호선", ..., "건대입구-7호선", ...]
    => 호선(line) 단위로 끊어서 [ (호선명, [역리스트], [인덱스들]), ... ] 형태로 변환
    """
    parsed = [node.split("-") for node in path]  # ["역","호선"]
    legs: List[Tuple[str, List[str], List[int]]] = []
    i = 0
    while i < len(parsed):
        st, ln = parsed[i]
        stations = [st]
        idxs = [i]
        j = i + 1
        while j < len(parsed) and parsed[j][1] == ln:
            stations.append(parsed[j][0])
            idxs.append(j)
            j += 1
        legs.append((ln, stations, idxs))
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


def get_subway_route(
    start_station: str,
    start_exit: str,
    end_station: str,
    end_exit: str,
) -> List[Tuple[str, str, str, Tuple[str, str]]]:
    """
    사용자 입력 → 최종 안내 세그먼트 리스트 반환

    반환 형식:
      [
        (station, start_node_name, goal_node_name, (line_name, leg_target_station)),
        ...
      ]

    예:
      [
        ("시청", "2번출구", "2호선 충정로 방면 승강장", ("2호선", "아현")),
        ("아현", "2호선 이대 방면 승강장", "1번출구", ("2호선", "도착역")),
      ]
    """
    # 1) DB에서 노선별 역 순서 로드 + 그래프 로드
    line_data = load_lines_from_db()
    G = get_graph()

    # 2) 그래프에서 출발/도착 노드 후보 찾기
    start_nodes = find_station_nodes(G, start_station)
    end_nodes = find_station_nodes(G, end_station)

    if not start_nodes or not end_nodes:
        # 역명이 잘못되었거나 DB에 없음
        return [
            (start_station, start_exit, "[오류] 역명 확인 필요", ("", "")),
            (end_station, "[오류] 역명 확인 필요", end_exit, ("", "")),
        ]

    # 3) 최단 경로(환승 가중치=1 최소화)
    best_path: Optional[List[str]] = None
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
        return [(start_station, start_exit, "[오류] 연결 경로 없음", ("", ""))]

    path = best_path

    # 4) path를 호선별 leg로 나누고, 각 leg의 진행 방향 계산
    legs = get_legs(path)
    leg_steps = [
        compute_leg_orientation(ln, sts, line_data) for ln, sts, idxs in legs
    ]

    instructions: List[Tuple[str, str, str, Tuple[str, str]]] = []

    # 5) 출발역 안내
    first_line, first_stations, first_idxs = legs[0]
    first_step = leg_steps[0]
    line_list_first = line_data[first_line]
    start_station_name = first_stations[0]

    # 출발역 방면명 = "현재역에서 다음 역" (path 상의 다음 역 기준)
    if len(first_stations) >= 2:
        dir_station0 = first_stations[1]
    else:
        idx = line_list_first.index(start_station_name)
        if first_line in RING_LINES:
            dir_station0 = line_list_first[(idx + first_step) % len(line_list_first)]
        else:
            dir_station0 = next_station_linear(line_list_first, idx, first_step)

    first_target = first_stations[-1]  # 이 leg에서 내릴 역 (환승역 or 도착역)
    instructions.append(
        (
            start_station_name,
            start_exit,
            make_direction_str(first_line, dir_station0),
            (first_line, first_target),
        )
    )

    # 6) 중간 환승 안내
    for k in range(len(legs) - 1):
        prev_line, prev_stations, prev_idxs = legs[k]
        next_line, next_stations, next_idxs = legs[k + 1]
        prev_step = leg_steps[k]
        next_step = leg_steps[k + 1]

        transfer_station = prev_stations[-1]  # 환승역 이름

        # 이전에 타고 온 호선의 방면 (환승역 기준, 한 칸 더 진행한 역)
        line_list_prev = line_data[prev_line]
        idx_tr_prev = line_list_prev.index(transfer_station)
        if prev_line in RING_LINES:
            dir_prev_station = line_list_prev[
                (idx_tr_prev + prev_step) % len(line_list_prev)
            ]
        else:
            dir_prev_station = next_station_linear(
                line_list_prev, idx_tr_prev, prev_step
            )

        # 새로 갈아탈 호선의 방면
        line_list_next = line_data[next_line]
        if len(next_stations) >= 2:
            dir_next_station = next_stations[1]
        else:
            idx_tr_next = line_list_next.index(transfer_station)
            if next_line in RING_LINES:
                dir_next_station = line_list_next[
                    (idx_tr_next + next_step) % len(line_list_next)
                ]
            else:
                dir_next_station = next_station_linear(
                    line_list_next, idx_tr_next, next_step
                )

        next_target = next_stations[-1]

        instructions.append(
            (
                transfer_station,
                make_direction_str(prev_line, dir_prev_station),
                make_direction_str(next_line, dir_next_station),
                (next_line, next_target),
            )
        )

    # 7) 도착역 안내
    last_line, last_stations, last_idxs = legs[-1]
    last_step = leg_steps[-1]
    arrival_station = last_stations[-1]
    line_list_last = line_data[last_line]
    idx_last = line_list_last.index(arrival_station)

    if last_line in RING_LINES:
        dir_last_station = line_list_last[
            (idx_last + last_step) % len(line_list_last)
        ]
    else:
        dir_last_station = next_station_linear(
            line_list_last, idx_last, last_step
        )

    instructions.append(
        (
            arrival_station,
            make_direction_str(last_line, dir_last_station),
            end_exit,
            (last_line, "도착역"),
        )
    )

    return instructions


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

    esc_val = row.get("escalator", False)
    # NaN, None 같은 값은 False 처리
    if pd.isna(esc_val):
        is_escalator = False
    else:
        is_escalator = bool(esc_val)

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