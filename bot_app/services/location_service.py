# services/location_service.py
import math
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from asgiref.sync import sync_to_async
from ..models import City
from ..utils.nominatim_utils import aget_coords_from_place, aget_place_from_coords
from django.core.cache import cache


class GlobalLocationService:
    # Cache time in seconds
    COORDINATES_CACHE_TIME = 3600  # 1 hour
    PLACE_CACHE_TIME = 1800  # 30 minutes

    @staticmethod
    def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Haversine formula bilan masofani hisoblash (km)"""
        R = 6371  # Earth radius in kilometers

        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)

        a = (math.sin(delta_lat / 2) ** 2 +
             math.cos(lat1_rad) * math.cos(lat2_rad) *
             math.sin(delta_lon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c

    @staticmethod
    async def get_city_coordinates(city_name: str = "", country: str = "uz") -> Optional[Tuple[float, float]]:
        """Shahar nomi bo'yicha koordinatalarni Nominatim orqali olish (cached)"""
        cache_key = f"city_coords_{city_name.lower()}_{country}"

        # Cache dan tekshirish
        cached_coords = cache.get(cache_key)
        if cached_coords:
            return cached_coords

        try:
            results = await aget_coords_from_place(city_name, country_code=country, limit=1)
            if results and results[0].get('lat') and results[0].get('lon'):
                coords = (float(results[0]['lat']), float(results[0]['lon']))
                # Cache ga saqlash
                cache.set(cache_key, coords, GlobalLocationService.COORDINATES_CACHE_TIME)
                return coords
        except Exception:
            pass

        return None

    @staticmethod
    async def get_place_info(lat: float, lon: float) -> Dict[str, Any]:
        """Koordinatalar bo'yicha joy ma'lumotlarini olish (cached)"""
        cache_key = f"place_info_{lat:.4f}_{lon:.4f}"

        # Cache dan tekshirish
        cached_info = cache.get(cache_key)
        if cached_info:
            return cached_info

        try:
            address_info = await aget_place_from_coords(lat, lon)
            # Cache ga saqlash
            cache.set(cache_key, address_info, GlobalLocationService.PLACE_CACHE_TIME)
            return address_info
        except Exception:
            return {}

    @staticmethod
    async def is_location_in_city_area(
            lat: float,
            lon: float,
            city: City,
            max_distance_km: float = 20.0
    ) -> Tuple[bool, float, Dict[str, Any], Dict[str, Any]]:
        """
        Koordinata shahar hududida ekanligini tekshirish (optimized)
        """
        # Parallel ravishda ma'lumotlarni olish
        city_coords_task = GlobalLocationService.get_city_coordinates(city.title)
        address_info_task = GlobalLocationService.get_place_info(lat, lon)

        city_coords, address_info = await asyncio.gather(city_coords_task, address_info_task)

        if not city_coords:
            return False, 0, address_info, {}

        city_lat, city_lon = city_coords
        distance = GlobalLocationService.calculate_distance(lat, lon, city_lat, city_lon)

        # Shahar ma'lumotlarini olish (faqat kerak bo'lsa)
        if distance <= max_distance_km * 2:  # Optimizatsiya: faqat yaqin bo'lsa olish
            city_address_info = await GlobalLocationService.get_place_info(city_lat, city_lon)
        else:
            city_address_info = {}

        # Hududni tekshirish
        is_in_city = (
                distance <= max_distance_km and
                address_info.get('shahar_tuman') == city_address_info.get('shahar_tuman')
        )

        return is_in_city, distance, address_info, city_address_info

    @staticmethod
    async def find_city_for_location(
            lat: float,
            lon: float,
            max_distance_km: float = 50.0
    ) -> Tuple[Optional[City], float, Dict[str, Any]]:
        """
        Koordinata uchun mos shaharni topish (optimized)
        """
        # Joy ma'lumotlarini olish
        address_info = await GlobalLocationService.get_place_info(lat, lon)
        location_city_name = address_info.get('shahar_tuman', "")

        if not location_city_name:
            return None, 0, address_info

        # Barcha ruxsat etilgan shaharlarni bir martta olish
        @sync_to_async
        def get_allowed_cities():
            return list(City.objects.filter(is_allowed=True))

        cities = await get_allowed_cities()

        # Shahar koordinatalarini parallel olish
        cities_with_coords = []
        for city in cities:
            city_coords = await GlobalLocationService.get_city_coordinates(city.title)
            if city_coords:
                cities_with_coords.append((city, city_coords))

        best_match = None
        min_distance = float('inf')
        location_city_name_lower = location_city_name.lower()

        for city, city_coords in cities_with_coords:
            # Nomlar mos kelishini tekshirish (tezroq)
            city_title_lower = city.title.lower()

            # Nom mos kelishini tekshirish
            name_match = (city_title_lower in location_city_name_lower or
                          location_city_name_lower in city_title_lower)

            if name_match:
                distance = GlobalLocationService.calculate_distance(
                    lat, lon, city_coords[0], city_coords[1]
                )

                if distance <= max_distance_km and distance < min_distance:
                    min_distance = distance
                    best_match = city
                    # Agar juda yaqin bo'lsa, keyingilarini tekshirishni to'xtatish
                    if distance < 1.0:  # 1 km dan kam
                        break

        return best_match, min_distance, address_info

    @staticmethod
    async def validate_city_location(
            city_name: str,
            lat: float,
            lon: float,
            max_distance_km: float = 20.0
    ) -> Dict[str, Any]:
        """
        Shahar nomi va koordinatalar mos kelishini tekshirish (optimized)
        """
        # Parallel ravishda ma'lumotlarni olish
        city_coords_task = GlobalLocationService.get_city_coordinates(city_name)
        user_address_task = GlobalLocationService.get_place_info(lat, lon)

        city_coords, user_address = await asyncio.gather(city_coords_task, user_address_task)

        if not city_coords:
            return {
                "valid": False,
                "error": f"{city_name} shahri uchun koordinatalar topilmadi",
                "distance_km": None
            }

        # Masofani hisoblash
        distance = GlobalLocationService.calculate_distance(lat, lon, city_coords[0], city_coords[1])

        # Faqat kerak bo'lganda shahar ma'lumotlarini olish
        city_address = {}
        if distance <= max_distance_km * 1.5:  # Optimizatsiya
            city_address = await GlobalLocationService.get_place_info(city_coords[0], city_coords[1])

        is_valid = distance <= max_distance_km

        return {
            "valid": is_valid,
            "distance_km": round(distance, 2),
            "max_distance_km": max_distance_km,
            "city_coordinates": {"latitude": city_coords[0], "longitude": city_coords[1]},
            "user_location": {"latitude": lat, "longitude": lon, **user_address},
            "city_location": {"latitude": city_coords[0], "longitude": city_coords[1], **city_address},
            "message": f"Koordinatalar {city_name} shahar hududida {'bor' if is_valid else 'yoq'}. Masofa: {distance:.1f} km"
        }

    @staticmethod
    async def search_cities_by_location(
            lat: float,
            lon: float,
            max_distance_km: float = 50.0
    ) -> List[Dict[str, Any]]:
        """
        Berilgan lokatsiya atrofidagi shaharlarni topish (optimized)
        """
        # Joy ma'lumotlarini olish
        address_info = await GlobalLocationService.get_place_info(lat, lon)
        location_city_name = address_info.get('shahar_tuman', '')

        # Barcha ruxsat etilgan shaharlarni olish
        @sync_to_async
        def get_allowed_cities():
            return list(City.objects.filter(is_allowed=True))

        cities = await get_allowed_cities()

        # Parallel ravishda koordinatalarni olish
        city_coords_tasks = [GlobalLocationService.get_city_coordinates(city.title) for city in cities]
        cities_coords = await asyncio.gather(*city_coords_tasks)

        results = []
        location_city_name_lower = location_city_name.lower()

        for city, city_coords in zip(cities, cities_coords):
            if not city_coords:
                continue

            distance = GlobalLocationService.calculate_distance(
                lat, lon, city_coords[0], city_coords[1]
            )

            if distance <= max_distance_km:
                match_type = "distance"

                # Nom bo'yicha tekshirish
                if location_city_name:
                    city_title_lower = city.title.lower()
                    if (city_title_lower in location_city_name_lower or
                            location_city_name_lower in city_title_lower):
                        match_type = "name"

                results.append({
                    "city": city,
                    "distance_km": round(distance, 2),
                    "coordinates": {"latitude": city_coords[0], "longitude": city_coords[1]},
                    "match_type": match_type
                })

        # Masofa bo'yicha saralash
        results.sort(key=lambda x: x["distance_km"])

        # Faqat eng yaqin 10 ta shaharni qaytarish (agar ko'p bo'lsa)
        if len(results) > 10:
            results = results[:10]

        return results

    @staticmethod
    async def batch_get_city_coordinates(city_names: List[str]) -> Dict[str, Optional[Tuple[float, float]]]:
        """Bir nechta shaharlar uchun koordinatalarni bir vaqtda olish"""
        tasks = [GlobalLocationService.get_city_coordinates(name) for name in city_names]
        coordinates = await asyncio.gather(*tasks)
        return dict(zip(city_names, coordinates))

