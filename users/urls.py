from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserViewSet, LocationViewSet, PropertyViewSet, BookingViewSet, PaymentViewSet,
    ReviewViewSet, MessageViewSet, PropertyMediaViewSet, NotificationViewSet,
    BookingInquiryViewSet, RoomViewSet, AmenityViewSet, PropertyAmenityViewSet,
    FavoriteViewSet, ManagerViewSet, MaintenanceRequestViewSet, SupportTicketViewSet
)

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'locations', LocationViewSet, basename='location')
router.register(r'properties', PropertyViewSet, basename='property')
router.register(r'bookings', BookingViewSet, basename='booking')
router.register(r'payments', PaymentViewSet, basename='payment')
router.register(r'reviews', ReviewViewSet, basename='review')
router.register(r'messages', MessageViewSet, basename='message')
router.register(r'property-media', PropertyMediaViewSet, basename='propertymedia')
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'booking-inquiries', BookingInquiryViewSet, basename='bookinginquiry')
router.register(r'maintenance-requests', MaintenanceRequestViewSet, basename='maintenancerequest')
router.register(r'rooms', RoomViewSet, basename='room')
router.register(r'amenities', AmenityViewSet, basename='amenity')
router.register(r'property-amenities', PropertyAmenityViewSet, basename='propertyamenity')
router.register(r'favorites', FavoriteViewSet, basename='favorite')
router.register(r'managers', ManagerViewSet, basename='manager')
router.register(r'support/tickets', SupportTicketViewSet, basename='supportticket')

urlpatterns = [
    path('', include(router.urls)),
    path('api/', include(router.urls))
]
