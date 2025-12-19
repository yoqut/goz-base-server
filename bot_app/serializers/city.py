# serializers.py
from rest_framework import serializers
from rest_framework.fields import SerializerMethodField

from ..models import City, CityPrice


class CitySerializer(serializers.ModelSerializer):
    subcategory_title = serializers.CharField(source='subcategory.title', read_only=True)
    subcategory_id = serializers.IntegerField(source='subcategory.id', read_only=True)
    price = SerializerMethodField()

    class Meta:
        model = City
        fields = [
            'id', 'title', 'price', 'translate', 'subcategory', 'latitude', 'longitude', 'subcategory_title',
            'subcategory_id',
            'is_allowed', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_price(self, obj):
        try:
            city_price = CityPrice.objects.get(city=obj)  # ✅ obj is the City instance
            return CityPriceSerializer(city_price).data
        except CityPrice.DoesNotExist:
            return {}


class CityPriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = CityPrice
        fields = [
            "economy", "comfort", "standard", "delivery",
        ]


class CityCreateSerializer(serializers.ModelSerializer):
    latitude = serializers.FloatField(required=False, write_only=True)
    longitude = serializers.FloatField(required=False, write_only=True)
    price = serializers.DictField(
        required=False,
        write_only=True,
        help_text="Price object containing economy, comfort, standard fields"
    )

    class Meta:
        model = City
        fields = [
            'title', 'subcategory', 'translate', 'is_allowed',
            'latitude', 'longitude', 'price'
        ]

    def validate(self, data):
        price = data.get('price')
        if price:
            # Price validatsiyasi
            required_fields = ['economy', 'comfort', 'standard', 'delivery']
            for field in required_fields:
                if field not in price:
                    raise serializers.ValidationError({
                        "price": f"{field} field is required in price object"
                    })

                # Agar raqam emas bo'lsa
                if not isinstance(price[field], (int, float)):
                    try:
                        price[field] = float(price[field])
                    except (ValueError, TypeError):
                        raise serializers.ValidationError({
                            "price": f"{field} must be a number"
                        })

        return data

    def create(self, validated_data):
        # Ajratib olish
        price_data = validated_data.pop('price', None)

        # City yaratish
        city = super().create(validated_data)

        # Agar price bo'lsa, CityPrice yaratish
        if price_data:
            CityPrice.objects.create(
                city=city,
                economy=price_data.get('economy', 0),
                comfort=price_data.get('comfort', 0),
                standard=price_data.get('standard', 0),
                delivery=price_data.get('delivery', 0)
            )

        return city

    def update(self, instance, validated_data):
        # Ajratib olish
        price_data = validated_data.pop('price', None)

        # City yangilash
        city = super().update(instance, validated_data)

        # Agar price bo'lsa, CityPrice ni yangilash yoki yaratish
        if price_data is not None:
            try:
                city_price = CityPrice.objects.get(city=city)
                city_price.economy = price_data.get('economy', city_price.economy)
                city_price.comfort = price_data.get('comfort', city_price.comfort)
                city_price.standard = price_data.get('standard', city_price.standard)
                city_price.delivery = price_data.get('delivery', city_price.standard)
                city_price.save()
            except CityPrice.DoesNotExist:
                CityPrice.objects.create(
                    city=city,
                    economy=price_data.get('economy', 0),
                    comfort=price_data.get('comfort', 0),
                    standard=price_data.get('standard', 0),
                    delivery=price_data.get('delivery', 0)
                )

        return city


class LocationCheckSerializer(serializers.Serializer):
    latitude = serializers.FloatField(required=True, min_value=-90, max_value=90)
    longitude = serializers.FloatField(required=True, min_value=-180, max_value=180)
    max_distance_km = serializers.FloatField(default=20.0, min_value=1, max_value=200)


class LocationCheckResponseSerializer(serializers.Serializer):
    is_in_city = serializers.BooleanField()
    city = serializers.DictField(required=False)  # ✅ shunday qiling
    distance_km = serializers.FloatField(required=False)
    address_info = serializers.DictField()
    message = serializers.CharField()
    match_type = serializers.CharField(required=False)


class CityValidationSerializer(serializers.Serializer):
    city_name = serializers.CharField(required=True)
    latitude = serializers.FloatField(required=True, min_value=-90, max_value=90)
    longitude = serializers.FloatField(required=True, min_value=-180, max_value=180)


class CityValidationResponseSerializer(serializers.Serializer):
    valid = serializers.BooleanField()
    distance_km = serializers.FloatField()
    max_distance_km = serializers.FloatField()
    city_coordinates = serializers.DictField()
    user_location = serializers.DictField()
    city_location = serializers.DictField()
    message = serializers.CharField()


class NearbyCitiesResponseSerializer(serializers.Serializer):
    city = CitySerializer()
    distance_km = serializers.FloatField()
    coordinates = serializers.DictField(required=False)
    match_type = serializers.CharField()
