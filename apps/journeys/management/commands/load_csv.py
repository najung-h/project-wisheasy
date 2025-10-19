import csv
import os
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from apps.journeys.models import Lines, Edges, Nodes


class Command(BaseCommand):
    help = "static/data 폴더의 CSV 파일(line2_7_edges.csv, line2_7_lines.csv, line2_7_nodes.csv)을 DB에 로드"

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            help='불러올 CSV 파일 이름 (예: line2_7_lines.csv)',
        )

    def handle(self, *args, **options):
        csv_file = options['file']

        if not csv_file:
            raise CommandError("CSV 파일 이름을 '--file' 옵션으로 지정해야 합니다. 예: python manage.py load_csv --file line2_7_lines.csv")

        # static/data 폴더 기준 경로 설정
        csv_path = os.path.join(settings.BASE_DIR, 'static', 'data', csv_file)
        if not os.path.exists(csv_path):
            raise CommandError(f"파일을 찾을 수 없습니다: {csv_path}")

        self.stdout.write(f"📂 '{csv_file}' 불러오는 중...")

        with open(csv_path, newline='', encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile)

            # 파일 이름으로 분기
            if 'lines' in csv_file:
                self.load_lines(reader)
            elif 'edges' in csv_file:
                self.load_edges(reader)
            elif 'nodes' in csv_file:
                self.load_nodes(reader)
            else:
                raise CommandError(f"⚠️ '{csv_file}'은(는) 인식되지 않는 파일입니다.")

    # --- Lines ---
    def load_lines(self, reader):
        count = 0
        for row in reader:
            Lines.objects.create(
                line=row["line"],
                station=row["station"],
                order_in_line=row["order_in_line"],
            )
            count += 1
        self.stdout.write(self.style.SUCCESS(f"✅ line2_7_lines.csv 업로드 완료 ({count}개 행 추가됨)"))

    # --- Edges ---
    def load_edges(self, reader):
        count_new = 0
        count_update = 0

        for row in reader:
            obj, created = Edges.objects.update_or_create(
                edge_key=row["edge_key"],  # PK 기준으로 찾음
                defaults={
                    "relation": row["relation"],
                    "escalator": row.get("escalator", 0),
                    "out_of_order": row.get("out_of_order", 0),
                    "is_escalator": row.get("is_escalator") or None,
                    "source": row["source"],
                    "target": row["target"],
                },
            )
            if created:
                count_new += 1
            else:
                count_update += 1

        self.stdout.write(
            self.style.SUCCESS(f"✅ edges.csv 업로드 완료: {count_new}개 추가, {count_update}개 업데이트됨")
        )


    # --- Nodes ---
    def load_nodes(self, reader):
        count_new = 0
        count_update = 0

        def parse_str(value):
            return value.strip() if value else None

        for row in reader:
            obj, created = Nodes.objects.update_or_create(
                node_id=row["node_id"],  # PK 기준으로 중복 체크
                defaults={
                    "line": parse_str(row.get("line")),
                    "node_name": parse_str(row.get("node_name")),
                    "floor": parse_str(row.get("floor")),
                    "type": parse_str(row.get("type")),
                    "station": parse_str(row.get("station")),
                },
            )
            if created:
                count_new += 1
            else:
                count_update += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"✅ nodes.csv 업로드 완료: {count_new}개 추가, {count_update}개 업데이트됨"
            )
        )
