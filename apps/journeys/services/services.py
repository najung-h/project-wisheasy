# apps/journeys/services/services.py

from apps.journeys.models import Station, Node

def _pretty_exit_label(exit_name: str) -> str:
    """
    DB에는 '8번출구'로 저장되어 있지만,
    메시지에는 '8번 출구'처럼 띄워서 보여주고 싶을 때 쓰는 함수.
    """
    if exit_name.endswith("번출구"):
        num = exit_name[:-3]  # '8번출구' -> '8번'
        return f"{num}번 출구"  # '8번출구' -> '8번 출구'
    return exit_name

def split_exit_with_space(exit_input: str) -> str:
    """
    출구 번호에서 '번출구' 형식을 분리하여, '번 출구' 형식으로 반환하는 함수.
    예: '8번출구' -> '8번 출구'
    """
    if "번출구" in exit_input:
        # '번출구'를 분리하고, '번 출구' 형식으로 반환
        return exit_input.replace("번출구", "번 출구")
    return exit_input

# ---- 캐시: 서버 프로세스당 한 번만 DB에서 읽어오도록 ----
_STATIONS_CACHE = None      # ['강남', '역삼', ...]
_EXITS_CACHE = None         # {'강남': ['1번출구', '2번출구', ...], ...}

def _load_station_and_exit_cache():
    """
    Station / Node(출구) 정보를 DB에서 한 번만 읽어서
    모듈 전역 캐시에 올려둔다.
    """
    global _STATIONS_CACHE, _EXITS_CACHE
    if _STATIONS_CACHE is not None and _EXITS_CACHE is not None:
        return

    # 역 이름 전체
    stations = list(Station.objects.values_list("name", flat=True))

    # 각 역별 출구 목록 (Node.type == '출구' 이고, name = '1번출구' 같은 형태)
    exits_qs = Node.objects.filter(type="출구").values_list("station__name", "name")

    exits_by_station = {}
    for station_name, exit_name in exits_qs:
        exits_by_station.setdefault(station_name, []).append(exit_name)

    _STATIONS_CACHE = stations
    _EXITS_CACHE = exits_by_station


def _get_station_and_exit_cache():
    """
    항상 이 함수만 통해 캐시를 읽게 하면,
    실제 DB 쿼리는 최초 1번만 실행된다.
    """
    _load_station_and_exit_cache()
    return _STATIONS_CACHE, _EXITS_CACHE


# ---- 역 / 출구 유효성 ----

def validate_and_correct_station_name(raw_station: str):
    """
    역 이름 유효성 검사 + 내부적으로 사용할 이름으로 보정.

    - DB에는 '강남'이 들어있다고 가정.
    - 사용자가 '강남' 또는 '강남역' 둘 다 입력해도 허용.
      · '강남'  -> 내부적으로 '강남'
      · '강남역' -> 내부적으로 '강남'
    """
    stations, _ = _get_station_and_exit_cache()
    station_input = (raw_station or "").strip()

    if not station_input:
        return False, "역 이름을 입력해 주세요."

    # 1) DB에 그대로 있는 경우 ('강남')
    if station_input in stations:
        return True, station_input

    # 2) '강남역' 같이 '역'을 붙여 준 경우 → '강남'으로 매핑
    if station_input.endswith("역"):
        base = station_input[:-1]
        if base in stations:
            return True, base

    # 3) 그 외는 전부 유효하지 않은 역
    return False, f"'{station_input}'은(는) 유효한 역이 아닙니다. 다시 입력해주세요."


def validate_and_correct_exit(raw_exit: str, station_name: str):
    """
    출구 유효성 검사 + 보정.

    - 출구는 '선택'이므로 빈 값이면 그냥 통과 ('' 그대로 반환)
    - 숫자만 들어오면 '번출구'를 붙여준다.
      · '1'  -> '1번출구'
    """
    _, exits_by_station = _get_station_and_exit_cache()
    exit_input = (raw_exit or "").strip()

    # 출구는 선택 사항이므로, 비어 있으면 그대로 OK
    if not exit_input:
        return True, ""

    # 숫자만 입력된 경우 → '번출구' 붙이기
    if exit_input.isdigit():
        exit_input = f"{exit_input}번출구"  # 예: '1' -> '1번출구'

    # 비교할 때는 띄어쓰기 제거
    exit_input_without_space = exit_input.replace(" ", "")  # 띄어쓰기 제거

    station_exits = exits_by_station.get(station_name)

    # 이 역에 대한 출구 데이터가 전혀 없다면, 형식만 맞춘 값은 그대로 통과
    if station_exits is None:
        return True, exit_input

    # 출구 번호가 등록된 목록에 있는지 확인 (띄어쓰기 제거 후 비교)
    if exit_input_without_space not in [exit.replace(" ", "") for exit in station_exits]:
        # 출구 목록이 있다면, 가장 큰 번호(마지막 값)를 기준으로 안내
        if station_exits:
            sorted_exits = sorted(
                station_exits,
                key=lambda x: int(''.join(filter(str.isdigit, x))))  # 출구 번호 기준으로 정렬
            max_exit = sorted_exits[-1]  # 예: '8번출구'
            pretty_max = _pretty_exit_label(max_exit)  # '8번 출구'
            exit_input = split_exit_with_space(exit_input)
            return False, (
                f"'{exit_input}'은(는) {station_name}역에 존재하지 않는 출구입니다. "
                f"{pretty_max}까지 있습니다."
            )

        return False, f"'{exit_input}'은(는) {station_name}에 존재하지 않는 출구입니다."

    return True, exit_input


def validate_stations(
    start_station: str,
    end_station: str,
    start_exit: str,
    end_exit: str,
):
    """
    출발역/도착역 + 출발출구/도착출구 전체에 대한 유효성 검사.

    성공 시:
      (True, (정규화된_출발역, 정규화된_도착역), 정규화된_출발출구, 정규화된_도착출구)

    실패 시:
      (False, "에러 메시지", None, None)
    """
    # 1) 출발역
    ok, normalized_start = validate_and_correct_station_name(start_station)
    if not ok:
        return False, normalized_start, None, None  # normalized_start에 에러 메시지

    # 2) 도착역
    ok, normalized_end = validate_and_correct_station_name(end_station)
    if not ok:
        return False, normalized_end, None, None

    # 3) 출발 출구 (선택)
    ok, normalized_start_exit = validate_and_correct_exit(start_exit, normalized_start)
    if not ok:
        return False, normalized_start_exit, None, None  # 에러 메시지

    # 4) 도착 출구 (선택)
    ok, normalized_end_exit = validate_and_correct_exit(end_exit, normalized_end)
    if not ok:
        return False, normalized_end_exit, None, None

    # 모두 통과
    return True, (normalized_start, normalized_end), normalized_start_exit, normalized_end_exit
