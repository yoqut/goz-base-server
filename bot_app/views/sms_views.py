import json
import random

from ninja import NinjaAPI
import requests
from ninja.responses import Response

from bot_app.models import Driver, Passenger, DriverGallery, BotClient
from rest_framework import serializers
from configuration import env

api = NinjaAPI()

ESKIZ_HOST = env.ESKIZ_HOST
ESKIZ_EMAIL = env.ESKIZ_EMAIL
ESKIZ_PASSWORD = env.ESKIZ_PASSWORD


def _get_token():
    response = requests.post(
        ESKIZ_HOST + '/api/auth/login',
        json={
            'email': ESKIZ_EMAIL,
            'password': ESKIZ_PASSWORD,
        }
    )

    result = response.json()
    return result.get('data', {}).get('token', "")


def _send_sms(to):
    code = random.randint(1000, 9999)
    response = requests.post(
        ESKIZ_HOST + '/api/message/sms/send',
        json={
            'mobile_phone': to,
            "message": f"G'oz Platformasidan ro'yxatdan o'tish kodi: {code}",
            "from": "4546",
            "callback_url": f"{env.DEFAULT_API_URL}/callback/",
        },
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {_get_token()}",
            "Accept": "application/json",
        }
    )
    data = response.json()
    data.update({"sms_code": code})
    return data


# Serializerlar
class DriverCarSerializer(serializers.ModelSerializer):
    # Bu serializer to'ldirilishi kerak
    class Meta:
        model = None  # Tegishli modelni qo'ying
        fields = '__all__'


class DriverSerializer(serializers.ModelSerializer):
    cars = DriverCarSerializer(many=True, read_only=True, source='driver')
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    profile_image = serializers.SerializerMethodField()
    full_profile_image_url = serializers.SerializerMethodField()

    class Meta:
        model = Driver
        fields = [
            'id',
            "telegram_id",
            "full_name",
            "total_rides",
            "phone",
            "rating",
            "from_location",
            "to_location",
            "status",
            "amount",
            "cars",
            "status_display",
            "profile_image",
            "full_profile_image_url"
        ]
        ref_name = 'DriverMainSerializer'

    def get_profile_image(self, obj):
        """Driverning profile rasmini olish (relative path)"""
        try:
            gallery = DriverGallery.objects.get(telegram_id=obj.telegram_id)
            return gallery.profile_image.url if gallery.profile_image else None
        except DriverGallery.DoesNotExist:
            return None

    def get_full_profile_image_url(self, obj):
        """Driverning profile rasmini to'liq URL sifatida olish"""
        try:
            gallery = DriverGallery.objects.get(telegram_id=obj.telegram_id)
            if gallery.profile_image:
                request = self.context.get('request')
                if request:
                    return request.build_absolute_uri(gallery.profile_image.url)
                return gallery.profile_image.url
        except DriverGallery.DoesNotExist:
            pass
        return None


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
        try:
            client = BotClient.objects.get(telegram_id=obj.telegram_id)
            return client.language
        except BotClient.DoesNotExist:
            return None


@api.post("/")
def auth_sms(request):
    """
    {
        "telegram_id": "1230394567",
        "phone": 998990347378,
        "is_driver": true
    }
    """
    try:
        result = json.loads(request.body)
    except json.JSONDecodeError:
        return Response(
            data={
                "status": "error",
                "message": "Invalid JSON format",
            },
            status=400
        )

    phone = result.get("phone")
    is_driver = result.get("is_driver")
    telegram_id = result.get("telegram_id")

    if not all([phone, telegram_id]):
        return Response(
            data={
                "status": "error",
                "message": "phone and telegram_id are required fields"
            },
            status=400
        )

    ModelClass = Driver if is_driver else Passenger
    SerializerClass = DriverSerializer if is_driver else PassengerSerializer

    try:
        # Foydalanuvchini telegram_id bo'yicha qidirish
        instance = ModelClass.objects.get(telegram_id=telegram_id)
        try:
            check_instance = ModelClass.objects.get(phone=str(phone))
        except ModelClass.DoesNotExist:
            check_instance = None

        if str(instance.phone) == str(phone) or check_instance:
            serializer = SerializerClass(instance, context={'request': request})

            return Response(
                data={
                    "status": "error",
                    "result": serializer.data,
                    "message": "User already exists",
                    "telegram_id": telegram_id
                },
                status=400
            )
        else:
            try:
                sms_result = _send_sms(phone)

                return Response(
                    data={
                        "status": "success",
                        "result": sms_result,
                        "message": "SMS sent successfully",
                        "telegram_id": telegram_id
                    }
                )

            except Exception as sms_ex:
                return Response(
                    data={
                        "status": "error",
                        "message": f"SMS sending failed: {str(sms_ex)}",
                        "telegram_id": telegram_id
                    },
                    status=500
                )


    except ModelClass.DoesNotExist:
        # Yangi foydalanuvchi, SMS yuborish
        try:
            sms_result = _send_sms(phone)

            return Response(
                data={
                    "status": "success",
                    "result": sms_result,
                    "message": "SMS sent successfully",
                    "telegram_id": telegram_id
                }
            )

        except Exception as sms_ex:
            return Response(
                data={
                    "status": "error",
                    "message": f"SMS sending failed: {str(sms_ex)}",
                    "telegram_id": telegram_id
                },
                status=500
            )

    except Exception as ex:
        return Response(
            data={
                "status": "error",
                "message": str(ex),
                "telegram_id": telegram_id
            },
            status=500
        )



