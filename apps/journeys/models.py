# Create your models here.

from django.db import models


# --- Edges 테이블 ---
class Edges(models.Model):
    edge_key = models.CharField(max_length=100, primary_key=True)
    relation = models.CharField(max_length=100)
    escalator = models.IntegerField(default=0)
    out_of_order = models.IntegerField(default=0)
    is_escalator = models.IntegerField(null=True, blank=True)
    source = models.CharField(max_length=100)
    target = models.CharField(max_length=100)

    class Meta:
        db_table = 'edges'

    def __str__(self):
        return f"{self.edge_key} ({self.relation})"


# --- Stations 테이블 ---
class Stations(models.Model):
    station = models.CharField(max_length=100)
    line = models.CharField(max_length=50)

    class Meta:
        db_table = 'stations'
        unique_together = ('station', 'line')

    def __str__(self):
        return f"{self.station} ({self.line})"


# --- Nodes 테이블 ---
class Nodes(models.Model):
    node_id = models.CharField(max_length=100, primary_key=True)
    line = models.CharField(max_length=50)
    node_name = models.CharField(max_length=100)
    floor = models.CharField(max_length=20)
    type = models.CharField(max_length=50)
    station = models.CharField(max_length=100)

    class Meta:
        db_table = 'nodes'

    def __str__(self):
        return f"{self.node_name} ({self.line})"


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