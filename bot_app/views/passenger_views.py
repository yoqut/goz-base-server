# views.py
from rest_framework import viewsets, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.shortcuts import get_object_or_404

from ..filters.passenger_filter import PassengerFilter
from ..models import Passenger
from ..serializers.passenger import (
    PassengerSerializer,
    PassengerCreateSerializer,
    PassengerUpdateSerializer,
    PassengerListSerializer
)


class PassengerViewSet(viewsets.ModelViewSet):
    queryset = Passenger.objects.all()
    filterset_class = PassengerFilter
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['rating', 'total_rides']
    search_fields = ['full_name', 'phone']
    ordering_fields = ['rating', 'total_rides', 'created_at']
    ordering = ['-rating']

    def get_serializer_class(self):
        if self.action == 'create':
            return PassengerCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return PassengerUpdateSerializer
        elif self.action == 'list':
            return PassengerListSerializer
        return PassengerSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except serializers.ValidationError as e:
            # Xatolikni aniqroq qaytarish
            error_detail = {}
            if 'telegram_id' in e.detail:
                error_detail['telegram_id'] = ['Bu telegram ID bilan foydalanuvchi mavjud']
            if 'phone' in e.detail:
                error_detail['phone'] = ['Bu telefon raqam bilan foydalanuvchi mavjud']

            return Response(
                error_detail or e.detail,
                status=status.HTTP_400_BAD_REQUEST
            )

        # Telegram ID qo'shimcha tekshirish
        telegram_id = serializer.validated_data.get('telegram_id')
        if Passenger.objects.filter(telegram_id=telegram_id).exists():
            return Response(
                {'telegram_id': ['Bu telegram ID bilan foydalanuvchi mavjud']},
                status=status.HTTP_400_BAD_REQUEST
            )

        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            PassengerSerializer(instance=serializer.instance).data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )

    @action(detail=False, methods=['get'], url_path='user/(?P<telegram_id>[^/.]+)')
    def by_telegram_id(self, request, telegram_id=None):
        try:
            telegram_id = int(telegram_id)
            passenger = get_object_or_404(Passenger, telegram_id=telegram_id)
            serializer = PassengerSerializer(passenger)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ValueError:
            return Response(
                {'error': 'Noto\'g\'ri telegram ID formati'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Passenger.DoesNotExist:
            return Response(
                {'error': 'Foydalanuvchi topilmadi'},
                status=status.HTTP_404_NOT_FOUND
            )