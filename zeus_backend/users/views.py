from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination  # Correct import
from .models import (
    User, Location, Property, Booking, Payment, Review, Message, PropertyMedia,
    Notification, BookingInquiry, Room, Amenity, PropertyAmenity, Favorite, Manager
)
from .serializers import (
    UserSerializer, LocationSerializer, PropertySerializer, BookingSerializer,
    PaymentSerializer, ReviewSerializer, MessageSerializer, PropertyMediaSerializer,
    NotificationSerializer, BookingInquirySerializer, RoomSerializer,
    AmenitySerializer, PropertyAmenitySerializer, FavoriteSerializer, ManagerSerializer
)

class IsAdmin(IsAuthenticated):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.role == 'admin'

class IsLandlordOrManager(IsAuthenticated):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.role in ['landlord', 'hotel_manager']

class IsTenant(IsAuthenticated):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.role == 'tenant'

class StandardPagination(PageNumberPagination):  # Fixed base class
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [IsAdmin]
    pagination_class = StandardPagination
    def get_queryset(self):
        return User.objects.all()

class LocationViewSet(viewsets.ModelViewSet):
    serializer_class = LocationSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination
    def get_queryset(self):
        if self.request.user.role in ['landlord', 'hotel_manager']:
            return Location.objects.filter(property__owner=self.request.user).distinct()
        return Location.objects.filter(property__bookings__user=self.request.user).distinct()

class PropertyViewSet(viewsets.ModelViewSet):
    serializer_class = PropertySerializer
    permission_classes = [IsLandlordOrManager]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['property_type', 'rental_type', 'availability_status']
    search_fields = ['property_name', 'description']
    pagination_class = StandardPagination

    def get_queryset(self):
        return Property.objects.filter(owner=self.request.user).select_related('location', 'owner').prefetch_related('media')

    def get_serializer_context(self):
        return {'request': self.request}

class BookingViewSet(viewsets.ModelViewSet):
    serializer_class = BookingSerializer
    permission_classes = [IsTenant | IsLandlordOrManager]
    pagination_class = StandardPagination
    def get_queryset(self):
        if self.request.user.role in ['landlord', 'hotel_manager']:
            return Booking.objects.filter(property__owner=self.request.user).select_related('property', 'user').prefetch_related('room')
        return Booking.objects.filter(user=self.request.user).select_related('property', 'user').prefetch_related('room')

    def perform_create(self, serializer):
        property = serializer.validated_data['property']
        start_date = serializer.validated_data['start_date']
        end_date = serializer.validated_data['end_date']
        room = serializer.validated_data.get('room')
        if room:
            overlapping = Booking.objects.filter(
                room=room, start_date__lte=end_date, end_date__gte=start_date, status__in=['Pending', 'Confirmed']
            ).exists()
        else:
            overlapping = Booking.objects.filter(
                property=property, start_date__lte=end_date, end_date__gte=start_date, status__in=['Pending', 'Confirmed']
            ).exists()
        if overlapping:
            raise serializers.ValidationError("Property or room is already booked for these dates.")
        serializer.save(user=self.request.user)

class PaymentViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination
    def get_queryset(self):
        if self.request.user.role in ['landlord', 'hotel_manager']:
            return Payment.objects.filter(booking__property__owner=self.request.user)
        return Payment.objects.filter(booking__user=self.request.user)

class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = [IsTenant]
    pagination_class = StandardPagination
    def get_queryset(self):
        return Review.objects.filter(user=self.request.user)

class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination
    def get_queryset(self):
        return Message.objects.filter(receiver=self.request.user) | Message.objects.filter(sender=self.request.user)

class PropertyMediaViewSet(viewsets.ModelViewSet):
    serializer_class = PropertyMediaSerializer
    permission_classes = [IsLandlordOrManager]
    pagination_class = StandardPagination

    def get_queryset(self):
        return PropertyMedia.objects.filter(property__owner=self.request.user)

    def get_serializer_context(self):
        return {'request': self.request}

class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        self.get_queryset().update(read_status='Read')
        return Response({'status': 'All notifications marked as read'})

class BookingInquiryViewSet(viewsets.ModelViewSet):
    serializer_class = BookingInquirySerializer
    permission_classes = [IsTenant]
    pagination_class = StandardPagination
    def get_queryset(self):
        return BookingInquiry.objects.filter(user=self.request.user)

class RoomViewSet(viewsets.ModelViewSet):
    serializer_class = RoomSerializer
    permission_classes = [IsLandlordOrManager]
    pagination_class = StandardPagination
    def get_queryset(self):
        return Room.objects.filter(property__owner=self.request.user)

class AmenityViewSet(viewsets.ModelViewSet):
    serializer_class = AmenitySerializer
    permission_classes = [IsLandlordOrManager]
    pagination_class = StandardPagination
    def get_queryset(self):
        return Amenity.objects.all()

class PropertyAmenityViewSet(viewsets.ModelViewSet):
    serializer_class = PropertyAmenitySerializer
    permission_classes = [IsLandlordOrManager]
    pagination_class = StandardPagination
    def get_queryset(self):
        return PropertyAmenity.objects.filter(property__owner=self.request.user)

class FavoriteViewSet(viewsets.ModelViewSet):
    serializer_class = FavoriteSerializer
    permission_classes = [IsTenant]
    pagination_class = StandardPagination
    def get_queryset(self):
        return Favorite.objects.filter(user=self.request.user)

class ManagerViewSet(viewsets.ModelViewSet):
    serializer_class = ManagerSerializer
    permission_classes = [IsLandlordOrManager]
    pagination_class = StandardPagination
    def get_queryset(self):
        return Manager.objects.filter(property__owner=self.request.user)