# tasks/travel_tasks.py
from celery import shared_task
from ..services.driver_service import DriverService
from ..services.passenger_service import PassengerService


@shared_task
def notify_driver_bot(order_id):
    try:
        driver_service = DriverService()
        driver_service.notify(order_id)
    except Exception as e:
        print(e)


@shared_task
def notify_passenger_bot(order_id):
    try:
        passenger_service = PassengerService()
        passenger_service.notify(order_id)

    except Exception as e:
        print(e)
