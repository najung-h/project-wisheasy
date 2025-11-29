from rest_framework import serializers
from .models import Facility, FacilityLoc

class FacilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Facility
        fields = ['facility_id', 'facility_name']

class FacilityLocSerializer(serializers.ModelSerializer):
    # FK로 따라가서 이름까지 같이 내려주기
    station_name = serializers.CharField(source='station.name', read_only=True)
    line_name = serializers.CharField(source='line.name', read_only=True)
    facility_name = serializers.CharField(source='facility.facility_name', read_only=True)


    class Meta:
        model = FacilityLoc
        fields = [
            'id',
            'detail_loc',
            'station',
            'station_name',
            'line',
            'line_name',
            'facility',
            'facility_name'
        ]