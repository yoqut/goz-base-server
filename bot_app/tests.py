from django.core.exceptions import ValidationError
from django.test import TestCase
from .models import Order, Driver


class OrderDriverAssignmentTest(TestCase):
    def setUp(self):
        self.driver1 = Driver.objects.create(telegram_id=1, from_location='qoqon', to_location='tashkent')
        self.driver2 = Driver.objects.create(telegram_id=2, from_location='qoqon', to_location='tashkent')
        self.order = Order.objects.create(user=123)

    def test_initial_driver_assignment(self):
        """Birinchi marta driver biriktirish"""
        self.order.driver = self.driver1
        self.order.save()
        self.assertEqual(self.order.driver, self.driver1)

    def test_prevent_driver_reassignment(self):
        """Driver o'zgartirishga yo'l qo'ymaslik"""
        self.order.driver = self.driver1
        self.order.save()

        # Driver o'zgartirishga urinish
        self.order.driver = self.driver2
        with self.assertRaises(ValidationError):
            self.order.save()

        # Order hali ham eski driverga biriktirilgan bo'lishi kerak
        refreshed_order = Order.objects.get(pk=self.order.pk)
        self.assertEqual(refreshed_order.driver, self.driver1)