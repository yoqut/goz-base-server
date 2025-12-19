# views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Q

from ..filters.passenger_travel_filter import PassengerTravelFilter
from ..models import PassengerTravel
from ..serializers.passenger_travel import (
    PassengerTravelSerializer,
    PassengerTravelCreateSerializer,
    PassengerTravelUpdateSerializer
)


class PassengerTravelViewSet(viewsets.ModelViewSet):
    queryset = PassengerTravel.objects.all()
    filterset_class = PassengerTravelFilter
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = [
        'user', 'travel_class', 'has_woman'
    ]
    search_fields = [
        'user'  # JSON fieldlarni oddiy search qila olmaydi, shuning uchun olib tashladik
    ]
    ordering_fields = [
        'price', 'passenger', 'created_at', 'updated_at'
    ]
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'create':
            return PassengerTravelCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return PassengerTravelUpdateSerializer
        return PassengerTravelSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        full_serializer = PassengerTravelSerializer(instance)

        return Response(full_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], url_path='by-telegram-id/(?P<telegram_id>[^/.]+)')
    def by_user(self, request, telegram_id=None):
        """Get posts by specific user"""
        if not telegram_id:
            return Response(
                {'error': 'user_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        travels = PassengerTravel.objects.filter(user=telegram_id)
        serializer = self.get_serializer(travels, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def search_routes(self, request):
        """Search for travels by from and to locations (JSON field uchun)"""
        from_city = request.query_params.get('from')
        to_city = request.query_params.get('to')

        queryset = self.filter_queryset(self.get_queryset())

        if from_city:
            # JSON field ichida qidirish
            queryset = queryset.filter(from_location__city__icontains=from_city)
        if to_city:
            # JSON field ichida qidirish
            queryset = queryset.filter(to_location__city__icontains=to_city)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def search_locations(self, request):
        """Kengaytirilgan location search (from yoki to da qidirish)"""
        search_term = request.query_params.get('q')
        if not search_term:
            return Response(
                {'error': 'q parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # from_location yoki to_location da qidirish
        queryset = self.filter_queryset(self.get_queryset()).filter(
            Q(from_location__city__icontains=search_term) |
            Q(to_location__city__icontains=search_term)
        )

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def get_queryset(self):
        """Asosiy queryset - JSON fieldlarni optimize qilish"""
        queryset = super().get_queryset()

        # Faqat kerakli fieldlarni select qilish
        if self.action == 'list':
            queryset = queryset.select_related()  # Agar related modellar bo'lsa

        return queryset