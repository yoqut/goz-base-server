from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers

from .bot_client import BotClientSerializer
from ..models import PassengerTravel, Order, BotClient


class PassengerTravelSerializer(serializers.ModelSerializer):
    from_city = serializers.SerializerMethodField()
    to_city = serializers.SerializerMethodField()
    order_id = serializers.SerializerMethodField()
    creator = serializers.SerializerMethodField()


    class Meta:
        model = PassengerTravel
        fields = [
            'id', 'user', 'start_time', 'destination', 'creator', 'order_id', 'rate', 'from_location', 'to_location',
            'from_city', 'to_city', 'travel_class', 'passenger',
            'price', 'has_woman', "created_at"
        ]

        read_only_fields = ['id']

    def get_from_city(self, obj):
        """from_location dan city nomini olish"""
        if isinstance(obj.from_location, dict):
            return obj.from_location.get('city')
        return None

    def get_to_city(self, obj):
        """to_location dan city nomini olish"""
        if isinstance(obj.to_location, dict):
            return obj.to_location.get('city')
        return None

    def get_order_id(self, obj):
        """Get order_id after object is created"""
        try:
            order = Order.objects.filter(
                content_type=ContentType.objects.get_for_model(obj),
                object_id=obj.id
            ).first()
            return order.pk if order else None
        except Order.DoesNotExist:
            return None

    def get_creator(self, obj):
        """Get creator after object is created"""
        try:
            creator = BotClient.objects.get(telegram_id=obj.user)
            return BotClientSerializer(creator).data
        except BotClient.DoesNotExist:
            return {}

class PassengerTravelCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = PassengerTravel
        fields = [
            'user', 'from_location', 'to_location', 'travel_class',
            'passenger', 'price', 'has_woman'
        ]

    def validate_from_location(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("from_location must be a JSON object")
        return value

    def validate_to_location(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("to_location must be a JSON object")
        return value

class PassengerTravelUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PassengerTravel
        fields = [
            'rate', 'travel_class', 'passenger', 'price', 'has_woman'
        ]
