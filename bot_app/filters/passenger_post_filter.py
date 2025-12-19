# filters/passenger_post_filter.py
import django_filters
from ..models import PassengerPost


class PassengerPostFilter(django_filters.FilterSet):
    min_price = django_filters.NumberFilter(field_name="price", lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name="price", lookup_expr='lte')
    min_created = django_filters.DateTimeFilter(field_name="created_at", lookup_expr='gte')
    max_created = django_filters.DateTimeFilter(field_name="created_at", lookup_expr='lte')
    min_start_time = django_filters.DateTimeFilter(field_name="created_at", lookup_expr='gte')
    max_start_time = django_filters.DateTimeFilter(field_name="created_at", lookup_expr='lte')

    destination = django_filters.CharFilter(field_name="destination", lookup_expr='icontains')
    # Add filters for JSON field and CharField
    from_location = django_filters.CharFilter(field_name="from_location", lookup_expr='icontains')
    to_location = django_filters.CharFilter(field_name="to_location", lookup_expr='icontains')

    # If you want to search within specific keys of the JSON field
    from_city = django_filters.CharFilter(method='filter_from_city')
    to_city = django_filters.CharFilter(field_name="to_location", lookup_expr='icontains')

    class Meta:
        model = PassengerPost
        fields = {
            'user': ['exact'],
            'price': ['exact', 'gte', 'lte'],
        }

    def filter_from_city(self, queryset, name, value):
        """
        Custom filter for searching city in from_location JSON field
        Assuming from_location structure like: {"city": "Tashkent", ...}
        """
        return queryset.filter(from_location__icontains=value)