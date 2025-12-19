# bot_app/filters/driver_filter.py
from django.db.models.functions import Coalesce
from django_filters import rest_framework as filters
from django.db.models import Q, OuterRef, Exists, Subquery, Count
from ..models import Driver, Car, DriverTransaction, DriverStatus, TravelClass, Order, TravelStatus


class DriverFilter(filters.FilterSet):
    # Asosiy filterlar
    status = filters.ChoiceFilter(choices=DriverStatus.choices)
    from_location = filters.CharFilter(field_name='from_location__title', lookup_expr='icontains')
    to_location = filters.CharFilter(field_name='to_location__title', lookup_expr='icontains')
    phone = filters.CharFilter(lookup_expr='icontains')
    telegram_id = filters.CharFilter(lookup_expr='icontains')

    # Range filterlar
    min_amount = filters.NumberFilter(field_name='amount', lookup_expr='gte')
    max_amount = filters.NumberFilter(field_name='amount', lookup_expr='lte')
    min_rating = filters.NumberFilter(field_name='rating', lookup_expr='gte')
    max_rating = filters.NumberFilter(field_name='rating', lookup_expr='lte')

    # Date filterlar
    created_after = filters.DateFilter(field_name='created_at', lookup_expr='gte')
    created_before = filters.DateFilter(field_name='created_at', lookup_expr='lte')

    # Universal location filter
    location = filters.CharFilter(method='filter_by_location')
    car_class = filters.CharFilter(method='filter_by_car_class')

    # Yangi filter: Faqat bo'sh driverlarni olish
    exclude_busy = filters.BooleanFilter(method='filter_exclude_busy', label="Exclude busy drivers")

    class Meta:
        model = Driver
        fields = ['telegram_id', 'status', 'from_location', 'to_location', "exclude_busy"]

    def filter_by_location(self, queryset, name, value):
        return queryset.filter(
            Q(from_location__title__icontains=value) |
            Q(to_location__title__icontains=value)
        )

    def filter_by_car_class(self, queryset, name, value):
        """
        economy  -> economy
        standard -> standard, comfort
        comfort  -> comfort
        """

        if isinstance(value, (list, tuple, set)):
            return queryset.filter(
                driver__car_class__in=value
            ).distinct()

        return queryset.filter(
            driver__car_class=value
        ).distinct()

    def filter_exclude_busy(self, queryset, name, value):
        """Faol orderlari 4 tadan ortiq bo'lgan driverlarni chiqarib tashlash"""
        if value:
            active_statuses = [
                TravelStatus.CREATED,
                TravelStatus.ASSIGNED,
                TravelStatus.ARRIVED,
                TravelStatus.STARTED
            ]

            # Faol orderlar sonini hisoblash
            active_order_count = Order.objects.filter(
                driver=OuterRef('pk'),
                status__in=active_statuses
            ).values('driver').annotate(
                count=Count('id')
            ).values('count')

            # Faol orderlar sonini annotation qo'shish
            queryset = queryset.annotate(
                active_order_count=Coalesce(Subquery(active_order_count), 0)
            ).filter(
                active_order_count__lt=4  # 4 tadan kam bo'lgan driverlarni qaytarish
            )

        return queryset

class CarFilter(filters.FilterSet):
    car_number = filters.CharFilter(lookup_expr='icontains')
    car_model = filters.CharFilter(lookup_expr='icontains')
    car_color = filters.CharFilter(lookup_expr='icontains')
    car_class = filters.ChoiceFilter(choices=TravelClass.choices)
    driver = filters.NumberFilter(field_name='driver__id')

    class Meta:
        model = Car
        fields = ['car_number', 'car_model', 'car_class', 'car_color', 'driver']


class DriverTransactionFilter(filters.FilterSet):
    driver = filters.NumberFilter(field_name='driver__id')
    min_amount = filters.NumberFilter(field_name='amount', lookup_expr='gte')
    max_amount = filters.NumberFilter(field_name='amount', lookup_expr='lte')

    class Meta:
        model = DriverTransaction
        fields = ['driver', 'amount']