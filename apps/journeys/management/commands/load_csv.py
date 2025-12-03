import csv
import os
from typing import Optional

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from apps.journeys.models import (
    Station,
    Line,
    Node,
    Edge,
    FastGate,
    Lines,
)


class Command(BaseCommand):
    help = (
        "static/data 폴더의 CSV 파일들을 DB에 로드합니다.\n"
        "지원 파일: station.csv, line.csv, node.csv, edge.csv, stationline.csv, FastGate.csv, lines.csv"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            type=str,
            help="불러올 CSV 파일 이름 (예: station.csv, line.csv, node.csv 등)",
        )

    def handle(self, *args, **options):
        csv_file = options["file"]

        if not csv_file:
            raise CommandError(
                "CSV 파일 이름을 '--file' 옵션으로 지정해야 합니다. "
                "예: python manage.py load_csv --file station.csv"
            )

        # static/data 기준 경로
        csv_path = os.path.join(settings.BASE_DIR, "static", "data", csv_file)
        if not os.path.exists(csv_path):
            raise CommandError(f"파일을 찾을 수 없습니다: {csv_path}")

        self.stdout.write(f"📂 '{csv_file}' 불러오는 중...")

        with open(csv_path, newline="", encoding="utf-8-sig") as csvfile:
            reader = csv.DictReader(csvfile)

            # 파일 이름으로 분기
            lower = csv_file.lower()
            if "stationline" in lower:
                self.load_stationline(reader)
            elif "fastgate" in lower or "fast_gate" in lower:
                self.load_fastgate(reader)
            elif lower.startswith("station") and "stationline" not in lower:
                self.load_station(reader)
            elif lower.startswith("line") and lower != "lines.csv":
                # line.csv (노선 마스터)
                self.load_line(reader)
            elif lower == "lines.csv":
                # Lines(line, station, order_in_line) → 노선별 역순서
                self.load_lines(reader)
            elif "node" in lower:
                self.load_nodes(reader)
            elif "edge" in lower:
                self.load_edges(reader)
            elif "facilityloc" in lower:
                self.load_facility_loc(reader)
            elif "facility" in lower:
                self.load_facility(reader)
            else:
                raise CommandError(f"⚠️ '{csv_file}'은(는) 인식되지 않는 파일입니다.")

    # -------------------
    # Station
    # -------------------
    def load_station(self, reader):
        count_new = 0
        count_update = 0

        for row in reader:
            station_id = row.get("id") or row.get("station_id")
            name = row.get("name") or row.get("station_name")

            if not station_id or not name:
                self.stdout.write(
                    self.style.WARNING(f"⚠️ station row 건너뜀 (id/name 누락): {row}")
                )
                continue

            obj, created = Station.objects.update_or_create(
                id=station_id,
                defaults={"name": name.strip()},
            )
            if created:
                count_new += 1
            else:
                count_update += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"✅ Station 업로드 완료: {count_new}개 추가, {count_update}개 업데이트됨"
            )
        )

    # -------------------
    # Line
    # -------------------
    def load_line(self, reader):
        count_new = 0
        count_update = 0

        for row in reader:
            line_id = row.get("id") or row.get("line_id")
            name = row.get("name") or row.get("line_name")

            if not line_id or not name:
                self.stdout.write(
                    self.style.WARNING(f"⚠️ line row 건너뜀 (id/name 누락): {row}")
                )
                continue

            obj, created = Line.objects.update_or_create(
                id=line_id,
                defaults={"name": name.strip()},
            )
            if created:
                count_new += 1
            else:
                count_update += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"✅ Line 업로드 완료: {count_new}개 추가, {count_update}개 업데이트됨"
            )
        )

    # -------------------
    # Lines (노선별 역 순서)
    # -------------------
    def load_lines(self, reader):
        """
        Lines(line, station, order_in_line)
        """
        count_new = 0
        count_update = 0

        for row in reader:
            line_name = row["line"].strip()
            station_name = row["station"].strip()
            order_in_line = int(row["order_in_line"])

            obj, created = Lines.objects.update_or_create(
                line=line_name,
                order_in_line=order_in_line,
                defaults={
                    "station": station_name,
                },
            )
            if created:
                count_new += 1
            else:
                count_update += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"✅ lines.csv 업로드 완료: {count_new}개 추가, {count_update}개 업데이트됨"
            )
        )

    # -------------------
    # Node
    # -------------------
    def load_nodes(self, reader):
        count_new = 0
        count_update = 0

        def parse_str(value: Optional[str]):
            return value.strip() if value else None

        for row in reader:
            # CSV에 node_id 또는 id 둘 중 하나가 있을 것으로 가정
            node_id = row.get("id") or row.get("node_id")
            if not node_id:
                self.stdout.write(
                    self.style.WARNING(f"⚠️ node row 건너뜀 (id/node_id 누락): {row}")
                )
                continue

            station_id = row.get("station_id")
            station_name = row.get("station")

            station_obj = None
            if station_id:
                station_obj = Station.objects.filter(id=station_id).first()
            elif station_name:
                station_obj = Station.objects.filter(name=station_name).first()

            if not station_obj:
                self.stdout.write(
                    self.style.WARNING(
                        f"⚠️ node row 건너뜀 (Station 미존재): {row}"
                    )
                )
                continue

            obj, created = Node.objects.update_or_create(
                id=node_id,
                defaults={
                    "name": parse_str(row.get("name") or row.get("node_name")),
                    "floor": parse_str(row.get("floor")),
                    "type": parse_str(row.get("type")),
                    "station": station_obj,
                },
            )
            if created:
                count_new += 1
            else:
                count_update += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"✅ node.csv 업로드 완료: {count_new}개 추가, {count_update}개 업데이트됨"
            )
        )

    # -------------------
    # Edge
    # -------------------
    def load_edges(self, reader):
        count_new = 0
        count_update = 0

        for row in reader:
            # edge_key, edge_id, id 중 하나
            edge_id = row.get("id") or row.get("edge_id") or row.get("edge_key")
            if not edge_id:
                self.stdout.write(
                    self.style.WARNING(
                        f"⚠️ edge row 건너뜀 (id/edge_id/edge_key 누락): {row}"
                    )
                )
                continue

            # source_node / source
            source_node_id = row.get("source_node") or row.get("source")
            target_node_id = row.get("target_node") or row.get("target")

            if not source_node_id or not target_node_id:
                self.stdout.write(
                    self.style.WARNING(
                        f"⚠️ edge row 건너뜀 (source/target 누락): {row}"
                    )
                )
                continue

            source_obj = Node.objects.filter(id=source_node_id).first()
            target_obj = Node.objects.filter(id=target_node_id).first()

            if not source_obj or not target_obj:
                self.stdout.write(
                    self.style.WARNING(
                        f"⚠️ edge row 건너뜀 (Node 미존재): {row}"
                    )
                )
                continue

            esc_raw = (row.get("escalator") or "").strip()
            is_escalator = esc_raw in ("1", "True", "true", "Y", "y")

            obj, created = Edge.objects.update_or_create(
                id=edge_id,
                defaults={
                    "escalator": is_escalator,
                    "source_node": source_obj,
                    "target_node": target_obj,
                },
            )
            if created:
                count_new += 1
            else:
                count_update += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"✅ edge.csv 업로드 완료: {count_new}개 추가, {count_update}개 업데이트됨"
            )
        )

    # -------------------
    # FastGate (새 구조: platform / boarding_gate / transfer / escalator)
    # -------------------
    def load_fastgate(self, reader):
        """
        FastGate.csv
        columns: platform, boarding_gate, transfer, escalator
        """
        self.stdout.write(self.style.WARNING("FastGate.csv 불러오는 중..."))

        # 기존 데이터 모두 삭제 후 재적재
        FastGate.objects.all().delete()

        cnt = 0
        for row in reader:
            platform = (row.get("platform") or "").strip()
            boarding_gate = (row.get("boarding_gate") or "").strip()
            transfer_raw = (row.get("transfer") or "").strip()
            escalator_raw = (row.get("escalator") or "").strip()

            if not platform or not boarding_gate:
                self.stdout.write(
                    self.style.WARNING(f"⚠️ fast_gate row 건너뜀 (platform/boarding_gate 누락): {row}")
                )
                continue

            transfer = transfer_raw in ("1", "True", "true", "Y", "y")
            escalator = escalator_raw in ("1", "True", "true", "Y", "y")

            FastGate.objects.create(
                platform=platform,
                boarding_gate=boarding_gate,
                transfer=transfer,
                escalator=escalator,
            )
            cnt += 1

        self.stdout.write(
            self.style.SUCCESS(f"✅ FastGate.csv 업로드 완료: {cnt}개 저장됨")
        )

    # -------------------
    # StationLine (ManyToMany through 테이블)
    # -------------------
    def load_stationline(self, reader):
        """
        stationline.csv
        - station_id, line_id 또는
        - station(역 이름), line(호선 이름) 형태라고 가정
        """
        ThroughModel = Station.lines.through

        count_new = 0
        count_exist = 0

        for row in reader:
            station_id = row.get("station_id")
            line_id = row.get("line_id")
            station_name = row.get("station")
            line_name = row.get("line")

            station_obj = None
            line_obj = None

            if station_id:
                station_obj = Station.objects.filter(id=station_id).first()
            elif station_name:
                station_obj = Station.objects.filter(name=station_name).first()

            if line_id:
                line_obj = Line.objects.filter(id=line_id).first()
            elif line_name:
                line_obj = Line.objects.filter(name=line_name).first()

            if not station_obj or not line_obj:
                self.stdout.write(
                    self.style.WARNING(
                        f"⚠️ stationline row 건너뜀 (Station/Line 미존재): {row}"
                    )
                )
                continue

            obj, created = ThroughModel.objects.get_or_create(
                station_id=station_obj.id,
                line_id=line_obj.id,
            )
            if created:
                count_new += 1
            else:
                count_exist += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"✅ stationline.csv 업로드 완료: {count_new}개 추가, {count_exist}개 이미 존재"
            )
        )

    # -------------------
    # Facility (편의시설)
    # -------------------
    def load_facility(self, reader):
        from apps.journeys.models import Facility

        count_new = 0
        count_update = 0

        for row in reader:
            facility_id = row.get("facility_id") or row.get("id")
            name = row.get("facility_name") or row.get("name")

            if not facility_id:
                self.stdout.write(self.style.WARNING(f"⚠️ facility row 건너뜀 (facility_id 누락): {row}"))
                continue

            try:
                facility_id = int(facility_id)
            except Exception:
                self.stdout.write(self.style.WARNING(f"⚠️ facility_id 정수 변환 실패: {facility_id}"))
                continue

            obj, created = Facility.objects.update_or_create(
                facility_id=facility_id,
                defaults={"facility_name": (name or "").strip()},
            )

            if created:
                count_new += 1
            else:
                count_update += 1

        self.stdout.write(
            self.style.SUCCESS(f"✅ facility.csv 업로드 완료: {count_new}개 추가, {count_update}개 업데이트됨")
        )

    # -------------------
    # FacilityLoc (편의시설 위치 정보)
    # -------------------
    def load_facility_loc(self, reader):
        from apps.journeys.models import FacilityLoc, Station, Line, Facility

        count_new = 0
        count_update = 0

        for row in reader:
            station_id = (row.get("station_id") or "").strip()
            line_id = (row.get("line_id") or "").strip()
            facility_id = (row.get("facility_id") or "").strip()
            detail_loc = (row.get("detail_loc") or "").strip()

            if not station_id or not line_id or not facility_id:
                self.stdout.write(
                    self.style.WARNING(
                        f"⚠️ facility_loc row 건너뜀 (station_id/line_id/facility_id 누락): {row}"
                    )
                )
                continue

            station_obj = Station.objects.filter(id=station_id).first()
            line_obj = Line.objects.filter(id=line_id).first()

            try:
                facility_id_int = int(facility_id)
            except Exception:
                self.stdout.write(
                    self.style.WARNING(f"⚠️ facility_id 정수 변환 실패: {facility_id}")
                )
                continue

            facility_obj = Facility.objects.filter(facility_id=facility_id_int).first()

            if not station_obj or not line_obj or not facility_obj:
                self.stdout.write(
                    self.style.WARNING(
                        f"⚠️ facility_loc row 건너뜀 (FK 매칭 실패): {row}"
                    )
                )
                continue

            obj, created = FacilityLoc.objects.update_or_create(
                station=station_obj,
                line=line_obj,
                facility=facility_obj,
                defaults={
                    "detail_loc": detail_loc,
                },
            )

            if created:
                count_new += 1
            else:
                count_update += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"✅ facility_loc.csv 업로드 완료: {count_new}개 추가, {count_update}개 업데이트됨"
            )
        )
