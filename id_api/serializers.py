from rest_framework import serializers
from .models import IDCard

class IDCardSerializer(serializers.ModelSerializer):
    class Meta:
        model = IDCard
        fields = ['image']

class IDDataSerializer(serializers.Serializer):
    full_name = serializers.CharField()
    id_number = serializers.CharField()
    date_of_birth = serializers.CharField()
    address = serializers.CharField(required=False, allow_blank=True)