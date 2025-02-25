# users/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    User, Location, Property, Booking, Payment, Review, Message, PropertyMedia,
    Notification, BookingInquiry, Room, Amenity, PropertyAmenity, Favorite, Manager
)

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'name', 'email', 'role', 'phone_number', 'is_staff')
    search_fields = ('username', 'name', 'email', 'phone_number')
    list_filter = ('role', 'is_staff')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('name', 'email', 'phone_number', 'date_of_birth', 'gender', 'profile_picture')}),
        ('Permissions', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'name', 'phone_number', 'password1', 'password2', 'role'),
        }),
    )

@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ('property_name', 'owner', 'rental_type', 'availability_status')
    list_filter = ('rental_type', 'availability_status')
    search_fields = ('property_name',)

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('room_number', 'property', 'floor_number', 'price_per_night', 'available')
    list_filter = ('available',)
    search_fields = ('room_number',)

admin.site.register(Location)
admin.site.register(Booking)
admin.site.register(Payment)
admin.site.register(Review)
admin.site.register(Message)
admin.site.register(PropertyMedia)
admin.site.register(Notification)
admin.site.register(BookingInquiry)
admin.site.register(Amenity)
admin.site.register(PropertyAmenity)
admin.site.register(Favorite)
admin.site.register(Manager)