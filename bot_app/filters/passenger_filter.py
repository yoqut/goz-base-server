import django_filters

from bot_app.models import Passenger


class PassengerFilter(django_filters.FilterSet):
    telegram_id = django_filters.CharFilter(field_name='telegram_id', lookup_expr='icontains')
    min_rating = django_filters.NumberFilter(field_name="rating", lookup_expr='gte')
    max_rating = django_filters.NumberFilter(field_name="rating", lookup_expr='lte')
    min_rides = django_filters.NumberFilter(field_name="total_rides", lookup_expr='gte')
    max_rides = django_filters.NumberFilter(field_name="total_rides", lookup_expr='lte')
    created_after = django_filters.DateTimeFilter(field_name="created_at", lookup_expr='gte')
    created_before = django_filters.DateTimeFilter(field_name="created_at", lookup_expr='lte')

    class Meta:
        model = Passenger
        fields = {
            'full_name': ['icontains'],
            'phone': ['exact'],
        }