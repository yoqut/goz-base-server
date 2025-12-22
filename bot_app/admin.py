from django.contrib import admin

from .models import (
    BotClient, PassengerTravel, PassengerPost,
    Driver, Car, DriverTransaction, City, Order, Passenger, DriverGallery, CityPrice
)

admin.site.site_header = "Taxi Bot Admin"
admin.site.site_title = "Taxi Bot Administration"
admin.site.index_title = "Boshqaruv paneliga xush kelibsiz"

@admin.register(BotClient)
class BotClientAdmin(admin.ModelAdmin):
    list_display = ("id", "new_full_name", "username", "language", "is_banned")
    list_filter = ("is_banned", "language", "created_at")
    search_fields = ("full_name", "username", "telegram_id")
    list_editable = ("is_banned",)
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)

    def new_full_name(self, obj):
        return f"{obj.full_name}({obj.telegram_id})"

@admin.register(PassengerTravel)
class PassengerTravelAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'creator_name',
        'rate',
        'price',
        'created_at'
    ]

    list_filter = ['travel_class', 'has_woman', 'created_at']
    search_fields = ['user', ]
    readonly_fields = ['created_at', 'updated_at']

    def creator_name(self, obj):
        try:
            client = BotClient.objects.get(telegram_id=obj.user)
            return f"{client.full_name}({obj.user})"
        except BotClient.DoesNotExist:
            return obj.user

@admin.register(PassengerPost)
class PassengerPostAdmin(admin.ModelAdmin):
    list_display = ("id", "creator_name", "from_location", "to_location", "price", "created_at")
    list_filter = ("created_at",)
    search_fields = ("from_location", "to_location", "user")
    list_editable = ("price",)
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)

    def creator_name(self, obj):
        try:
            client = BotClient.objects.get(telegram_id=obj.user)
            return f"{client.full_name}({obj.user})"
        except BotClient.DoesNotExist:
            return obj.user


class CarInline(admin.TabularInline):
    model = Car
    extra = 1
    readonly_fields = ("created_at", "updated_at")


class DriverTransactionInline(admin.TabularInline):
    model = DriverTransaction
    extra = 1
    readonly_fields = ("created_at",)

class DriverGalleryInline(admin.StackedInline):
    """DriverGallery modelini Driver adminida inline ko'rinishda ko'rsatish"""
    model = DriverGallery
    can_delete = False
    extra = 0
    max_num = 1


@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ("new_full_name", "car_info", "phone", "status", "locations", "amount",)
    list_filter = ("phone", "status")
    search_fields = ("telegram_id", "phone")
    list_editable = ("amount", "status")
    inlines = [DriverGalleryInline, CarInline, DriverTransactionInline]
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)

    def locations(self, obj):
        return f"{obj.from_location} -> {obj.to_location}"

    locations.short_description = "Yo'nalish"

    def new_full_name(self, obj):
        return f"{obj.full_name}({obj.telegram_id})"

    new_full_name.short_description = "Ism"

    def car_info(self, obj):
        try:
            cars = Car.objects.filter(driver_id=obj.id).first()
            return f"{cars.car_model}({cars.car_number})"
        except Exception as e:
            print(e)
            return ""

    car_info.short_description = "Avtomobil ma'lumotlari"


# CityPrice uchun inline
class CityPriceInline(admin.StackedInline):
    model = CityPrice
    extra = 1
    can_delete = False  # O'chirishni o'chirib qo'yish


# City admini
@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    # Ro'yxat ko'rinishi
    list_display = ['title', 'get_subcategory', 'is_allowed', 'created_at']
    list_filter = ['is_allowed', 'created_at']
    search_fields = ['title']

    # Forma sozlamalari - MUHIM: fields yoki fieldsets bo'lishi kerak
    fields = [
        'title',
        'subcategory',
        'latitude',
        'longitude',
        'translate',
        'is_allowed'
    ]

    # Inline lar
    inlines = [CityPriceInline]

    # Qo'shimcha funksiyalar
    def get_subcategory(self, obj):
        return obj.subcategory.title if obj.subcategory else "-"

    get_subcategory.short_description = "Subkategoriya"


# CityPrice alohida admin (ixtiyoriy)
@admin.register(CityPrice)
class CityPriceAdmin(admin.ModelAdmin):
    list_display = ['city', 'economy', 'comfort', 'standard']
    search_fields = ['city__title']




@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    # Ro'yxatda ko'rsatiladigan maydonlar
    list_display = [
        'id',
        'creator_name',
        'order_type',
        'status',
        'driver',
        'content_type',
        'object_id',
        'created_at'
    ]

    # Filter panel
    list_filter = [
        'user',
        'status',
        'order_type',
        'created_at',
        'driver'
    ]

    # Qidiruv maydonlari
    search_fields = [
        'user',
        'driver__name',
        'driver__phone',

    ]

    # Readonly maydonlar
    readonly_fields = [
        'created_at',
        'updated_at'
    ]

    # Sahifadagi elementlar soni
    list_per_page = 20

    # Sana bo'yicha guruhlash
    date_hierarchy = 'created_at'


    # Actionlar
    actions = ['make_ended', 'make_rejected']

    def make_ended(self, request, queryset):
        """Tanlangan orderlarni completed qilish"""
        updated = queryset.update(status='ended')
        self.message_user(request, f'{updated} ta order completed holatiga o\'zgartirildi')

    make_ended.short_description = "Tanlangan orderlarni completed qilish"

    def make_rejected(self, request, queryset):
        """Tanlangan orderlarni cancelled qilish"""
        updated = queryset.update(status='rejected')
        self.message_user(request, f'{updated} ta order cancelled holatiga o\'zgartirildi')

    make_rejected.short_description = "Tanlangan orderlarni cancelled qilish"

    def creator_name(self, obj):
        try:
            client = BotClient.objects.get(telegram_id=obj.user)
            return f"{client.full_name}({obj.user})"
        except BotClient.DoesNotExist:
            return obj.user

@admin.register(Passenger)
class PassengerAdmin(admin.ModelAdmin):
    # Ro'yxat ko'rinishidagi ustunlar
    list_display = [
        'id',
        'telegram_id',
        'full_name',
        'phone',
        'total_rides',
        'rating',
        'created_at'
    ]

    # Filtrlar
    list_filter = [
        'rating',
        'created_at',
        'updated_at'
    ]

    # Qidiruv maydonlari
    search_fields = [
        'telegram_id',
        'full_name',
        'phone'
    ]

    # Tartiblash
    ordering = ['-rating']

    # Faqat o'qish uchun maydonlar
    readonly_fields = [
        'created_at',
        'updated_at'
    ]

    # Maydonlar guruhlari
    fieldsets = (
        ('Asosiy maʼlumotlar', {
            'fields': (
                'telegram_id',
                'full_name',
                'phone'
            )
        }),
        ('Statistika', {
            'fields': (
                'total_rides',
                'rating'
            )
        }),
        ('Qo\'shimcha maʼlumotlar', {
            'fields': (
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)  # Yig'iladigan blok
        }),
    )

    # Admin panelda ko'rsatiladigan sarlavha
    list_display_links = ['telegram_id', 'full_name']

    # Sahifadagi elementlar soni
    list_per_page = 20

    def get_readonly_fields(self, request, obj=None):
        """Yangi yaratishda telegram_id ni o'zgartirish mumkin, mavjud bo'lsa yo'q"""
        if obj:  # object mavjud bo'lsa (yangilash)
            return ['telegram_id', 'created_at', 'updated_at']
        else:  # yangi yaratish
            return ['created_at', 'updated_at']

