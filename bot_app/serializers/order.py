# serializers.py
from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType
from django.core.serializers.json import DjangoJSONEncoder
import json

from .bot_client import BotClientSerializer
from .driver import DriverSerializer
from .passenger import PassengerSerializer
from ..models import Order, PassengerTravel, PassengerPost, TravelStatus, OrderType, Driver, BotClient, Passenger, City


class ContentObjectSerializer(serializers.Serializer):
    """Generic content object serializer"""

    def to_representation(self, instance):
        if isinstance(instance, PassengerTravel):
            return {
                'type': 'passengertravel',
                'id': instance.pk,
                'from_location': instance.from_location,
                'to_location': instance.to_location,
                'travel_class': instance.travel_class,
                'rate': instance.rate,
                'passenger': instance.passenger,
                'has_woman': instance.has_woman,
                'price': str(instance.price) if instance.price else None,  # Decimal to string
                'created_at': instance.created_at.isoformat() if instance.created_at else None  # ISO format
            }
        elif isinstance(instance, PassengerPost):
            return {
                'type': 'passengerpost',
                'id': instance.pk,
                'from_location': instance.from_location,
                'to_location': instance.to_location,
                'travel_class': "delivery",
                'price': str(instance.price) if instance.price else None,  # Decimal to string
                'created_at': instance.created_at.isoformat() if instance.created_at else None  # ISO format
            }
        return None

    def get_serialized_data(self, instance):
        """JSON serializatsiya uchun maxsus metod"""
        data = self.to_representation(instance)
        # DjangoJSONEncoder bilan serializatsiya
        return json.loads(json.dumps(data, cls=DjangoJSONEncoder))


class OrderSerializer(serializers.ModelSerializer):
    content_object = ContentObjectSerializer(read_only=True)
    driver_details = DriverSerializer(source='driver', read_only=True)
    content_type_name = serializers.CharField(source='content_type.model', read_only=True)
    creator = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'id', 'user', 'creator', 'driver', 'driver_details', 'status',
            'order_type', 'content_object', 'content_type_name',
        ]
        read_only_fields = ['id', 'content_object']

    def get_creator(self, obj):
        try:
            creator = Passenger.objects.get(telegram_id=obj.user)
            return PassengerSerializer(creator).data
        except Exception as e:
            print(e)
            return {}

    def to_representation(self, instance):
        """Override to handle datetime serialization"""
        representation = super().to_representation(instance)

        # Datetime fieldlarni ISO formatga o'tkazish
        if representation.get('created_at'):
            representation['created_at'] = instance.created_at.isoformat()

        if representation.get('updated_at'):
            representation['updated_at'] = instance.updated_at.isoformat()

        # Content objectni serializatsiya qilish
        if instance.content_object:
            content_serializer = ContentObjectSerializer()
            representation['content_object'] = content_serializer.get_serialized_data(instance.content_object)

        return representation


class OrderCreateSerializer(serializers.ModelSerializer):
    content_type = serializers.ChoiceField(
        choices=['passengertravel', 'passengerpost'],
        write_only=True
    )
    object_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Order
        fields = ['user', 'order_type', 'content_type', 'object_id']

    def validate(self, attrs):
        content_type_name = attrs.get('content_type')
        object_id = attrs.get('object_id')
        order_type = attrs.get('order_type')

        # Content type va object mavjudligini tekshirish
        try:
            content_type = ContentType.objects.get(model=content_type_name)
            model_class = content_type.model_class()
            obj = model_class.objects.get(id=object_id)
        except ContentType.DoesNotExist:
            raise serializers.ValidationError({
                'content_type': 'Noto\'g\'ri content type'
            })
        except model_class.DoesNotExist:
            raise serializers.ValidationError({
                'object_id': f'{content_type_name} topilmadi'
            })

        # Order type va content type mos kelishini tekshirish
        if (order_type == OrderType.TRAVEL and
                content_type_name != 'passengertravel'):
            raise serializers.ValidationError({
                'order_type': 'Travel order faqat PassengerTravel ga bog\'lanishi kerak'
            })
        elif (order_type == OrderType.DELIVERY and
              content_type_name != 'passengerpost'):
            raise serializers.ValidationError({
                'order_type': 'Delivery order faqat PassengerPost ga bog\'lanishi kerak'
            })

        return attrs

    def create(self, validated_data):
        content_type_name = validated_data.pop('content_type')
        object_id = validated_data.pop('object_id')

        content_type = ContentType.objects.get(model=content_type_name)

        return Order.objects.create(
            **validated_data,
            content_type=content_type,
            object_id=object_id
        )


class OrderUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['driver', 'status']


class OrderListSerializer(serializers.ModelSerializer):
    driver_details = serializers.SerializerMethodField()
    creator = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'id', 'user', 'creator', 'driver', 'driver_details', 'status', 'order_type', 'object_id',
        ]

    def get_driver_details(self, obj):
        try:
            driver = Driver.objects.get(id=obj.driver.id)
            return DriverSerializer(driver).data
        except Exception as e:
            return None

    def get_creator(self, obj):
        try:
            creator = BotClient.objects.get(telegram_id=obj.user)
            return BotClientSerializer(creator).data
        except Exception as e:
            print(e)
            return {}