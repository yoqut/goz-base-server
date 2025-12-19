# bot_app/views/driver_views.py
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Sum
from ..models import DriverStatus, Driver, DriverTransaction
from ..serializers.driver import DriverSerializer, DriverListSerializer, DriverUpdateSerializer, \
    DriverTransactionSerializer, DriverCreateSerializer
from ..filters.driver_filter import DriverFilter, DriverTransactionFilter


class DriverViewSet(viewsets.ModelViewSet):
    """
    Driverlar uchun ViewSet
    """
    queryset = Driver.objects.all()
    serializer_class = DriverSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = DriverFilter
    search_fields = ['from_location', 'to_location',]
    ordering_fields = ['created_at', 'amount']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return DriverListSerializer
        elif self.action in ['update', 'partial_update']:
            return DriverUpdateSerializer
        elif self.action == 'create':
            return DriverCreateSerializer
        return DriverSerializer

    @action(detail=False, methods=['get'], url_path='by-telegram-id/(?P<telegram_id>[^/.]+)')
    def by_telegram_id(self, request, telegram_id=None):
        """Telegram ID bo'yicha driver qidirish"""
        if not telegram_id:
            return Response(
                {'error': 'telegram_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            telegram_id = int(telegram_id)
        except ValueError:
            return Response(
                {'error': 'telegram_id must be an integer'},
                status=status.HTTP_400_BAD_REQUEST
            )

        driver = get_object_or_404(Driver, telegram_id=telegram_id)
        serializer = self.get_serializer(driver)
        return Response(serializer.data)

    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        """Driver statusini yangilash"""
        driver = self.get_object()
        new_status = request.data.get('status')

        if new_status not in dict(DriverStatus.choices):
            return Response(
                {'error': 'Invalid status'},
                status=status.HTTP_400_BAD_REQUEST
            )

        driver.status = new_status
        driver.save()

        return Response({
            'message': 'Status updated successfully',
            'status': driver.status,
            'status_display': driver.get_status_display()
        })

    @action(detail=False, methods=['get'])
    def search(self, request):
        """Driverlarni qidirish"""
        query = request.query_params.get('q', '')

        if not query:
            return Response(
                {'error': 'Search query (q) parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        drivers = Driver.objects.filter(
            Q(from_location__icontains=query) |
            Q(to_location__icontains=query) |
            Q(phone__icontains=query)
        )

        serializer = DriverListSerializer(drivers, many=True)
        return Response(serializer.data)

class DriverTransactionViewSet(viewsets.ModelViewSet):
    """
    Driver transaksiyalari uchun ViewSet
    """
    queryset = DriverTransaction.objects.all().select_related('driver')
    serializer_class = DriverTransactionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = DriverTransactionFilter
    ordering_fields = ['created_at', 'amount']
    ordering = ['-created_at']

    @action(detail=False, methods=['get'])
    def driver_stats(self, request):
        """Driver statistikasi"""
        driver_id = request.query_params.get('driver_id')

        if not driver_id:
            return Response(
                {'error': 'driver_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            driver = Driver.objects.get(id=driver_id)
            transactions = DriverTransaction.objects.filter(driver=driver)
            total_earnings = transactions.aggregate(total=Sum('amount'))['total'] or 0

            return Response({
                'driver_id': driver_id,
                'driver_name': driver.from_location,
                'total_earnings': total_earnings,
                'transaction_count': transactions.count(),
                'current_balance': driver.amount
            })

        except Driver.DoesNotExist:
            return Response(
                {'error': 'Driver not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(methods=["patch"], detail=False, url_path='separation_amount/')
    def separation_amount(self, request):
        driver_id = request.query_params.get('driver_id')
        price = request.query_params.get('price')
        if not driver_id and not price:
            return Response(
                {'error': 'driver_id parameter is required'},
            )
        try:
            driver = Driver.objects.get(id=driver_id)
            driver.amount -= float(price)
            driver.save()
            return Response({
                'driver': DriverSerializer(driver).data,

            },
            status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_404_NOT_FOUND
            )


