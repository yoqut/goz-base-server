# views.py

from django.db import models
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from ..models import BotClient
from ..serializers.bot_client import BotClientCreateSerializer, BotClientUpdateSerializer, BotClientListSerializer, \
    BotClientSerializer
from ..filters.bot_client_filters import BotClientFilter


class BotClientViewSet(viewsets.ModelViewSet):
    queryset = BotClient.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = BotClientFilter
    search_fields = ['full_name', 'username',]
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'create':
            return BotClientCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return BotClientUpdateSerializer
        elif self.action == 'list':
            return BotClientListSerializer
        return BotClientSerializer

    def get_queryset(self):
        """Return base queryset"""
        return BotClient.objects.all()

    def get_object(self):
        """Get object by telegram_id if 'pk' is provided as telegram_id"""
        # Check if we're looking up by telegram_id instead of primary key
        if 'pk' in self.kwargs and str(self.kwargs['pk']).isdigit():
            pk = int(self.kwargs['pk'])
            # Try to find by telegram_id first
            try:
                return BotClient.objects.get(telegram_id=pk)
            except BotClient.DoesNotExist:
                # Fall back to primary key lookup
                try:
                    return BotClient.objects.get(pk=pk)
                except BotClient.DoesNotExist:
                    pass
        return super().get_object()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            # Telegram ID unikal ligini tekshirish
            telegram_id = serializer.validated_data.get('telegram_id')
            if BotClient.objects.filter(telegram_id=telegram_id).exists():
                return Response(
                    {'error': 'Bu Telegram ID bilan foydalanuvchi mavjud'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(
                BotClientSerializer(serializer.instance).data,
                status=status.HTTP_201_CREATED,
                headers=headers
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    @action(detail=False, methods=['get'], url_path='by-telegram-id/(?P<telegram_id>[^/.]+)')
    def by_telegram_id(self, request, telegram_id=None):
        """Get client by telegram ID"""
        try:
            client = BotClient.objects.get(telegram_id=telegram_id)
            serializer = BotClientSerializer(client)
            return Response(serializer.data)
        except BotClient.DoesNotExist:
            return Response(
                {'error': 'Foydalanuvchi topilmadi'},
                status=status.HTTP_404_NOT_FOUND
            )
