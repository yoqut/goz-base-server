
from typing import Optional

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from pydantic import BaseModel

class BotClient(models.Model):
    telegram_id = models.BigIntegerField(unique=True)
    username = models.CharField(max_length=200, null=True, blank=True)
    full_name = models.CharField(max_length=200)
    language = models.CharField(max_length=50, default="uz")
    is_banned = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.full_name

    class Meta:
        verbose_name_plural = "Bot foydalanuvchilari"
        verbose_name = "Bot foydalanuvchisi"


class Passenger(models.Model):
    telegram_id = models.BigIntegerField(unique=True)
    full_name = models.CharField(max_length=200)
    total_rides = models.IntegerField(default=0)
    phone = models.CharField(max_length=50, unique=True, null=True, blank=True)
    rating = models.IntegerField(default=5)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.full_name

    class Meta:
        ordering = ['-rating']
        verbose_name_plural = "Yo'lovchilar"
        verbose_name = "Yo'lovchi"


class TravelClass(models.TextChoices):
    ECONOMY = "economy", "Economy"
    STANDARD = "standard", "Standard"
    COMFORT = "comfort", "Comfort"


class TravelStatus(models.TextChoices):
    CREATED = "created", "Created"
    ASSIGNED = "assigned", "Assigned"
    ARRIVED = "arrived", "Arrived"
    STARTED = "started", "Started"
    ENDED = "ended", "Ended"
    REJECTED = "rejected", "Rejected"


class Coordinate(BaseModel):
    longitude: float  # Changed to float, coordinates are typically floats
    latitude: float


class Location(BaseModel):
    city: str = ""
    location: Optional[Coordinate] = None


def default_location():
    return Location().dict()


class Journey(models.Model):
    user = models.BigIntegerField()
    from_location = models.JSONField(default=default_location)
    to_location = models.JSONField(default=default_location)
    price = models.IntegerField(default=0)
    start_time = models.DateTimeField(null=True, blank=True)
    destination = models.TextField(default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class PassengerTravel(Journey):
    travel_class = models.CharField(max_length=200, choices=TravelClass.choices, default=TravelClass.STANDARD)
    passenger = models.IntegerField(default=1)
    has_woman = models.BooleanField(default=False)
    rate = models.IntegerField(default=0)

    def __str__(self):
        return str(self.user)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Sayohatlar"
        verbose_name = "Sayohat"


class PassengerPost(Journey):
    pass

    def __str__(self):
        return f"{self.from_location} -> {self.to_location}"

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Pochtalar"
        verbose_name = "Pochta"


class DriverStatus(models.TextChoices):
    OFFLINE = "offline", "Offline"
    ONLINE = "online", "Online"


class Driver(models.Model):
    telegram_id = models.BigIntegerField(unique=True, null=True, blank=True)
    full_name = models.CharField(max_length=200, default='')
    total_rides = models.IntegerField(default=0)
    phone = models.CharField(max_length=50, unique=True, null=True, blank=True)
    rating = models.IntegerField(default=5)
    from_location = models.ForeignKey(
        "City",
        on_delete=models.CASCADE,
        related_name='drivers_from',  # Add this
        related_query_name='driver_from',  # Optional but recommended
        default=None,  # Use None if you want to allow empty
        null=True,  # Add this if default=None
        blank=True
    )
    to_location = models.ForeignKey(
        "City",
        on_delete=models.CASCADE,
        related_name='drivers_to',  # Add this
        related_query_name='driver_to',  # Optional but recommended
        default=None,  # Use None if you want to allow empty
        null=True,  # Add this if default=None
        blank=True
    )
    status = models.CharField(max_length=10, choices=DriverStatus.choices, default=DriverStatus.OFFLINE)
    amount = models.IntegerField(default=150000)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.phone)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Haydovchilar"
        verbose_name = "Haydovchi"


class DriverGallery(models.Model):
    telegram_id = models.OneToOneField(Driver, on_delete=models.CASCADE)
    profile_image = models.ImageField(null=True, blank=True, upload_to="profile_image/")


class Car(models.Model):
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE, related_name="driver")
    car_number = models.CharField(max_length=200, unique=True)
    car_model = models.CharField(max_length=200)
    car_color = models.CharField(max_length=200)
    car_class = models.CharField(max_length=200, choices=TravelClass.choices, default=TravelClass.ECONOMY)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.car_number)

    class Meta:
        ordering = ['-created_at']



class DriverTransaction(models.Model):
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE)
    amount = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.driver)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Haydovchi pul o'tkazmalari"
        verbose_name = "Haydovchi pul o'tkazmasi"


class City(models.Model):
    title = models.CharField(max_length=200)
    subcategory = models.ForeignKey("self", on_delete=models.SET_NULL, null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    translate = models.JSONField(null=True, blank=True)
    is_allowed = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Shaharlar"
        verbose_name = "Shahar"


class CityPrice(models.Model):
    city = models.OneToOneField(City, on_delete=models.CASCADE)
    economy = models.DecimalField(decimal_places=2, max_digits=10)
    comfort = models.DecimalField(decimal_places=2, max_digits=10)
    standard = models.DecimalField(decimal_places=2, max_digits=10)
    delivery = models.DecimalField(decimal_places=2, max_digits=10, default=50000)

    def __str__(self):
        return self.city.title

    class Meta:
        verbose_name_plural = "Shahar narxlari"
        verbose_name = "Shahar narxlari"


class OrderType(models.TextChoices):
    TRAVEL = "travel", "Travel"
    DELIVERY = "delivery", "Delivery"


class Order(models.Model):
    user = models.BigIntegerField()
    driver = models.ForeignKey('Driver', on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=10, choices=TravelStatus.choices, default=TravelStatus.CREATED)
    order_type = models.CharField(max_length=200, choices=OrderType.choices, default=OrderType.TRAVEL)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Buyurtmalar"
        verbose_name = "Buyurtma"

    def __str__(self):
        if self.content_object:
            return f"{self.content_type} -> {self.object_id}"
        return f"Order #{self.pk} - User: {self.user}"

    def clean(self):
        super().clean()
        if self.driver and self.pk:
            try:
                old_order = Order.objects.get(pk=self.pk)
                if old_order.driver and old_order.driver != self.driver:

                    print(
                        f"Order {self.pk} driver o'zgartirishga urinish: "
                        f"Eski driver: {old_order.driver.pk}, Yangi driver: {self.driver.pk}"
                    )

                    self.driver = old_order.driver
            except Order.DoesNotExist:
                pass