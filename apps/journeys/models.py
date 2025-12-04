from django.db import models

# --- Station 테이블 --- 
class Station(models.Model):
    id = models.CharField(max_length=10, primary_key=True)  # station_id
    name = models.CharField(max_length=20)  # station name

    # Line과 다대다 관계
    # (Django가 자동으로 중간 테이블 생성)
    lines = models.ManyToManyField('Line', related_name='station', db_table='stationline')

    class Meta:
        db_table = 'station'

    def __str__(self):
        return self.name

# --- Line 테이블 --- 
class Line(models.Model):
    id = models.CharField(max_length=10, primary_key=True)  # line_id
    name = models.CharField(max_length=50)  # line name

    class Meta:
        db_table = 'line'

    def __str__(self):
        return self.name


# --- Node 테이블 --- 
class Node(models.Model):
    id = models.CharField(max_length=20, primary_key=True)  # node_id
    name = models.CharField(max_length=50)  # node_name (ex: platform, stair)
    floor = models.CharField(max_length=10)  # floor information
    type = models.CharField(max_length=50)  # type of node (ex: platform, stair, escalator)
    station = models.ForeignKey(Station, on_delete=models.CASCADE)  # station_id (FK)

    class Meta:
        db_table = 'node'

    def __str__(self):
        return f"{self.name} ({self.station.name})"


# --- Fast_Gate 테이블 (빠른하차탑승구) --- 
class FastGate(models.Model):
    platform = models.CharField(max_length=50, default="")  # ex. 2호선 구의역 방면 승강장
    boarding_gate = models.CharField(max_length=50, default="") # ex. 4-2, 5-2
    transfer = models.BooleanField(default=False) 
    escalator = models.BooleanField(default=False)  

    class Meta:
        db_table = 'fast_gate'

    def __str__(self):
        return f"Fast Gate  {self.platform} {self.boarding_gate}"


# --- Edge 테이블 (노드 간의 연결) --- 
class Edge(models.Model):
    id = models.CharField(max_length=30, primary_key=True)  # edge_key
    escalator = models.BooleanField(default=False) 
    source_node = models.ForeignKey(Node, related_name="source_edges", on_delete=models.CASCADE)  # source_node_id
    target_node = models.ForeignKey(Node, related_name="target_edges", on_delete=models.CASCADE)  # target_node_id

    class Meta:
        db_table = 'edge'

    def __str__(self):
        return f"{self.source_node.name} -> {self.target_node.name}"


# --- Users 테이블 ---
class Users(models.Model):
    user_id = models.CharField(max_length=100, primary_key=True)
    profile_image = models.TextField(null=True, blank=True)
    nickname = models.CharField(max_length=50, null=True, blank=True)
    google_mail = models.CharField(max_length=100)
    password = models.CharField(max_length=100)

    class Meta:
        db_table = 'users'

    def __str__(self):
        return self.nickname or self.user_id


# --- Lines 테이블 ---
class Lines(models.Model):
    line = models.CharField(max_length=50)
    station = models.CharField(max_length=100)
    order_in_line = models.IntegerField()

    class Meta:
        db_table = 'lines'
        unique_together = ('line', 'order_in_line')

    def __str__(self):
        return f"{self.station} ({self.line})"
    
# --- Facility 테이블 (편의시설) ---
class Facility(models.Model):
    facility_id = models.IntegerField(primary_key=True)
    facility_name = models.CharField(max_length=50)  # 편의시설 이름

    class Meta:
        db_table = 'facility'

    def __str__(self):
        return self.facility_name
    
# --- FacilityLoc 테이블 (편의시설 위치 정보) ---
class FacilityLoc(models.Model):
    id = models.AutoField(primary_key=True)  # PK
    detail_loc = models.TextField()  # 상세 위치 정보
    station = models.ForeignKey(Station, on_delete=models.CASCADE)  # station_id FK
    line = models.ForeignKey(Line, on_delete=models.CASCADE)  # line_id FK
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE)  # 🔥 FK도 정수형을 참조하게 자동 적용됨

    class Meta:
        db_table = 'facility_loc'

    def __str__(self):
        return f"{self.facility.facility_name} at {self.station.name}"

class Escalator(models.Model):
    id = models.CharField(max_length=30, primary_key=True)
    operation = models.BooleanField(default=True)
    detail = models.CharField(
        max_length=50,
        null=True,
        blank=True
    )
    edge = models.ForeignKey(
        Edge,
        on_delete=models.CASCADE,
        related_name="escalator_detail"
    )

    class Meta:
        db_table = 'escalator'

    def __str__(self):
        return f"Escalator {self.id}"