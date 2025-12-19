# views.py
from rest_framework import viewsets, filters, status
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.response import Response

from ..models import Order
from ..serializers.order import (
    OrderSerializer, OrderCreateSerializer, OrderUpdateSerializer, OrderListSerializer,
)
from ..filters.order_filters import OrderFilter


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all().select_related(
        'driver', 'content_type'
    )
    serializer_class = OrderSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = OrderFilter
    search_fields = ['user', 'driver__name', 'content_type__model']
    ordering_fields = [
        'id', 'user', 'status', 'order_type',
        'created_at', 'updated_at'
    ]
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'create':
            return OrderCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return OrderUpdateSerializer
        elif self.action == 'list':
            return OrderListSerializer
        return OrderSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        # Dynamic filtering based on query parameters
        status_list = self.request.query_params.get('status_list')
        if status_list:
            statuses = status_list.split(',')
            queryset = queryset.filter(status__in=statuses)

        # Order type list filter
        order_type_list = self.request.query_params.get('order_type_list')
        if order_type_list:
            types = order_type_list.split(',')
            queryset = queryset.filter(order_type__in=types)

        return queryset

    @action(detail=False, methods=['get'], url_path="user/(?P<telegram_id>[^/.]+)")
    def by_telegram_id(self, request, telegram_id=None):
        try:
            telegram_id = int(telegram_id)
            order = Order.objects.filter(user=telegram_id)
            serializer = OrderListSerializer(order, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ValueError:
            return Response(
                {'error': 'Noto\'g\'ri telegram ID formati'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Order.DoesNotExist:
            return Response(
                {'error': 'Foydalanuvchi topilmadi'},
                status=status.HTTP_404_NOT_FOUND
            )