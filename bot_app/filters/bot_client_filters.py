# filters.py
import django_filters
from ..models import BotClient

class BotClientFilter(django_filters.FilterSet):
    telegram_id = django_filters.NumberFilter(field_name='telegram_id')
    is_active = django_filters.BooleanFilter(field_name='is_active')
    is_banned = django_filters.BooleanFilter(field_name='is_banned')
    language = django_filters.CharFilter(field_name='language')
    min_rating = django_filters.NumberFilter(field_name='rating', lookup_expr='gte')
    max_rating = django_filters.NumberFilter(field_name='rating', lookup_expr='lte')
    min_rides = django_filters.NumberFilter(field_name='total_rides', lookup_expr='gte')
    max_rides = django_filters.NumberFilter(field_name='total_rides', lookup_expr='lte')
    created_after = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')

    class Meta:
        model = BotClient
        fields = ['telegram_id', 'is_active', 'is_banned', 'language',
                 'min_rating', 'max_rating', 'min_rides', 'max_rides']