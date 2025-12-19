from asgiref.sync import async_to_sync, sync_to_async
from django.db.models import Q, Prefetch
from rest_framework import viewsets, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
import logging

from ..filters.city_filters import CityFilter
from ..models import City, CityPrice
from ..serializers.city import (
    CitySerializer,
    CityCreateSerializer,
    LocationCheckSerializer,
    LocationCheckResponseSerializer,
    CityValidationSerializer,
    CityValidationResponseSerializer,
    NearbyCitiesResponseSerializer
)
from ..services.location_service import GlobalLocationService

logger = logging.getLogger(__name__)


class CityViewSet(viewsets.ModelViewSet):
    queryset = City.objects.filter(is_allowed=True).prefetch_related(
        Prefetch('cityprice', queryset=CityPrice.objects.only('economy', 'comfort', 'standard'))
    )
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_allowed', 'subcategory']
    filterset_class = CityFilter
    search_fields = ['title']
    ordering_fields = ['title', 'created_at', 'updated_at']
    ordering = ['title']

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return CityCreateSerializer
        return CitySerializer

    def create(self, request, *args, **kwargs):
        """Sync wrapper for async create"""
        return async_to_sync(self._async_create)(request, *args, **kwargs)

    async def _async_create(self, request, *args, **kwargs):
        """Async create logic"""
        logger.debug(f"Create request data: {request.data}")

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        city = await sync_to_async(serializer.save)()
        response_data = await sync_to_async(self._prepare_city_response)(city, request)

        return Response(response_data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        """Sync wrapper for async update"""
        return async_to_sync(self._async_update)(request, *args, **kwargs)

    async def _async_update(self, request, *args, **kwargs):
        """Async update logic"""
        instance = await sync_to_async(self.get_object)()

        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data

        # Location validation
        latitude = validated_data.get('latitude', instance.latitude)
        longitude = validated_data.get('longitude', instance.longitude)
        city_title = validated_data.get('title', instance.title)

        if latitude and longitude and not request.data.get('skip_location_validation', False):
            validation_result = await GlobalLocationService.validate_city_location(
                city_title, latitude, longitude
            )

            if not validation_result["valid"]:
                return Response({
                    "error": "location_validation_failed",
                    "message": validation_result["message"],
                    "details": validation_result
                }, status=status.HTTP_400_BAD_REQUEST)

        city = await sync_to_async(serializer.save)()
        response_data = await sync_to_async(self._prepare_city_response)(city, request)

        return Response(response_data)

    def _prepare_city_response(self, city, request):
        """Sync method: Prepare city response data"""
        try:
            city_price = city.cityprice  # prefetch related dan olish
            price_data = {
                "economy": city_price.economy,
                "comfort": city_price.comfort,
                "standard": city_price.standard
            }
        except (CityPrice.DoesNotExist, AttributeError):
            price_data = None

        serializer = CitySerializer(city, context={'request': request})
        data = serializer.data

        if price_data:
            data['price'] = price_data
        else:
            data['price'] = None

        return data

    @action(detail=False, methods=['post'], url_path='check-location')
    def check_location(self, request):
        """Sync wrapper for async check_location"""
        logger.debug(f"Check location request: {request.data}")
        logger.debug(f"Content type: {request.content_type}")

        try:
            return async_to_sync(self._async_check_location)(request)
        except Exception as e:
            logger.error(f"Error in check_location: {str(e)}", exc_info=True)
            return Response({
                "error": "Internal server error",
                "details": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    async def _async_check_location(self, request):
        """Check if coordinates are within city area"""
        logger.debug(f"Async check_location called with data: {request.data}")

        serializer = LocationCheckSerializer(data=request.data)

        if not serializer.is_valid():
            logger.error(f"Serializer validation errors: {serializer.errors}")
            logger.error(f"Raw data that failed validation: {request.data}")
            raise serializers.ValidationError(serializer.errors)

        lat = serializer.validated_data['latitude']
        lon = serializer.validated_data['longitude']
        max_distance = serializer.validated_data['max_distance_km']

        logger.debug(f"Validated data - lat: {lat}, lon: {lon}, max_distance: {max_distance}")

        city, distance, address_info = await GlobalLocationService.find_city_for_location(
            lat, lon, max_distance
        )

        logger.debug(f"Found city: {city}, distance: {distance}")

        if city:
            city_data = await sync_to_async(self._prepare_city_response)(city, request)

            response_data = {
                "is_in_city": True,
                "city": city_data,
                "distance_km": round(distance, 2) if distance < float('inf') else None,
                "address_info": address_info,
                "message": f"Koordinatalar {city.title} shahar hududida. Masofa: {distance:.1f} km",
                "match_type": "exact"
            }
        else:
            nearby_cities = await GlobalLocationService.search_cities_by_location(lat, lon, max_distance)

            if nearby_cities:
                nearest_city = nearby_cities[0]
                nearest_city_data = await sync_to_async(self._prepare_city_response)(
                    nearest_city["city"], request
                )

                response_data = {
                    "is_in_city": False,
                    "city": nearest_city_data,
                    "distance_km": round(nearest_city["distance_km"], 2),
                    "address_info": address_info,
                    "message": f"Koordinatalar hech qanday shahar hududida emas. Eng yaqin shahar: {nearest_city['city'].title} ({nearest_city['distance_km']:.1f} km)",
                    "match_type": "nearest"
                }
            else:
                response_data = {
                    "is_in_city": False,
                    "address_info": address_info,
                    "message": "Koordinatalar hech qanday shahar hududida emas va yaqin shaharlar topilmadi",
                    "match_type": "none"
                }

        logger.debug(f"Response data: {response_data}")
        response_serializer = LocationCheckResponseSerializer(response_data)
        return Response(response_serializer.data)

    @action(detail=False, methods=['post'], url_path='validate-city-location')
    def validate_city_location(self, request):
        """Sync wrapper for async validate_city_location"""
        return async_to_sync(self._async_validate_city_location)(request)

    async def _async_validate_city_location(self, request):
        """Validate if city name matches coordinates"""
        serializer = CityValidationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        city_name = serializer.validated_data['city_name']
        lat = serializer.validated_data['latitude']
        lon = serializer.validated_data['longitude']

        validation_result = await GlobalLocationService.validate_city_location(city_name, lat, lon)

        response_serializer = CityValidationResponseSerializer(validation_result)
        return Response(response_serializer.data)

    @action(detail=False, methods=['post'], url_path='nearby-cities')
    def nearby_cities(self, request):
        """Sync wrapper for async nearby_cities"""
        return async_to_sync(self._async_nearby_cities)(request)

    async def _async_nearby_cities(self, request):
        """Find cities near given location"""
        serializer = LocationCheckSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        lat = serializer.validated_data['latitude']
        lon = serializer.validated_data['longitude']
        max_distance = serializer.validated_data['max_distance_km']

        nearby_cities = await GlobalLocationService.search_cities_by_location(lat, lon, max_distance)

        results = []
        for city_data in nearby_cities:
            city_response_data = await sync_to_async(self._prepare_city_response)(
                city_data["city"], request
            )

            results.append({
                "city": city_response_data,
                "distance_km": round(city_data["distance_km"], 2),
                "coordinates": city_data.get("coordinates"),
                "match_type": city_data["match_type"]
            })

        response_serializer = NearbyCitiesResponseSerializer(results, many=True)
        return Response(response_serializer.data)

    @action(detail=True, methods=['get'], url_path='location-info')
    def get_city_location_info(self, request, pk=None):
        """Sync wrapper for async get_city_location_info"""
        return async_to_sync(self._async_get_city_location_info)(request, pk)

    async def _async_get_city_location_info(self, request, pk=None):
        """Get location information for a city"""
        city = await sync_to_async(self.get_object)()

        city_coords = await GlobalLocationService.get_city_coordinates(city.title)
        if not city_coords:
            return Response({
                "error": "Shahar uchun lokatsiya ma'lumotlari topilmadi"
            }, status=status.HTTP_404_NOT_FOUND)

        from ..utils.nominatim_utils import aget_place_from_coords
        address_info = await aget_place_from_coords(city_coords[0], city_coords[1])

        city_data = await sync_to_async(self._prepare_city_response)(city, request)

        return Response({
            "city": city_data,
            "coordinates": {
                "latitude": city_coords[0],
                "longitude": city_coords[1]
            },
            "address_info": address_info
        })

    @action(detail=False, methods=['get'], url_path='search-by-name')
    def search_cities_by_name(self, request):
        """Sync wrapper for async search_cities_by_name"""
        return async_to_sync(self._async_search_cities_by_name)(request)

    async def _async_search_cities_by_name(self, request):
        """Search cities by name and get coordinates"""
        city_name = request.query_params.get('name')
        if not city_name:
            return Response({
                "error": "name parametri talab qilinadi"
            }, status=status.HTTP_400_BAD_REQUEST)

        @sync_to_async
        def get_cities():
            return list(City.objects.filter(
                Q(title__icontains=city_name) | Q(title__iexact=city_name),
                is_allowed=True
            ).prefetch_related(
                Prefetch('cityprice', queryset=CityPrice.objects.only('economy', 'comfort', 'standard'))
            ))

        cities = await get_cities()

        results = []
        for city in cities:
            city_coords = await GlobalLocationService.get_city_coordinates(city.title)

            city_data = await sync_to_async(self._prepare_city_response)(city, request)

            results.append({
                "city": city_data,
                "coordinates": {
                    "latitude": city_coords[0],
                    "longitude": city_coords[1]
                } if city_coords else None,
                "has_coordinates": city_coords is not None
            })

        return Response(results)