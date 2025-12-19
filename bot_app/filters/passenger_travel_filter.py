# filters/passenger_travel_filter.py
import django_filters
from ..models import PassengerTravel


class PassengerTravelFilter(django_filters.FilterSet):
    from_city = django_filters.CharFilter(
        field_name='from_location__city',
        lookup_expr='icontains'
    )
    to_city = django_filters.CharFilter(
        field_name='to_location__city',
        lookup_expr='icontains'
    )
    min_price = django_filters.NumberFilter(
        field_name='price',
        lookup_expr='gte'
    )
    max_price = django_filters.NumberFilter(
        field_name='price',
        lookup_expr='lte'
    )
    max_rate = django_filters.NumberFilter(
        field_name='rate',
        lookup_expr='lte'
    )
    min_rate = django_filters.NumberFilter(
        field_name='rate',
        lookup_expr='gte'
    )
    min_start_time = django_filters.DateTimeFilter(field_name="created_at", lookup_expr='gte')
    max_start_time = django_filters.DateTimeFilter(field_name="created_at", lookup_expr='lte')

    destination = django_filters.CharFilter(field_name="destination", lookup_expr='icontains')

    class Meta:
        model = PassengerTravel
        fields = {
            'user': ['exact'],
            'travel_class': ['exact'],
            'has_woman': ['exact'],
        }
