# from django.urls import path, include
# from django.contrib import admin
# from rest_framework.routers import DefaultRouter
# from .views import (
#     UserViewSet, LocationViewSet, PropertyViewSet, RentalAgreementViewSet,
#     PaymentViewSet, ReviewViewSet, MessageViewSet, PropertyImageViewSet,
#     NotificationViewSet, BookingInquiryViewSet
# )

# # Create a router and register viewsets
# router = DefaultRouter()
# router.register(r'users', UserViewSet)
# router.register(r'locations', LocationViewSet)
# router.register(r'properties', PropertyViewSet)
# router.register(r'rental-agreements', RentalAgreementViewSet)
# router.register(r'payments', PaymentViewSet)
# router.register(r'reviews', ReviewViewSet)
# router.register(r'messages', MessageViewSet)
# router.register(r'property-images', PropertyImageViewSet)
# router.register(r'notifications', NotificationViewSet)
# router.register(r'booking-inquiries', BookingInquiryViewSet)

# # Define the API URL patterns
# urlpatterns = [
#     path('admin/', admin.site.urls),
#     path('api/', include(router.urls)),
# ]

# from django.urls import path, include

# urlpatterns = [
#     path('admin/', admin.site.urls),
#     path('', include('core.urls')),  # Include your app's API URLs
# ]
from django.urls import path, include  # Add this import at the top
from rest_framework.routers import DefaultRouter
from django.http import HttpResponse
from django.contrib import admin
from .views import (
    UserViewSet, LocationViewSet, PropertyViewSet, RentalAgreementViewSet,
    PaymentViewSet, ReviewViewSet, MessageViewSet, PropertyImageViewSet,
    NotificationViewSet, BookingInquiryViewSet
)

# Simple root view
def api_root(request):
    return HttpResponse("Welcome to Zeus API! Append '/api/' to access endpoints.")

# Create a router and register viewsets
router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'locations', LocationViewSet)
router.register(r'properties', PropertyViewSet)
router.register(r'rental-agreements', RentalAgreementViewSet)
router.register(r'payments', PaymentViewSet)
router.register(r'reviews', ReviewViewSet)
router.register(r'messages', MessageViewSet)
router.register(r'property-images', PropertyImageViewSet)
router.register(r'notifications', NotificationViewSet)
router.register(r'booking-inquiries', BookingInquiryViewSet)

urlpatterns = [
    path('', include(router.urls)),  # API endpoints remain at /api/
]