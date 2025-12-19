# serializers.py
from rest_framework import serializers
from ..models import Passenger, BotClient


class PassengerSerializer(serializers.ModelSerializer):
    language = serializers.SerializerMethodField()

    class Meta:
        model = Passenger
        fields = [
            'id', 'telegram_id', "language", 'full_name', 'total_rides',
            'phone', 'rating'
        ]
        read_only_fields = ['id']

    def get_language(self, obj):
        client = BotClient.objects.get(telegram_id=obj.telegram_id)
        return client.language


class PassengerCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Passenger
        fields = ['telegram_id', 'full_name', 'phone']

    def validate_telegram_id(self, value):
        if Passenger.objects.filter(telegram_id=value).exists():
            raise serializers.ValidationError("Bu telegram ID bilan foydalanuvchi mavjud")
        return value


class PassengerUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Passenger
        fields = ['full_name', 'phone', 'rating', 'total_rides']


class PassengerListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Passenger
        fields = ['id', 'telegram_id', 'phone', 'full_name', 'total_rides', 'rating']