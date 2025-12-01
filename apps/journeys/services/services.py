# apps/journeys/services/services.py

from apps.journeys.models import Station, Node

def format_exit_for_message(exit_name: str) -> str:
    """
    '8번출구', '8번 출구' 등 → '8번 출구'로 통일해서
    사용자에게 보여줄 때 쓰는 함수.
    """
    if not exit_name:
        return exit_name

    no_space = exit_name.replace(" ", "")
    if "번출구" in no_space:
        # '8번출구' -> '8번 출구'
        return no_space.replace("번출구", "번 출구")

    return exit_name.strip()


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

def _normalize_exit_string(raw: str) -> str:
    """
    '1', '1번', '1 번', '1번 출구', '1번출구' -> '1번출구' 로 통일
    그 외는 공백만 제거
    """
    if not raw:
        return ""

    s = raw.strip()
    no_space = s.replace(" ", "")

    # 1 -> 1번출구
    if no_space.isdigit():
        return f"{no_space}번출구"

    # 1번 -> 1번출구
    if no_space.endswith("번") and no_space[:-1].isdigit():
        return f"{no_space}출구"

    # 이미 1번출구 꼴이면 그대로
    if no_space.endswith("번출구") and no_space[:-3].isdigit():
        return no_space

    # 그 외는 그냥 공백만 제거한 값
    return no_space

def validate_and_correct_exit(raw_exit: str, station_name: str):
    """
    출구 유효성 검사 + 보정.

    - 출구는 '선택'이지만, 비어 있으면 기본값 1번출구로 시도
    - 1 / 1번 / 1번 출구 / 1번출구 등은 모두 '1번출구'로 정규화
    - DB에 없는 출구면 오류 메시지 + 최대 출구 번호 안내
    """
    _, exits_by_station = _get_station_and_exit_cache()

    # 0) 출구가 비어 있으면 기본값 "1번출구" 로 시도
    exit_input = (raw_exit or "").strip()
    if not exit_input:
        exit_input = "1번출구"

    # 1) 문자열 정규화 (공백/형식 정리)
    exit_norm = _normalize_exit_string(exit_input)   # 예: '1', '1 번 출구' -> '1번출구'

    station_exits = exits_by_station.get(station_name)

    # 2) 이 역에 출구 데이터가 전혀 없다면: 형식만 맞춘 값은 그대로 통과
    if station_exits is None:
        return True, exit_norm

    # 3) 역에 등록된 출구 목록도 공백 제거해서 비교용으로 맞춰줌
    normalized_station_exits = [ex.replace(" ", "") for ex in station_exits]

    # 등록되지 않은 출구라면 에러
    if exit_norm not in normalized_station_exits:
        if station_exits:
            # 출구 번호 기준으로 정렬해서 최대 출구 찾기
            sorted_exits = sorted(
                station_exits,
                key=lambda x: int("".join(filter(str.isdigit, x)) or 0),
            )
            max_exit = sorted_exits[-1]               # 예: '8번출구'
            pretty_max = format_exit_for_message(max_exit) # '8번 출구'
            pretty_input = format_exit_for_message(exit_norm)

            return False, (
                f"'{pretty_input}'은(는) {station_name}역에 존재하지 않는 출구입니다. "
                f"{pretty_max}까지 있습니다."
            )

        pretty_input = format_exit_for_message(exit_norm)
        return False, f"'{pretty_input}'은(는) {station_name}에 존재하지 않는 출구입니다."

    # 4) 정상인 경우: 정규화된 exit_norm 그대로 반환
    return True, exit_norm

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
