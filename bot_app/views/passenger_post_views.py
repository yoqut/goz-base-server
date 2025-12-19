# views/passenger_post_views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from ..filters.passenger_post_filter import PassengerPostFilter
from ..models import PassengerPost
from ..serializers.passenger_post import (
    PassengerPostSerializer,
    PassengerPostCreateSerializer,
    PassengerPostUpdateSerializer,
    PassengerPostListSerializer
)


class PassengerPostViewSet(viewsets.ModelViewSet):
    queryset = PassengerPost.objects.all()
    filterset_class = PassengerPostFilter
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['user',]
    search_fields = ['from_location', 'to_location']
    ordering_fields = ['price', 'created_at', 'updated_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'create':
            return PassengerPostCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return PassengerPostUpdateSerializer
        elif self.action == 'list':
            return PassengerPostListSerializer
        return PassengerPostSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()

        # Return full object after creation
        full_serializer = PassengerPostSerializer(instance)
        return Response(full_serializer.data, status=status.HTTP_201_CREATED)


    @action(detail=False, methods=['get'], url_path='by-telegram-id/(?P<telegram_id>[^/.]+)')
    def by_user(self, request, telegram_id=None):
        """Get posts by specific user"""
        if not telegram_id:
            return Response(
                {'error': 'user_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        posts = PassengerPost.objects.filter(user=telegram_id)
        serializer = self.get_serializer(posts, many=True)
        return Response(serializer.data)
