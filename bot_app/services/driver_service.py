
from ..models import PassengerTravel, PassengerPost, Order, TravelStatus
from ..serializers.order import OrderSerializer
from ..services.base import BaseService
class DriverService(BaseService):

    def notify(self, order_id: int):
        order = Order.objects.get(id=order_id)

        return self._request(
                "POST",
                "driver",
                json=OrderSerializer(order).data)




