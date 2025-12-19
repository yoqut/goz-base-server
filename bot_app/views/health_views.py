from datetime import datetime

from django.http import JsonResponse
from django.views import View
import logging

logger = logging.getLogger(__name__)


class HealthView(View):
    """Simple health check endpoint"""

    def get(self, request):
        logger.info("Health check requested")
        return JsonResponse({
            "status": "healthy",
            "service": "event-backend",
            "timestamp": datetime.now().isoformat()
        })