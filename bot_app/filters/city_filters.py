# filters.py
from django_filters import rest_framework as filters
from ..models import City


class CityFilter(filters.FilterSet):
    title = filters.CharFilter(lookup_expr='icontains')
    has_children = filters.BooleanFilter(method='filter_has_children')
    created_after = filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')

    class Meta:
        model = City
        fields = {
            'title': ['exact', 'icontains'],
            'is_allowed': ['exact'],
            'subcategory': ['exact', 'isnull'],
        }

    def filter_has_children(self, queryset, name, value):
        if value:
            return queryset.filter(children__isnull=False).distinct()
        return queryset.filter(children__isnull=True)