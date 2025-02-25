from django.views.decorators.cache import cache_page
from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from django.db.models import F, FloatField
from django.db.models.functions import Sin, Cos, Radians, Sqrt, ACos
from math import radians
from .models import (
    User, Location, Property, Booking, Payment, Review, Message, PropertyMedia,
    Notification, BookingInquiry, Room, Amenity, PropertyAmenity, Favorite, Manager,
    MaintenanceRequest, SupportTicket
)
from .serializers import (
    UserSerializer, LocationSerializer, PropertySerializer, BookingSerializer,
    PaymentSerializer, ReviewSerializer, MessageSerializer, PropertyMediaSerializer,
    NotificationSerializer, BookingInquirySerializer, RoomSerializer,
    AmenitySerializer, PropertyAmenitySerializer, FavoriteSerializer, ManagerSerializer,
    MaintenanceRequestSerializer, SupportTicketSerializer
)
from .chatbot import handle_chatbot_request

class IsAdmin(IsAuthenticated):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.role == 'admin'

class IsLandlordOrManager(IsAuthenticated):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.role in ['landlord', 'hotel_manager']

class IsTenant(IsAuthenticated):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.role == 'tenant'

class StandardPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [IsAdmin]
    pagination_class = StandardPagination

    def get_queryset(self):
        if self.request.user.role == 'admin':
            return User.objects.all()
        return User.get_active()

    def get_serializer_context(self):
        return {'request': self.request}

    @action(detail=True, methods=['patch'], permission_classes=[IsAuthenticated])
    def update_profile(self, request, pk=None):
        user = self.get_object()
        if user != request.user and not request.user.is_admin:
            return Response({'error': 'Permission denied'}, status=403)
        serializer = UserSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    @action(detail=True, methods=['patch'], permission_classes=[IsAuthenticated])
    def update_settings(self, request, pk=None):
        user = self.get_object()
        if user != request.user:
            return Response({'error': 'Permission denied'}, status=403)
        serializer = UserSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            if 'email' in request.data:
                user.email = request.data['email']
            if 'password' in request.data:
                user.set_password(request.data['password'])
            user.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def register(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def chat(self, request):
        message = request.data.get('message')
        if not message:
            return Response({'error': 'Message required'}, status=400)
        response = handle_chatbot_request(request.user, message)
        return Response({'response': response})

class LocationViewSet(viewsets.ModelViewSet):
    serializer_class = LocationSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination

    def get_queryset(self):
        if self.request.user.role == 'admin':
            return Location.objects.all()
        if self.request.user.role in ['landlord', 'hotel_manager']:
            return Location.objects.filter(property__owner=self.request.user).distinct()
        return Location.objects.filter(property__bookings__user=self.request.user).distinct()

class PropertyViewSet(viewsets.ModelViewSet):
    serializer_class = PropertySerializer
    permission_classes = [IsLandlordOrManager]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['property_type', 'rental_type', 'availability_status', 'location__city']
    search_fields = ['property_name', 'description']
    pagination_class = StandardPagination

    @cache_page(60 * 15)
    def get_queryset(self):
        if self.request.user.role == 'admin':
            return Property.objects.all()
        return Property.get_active().filter(owner=self.request.user).select_related('location', 'owner').prefetch_related('media')

    def get_serializer_context(self):
        return {'request': self.request}

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def nearby(self, request):
        try:
            user_lat = float(request.query_params.get('latitude'))
            user_lon = float(request.query_params.get('longitude'))
            radius_km = float(request.query_params.get('radius', 10))
            property_type = request.query_params.get('property_type')
            rental_type = request.query_params.get('rental_type')
            availability_status = request.query_params.get('availability_status')
            sort_by = request.query_params.get('sort_by', 'distance')

            queryset = Property.get_active().filter(
                location__latitude__isnull=False,
                location__longitude__isnull=False
            )

            if property_type:
                queryset = queryset.filter(property_type=property_type)
            if rental_type:
                queryset = queryset.filter(rental_type=rental_type)
            if availability_status:
                queryset = queryset.filter(availability_status=availability_status)

            queryset = queryset.annotate(
                distance=6371 * ACos(
                    Cos(Radians(user_lat)) * Cos(Radians(F('location__latitude'))) *
                    Cos(Radians(F('location__longitude')) - Radians(user_lon)) +
                    Sin(Radians(user_lat)) * Sin(Radians(F('location__latitude'))),
                    output_field=FloatField()
                )
            ).filter(distance__lte=radius_km)

            if sort_by == 'price_per_night':
                queryset = queryset.order_by('price_per_night')
            elif sort_by == 'price_per_month':
                queryset = queryset.order_by('price_per_month')
            else:
                queryset = queryset.order_by('distance')

            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        except (ValueError, TypeError):
            return Response({'error': 'Invalid parameters (latitude, longitude, radius, etc.)'}, status=400)

class BookingViewSet(viewsets.ModelViewSet):
    serializer_class = BookingSerializer
    permission_classes = [IsTenant | IsLandlordOrManager]
    pagination_class = StandardPagination

    def get_queryset(self):
        if self.request.user.role == 'admin':
            return Booking.objects.all()
        if self.request.user.role in ['landlord', 'hotel_manager']:
            return Booking.get_active().filter(property__owner=self.request.user).select_related('property', 'user').prefetch_related('room')
        return Booking.get_active().filter(user=self.request.user).select_related('property', 'user').prefetch_related('room')

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        booking = self.get_object()
        new_status = request.data.get('status')
        if new_status:
            booking.status = new_status
            try:
                booking.save()
                return Response({'status': f'Booking updated to {new_status}'})
            except ValidationError as e:
                return Response({'error': str(e)}, status=400)
        return Response({'error': 'Status required'}, status=400)

class PaymentViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination

    def get_queryset(self):
        if self.request.user.role == 'admin':
            return Payment.objects.all()
        if self.request.user.role in ['landlord', 'hotel_manager']:
            return Payment.get_active().filter(booking__property__owner=self.request.user)
        return Payment.get_active().filter(booking__user=self.request.user)

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        payment = self.get_object()
        new_status = request.data.get('payment_status')
        if new_status in [choice[0] for choice in Payment.PAYMENT_STATUS_CHOICES]:
            payment.payment_status = new_status
            payment.save()
            return Response({'status': f'Payment updated to {new_status}'})
        return Response({'error': 'Invalid status'}, status=400)

class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = [IsTenant]
    pagination_class = StandardPagination

    def get_queryset(self):
        if self.request.user.role == 'admin':
            return Review.objects.all()
        if self.request.user.role in ['landlord', 'hotel_manager']:
            return Review.get_active().filter(property__owner=self.request.user)
        return Review.get_active().filter(user=self.request.user)

class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination

    def get_queryset(self):
        if self.request.user.role == 'admin':
            return Message.objects.all()
        return Message.get_active().filter(receiver=self.request.user) | Message.get_active().filter(sender=self.request.user)

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        message = self.get_object()
        message.read_status = 'Read'
        message.save()
        return Response({'status': 'Message marked as read'})

class PropertyMediaViewSet(viewsets.ModelViewSet):
    serializer_class = PropertyMediaSerializer
    permission_classes = [IsLandlordOrManager]
    pagination_class = StandardPagination

    def get_queryset(self):
        if self.request.user.role == 'admin':
            return PropertyMedia.objects.all()
        return PropertyMedia.objects.filter(property__owner=self.request.user)

    def get_serializer_context(self):
        return {'request': self.request}

class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination

    def get_queryset(self):
        if self.request.user.role == 'admin':
            return Notification.objects.all()
        queryset = Notification.get_active().filter(user=self.request.user)
        read_status = self.request.query_params.get('read_status', None)
        if read_status:
            queryset = queryset.filter(read_status=read_status)
        return queryset

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        self.get_queryset().update(read_status='Read')
        return Response({'status': 'All notifications marked as read'})

class BookingInquiryViewSet(viewsets.ModelViewSet):
    serializer_class = BookingInquirySerializer
    permission_classes = [IsTenant | IsLandlordOrManager]
    pagination_class = StandardPagination

    def get_queryset(self):
        if self.request.user.role == 'admin':
            return BookingInquiry.objects.all()
        if self.request.user.role in ['landlord', 'hotel_manager']:
            return BookingInquiry.get_active().filter(property__owner=self.request.user)
        return BookingInquiry.get_active().filter(user=self.request.user)

class MaintenanceRequestViewSet(viewsets.ModelViewSet):
    serializer_class = MaintenanceRequestSerializer
    permission_classes = [IsTenant | IsLandlordOrManager]
    pagination_class = StandardPagination

    def get_queryset(self):
        if self.request.user.role == 'admin':
            return MaintenanceRequest.objects.all()
        if self.request.user.role in ['landlord', 'hotel_manager']:
            return MaintenanceRequest.get_active().filter(property__owner=self.request.user)
        return MaintenanceRequest.get_active().filter(user=self.request.user)

class RoomViewSet(viewsets.ModelViewSet):
    serializer_class = RoomSerializer
    permission_classes = [IsLandlordOrManager]
    pagination_class = StandardPagination

    def get_queryset(self):
        if self.request.user.role == 'admin':
            return Room.objects.all()
        return Room.objects.filter(property__owner=self.request.user)

class AmenityViewSet(viewsets.ModelViewSet):
    serializer_class = AmenitySerializer
    permission_classes = [IsLandlordOrManager]
    pagination_class = StandardPagination

    def get_queryset(self):
        if self.request.user.role == 'admin':
            return Amenity.objects.all()
        return Amenity.objects.all()

class PropertyAmenityViewSet(viewsets.ModelViewSet):
    serializer_class = PropertyAmenitySerializer
    permission_classes = [IsLandlordOrManager]
    pagination_class = StandardPagination

    def get_queryset(self):
        if self.request.user.role == 'admin':
            return PropertyAmenity.objects.all()
        return PropertyAmenity.objects.filter(property__owner=self.request.user)

class FavoriteViewSet(viewsets.ModelViewSet):
    serializer_class = FavoriteSerializer
    permission_classes = [IsTenant]
    pagination_class = StandardPagination

    def get_queryset(self):
        if self.request.user.role == 'admin':
            return Favorite.objects.all()
        return Favorite.objects.filter(user=self.request.user)

class ManagerViewSet(viewsets.ModelViewSet):
    serializer_class = ManagerSerializer
    permission_classes = [IsLandlordOrManager]
    pagination_class = StandardPagination

    def get_queryset(self):
        if self.request.user.role == 'admin':
            return Manager.objects.all()
        return Manager.objects.filter(property__owner=self.request.user)

class SupportTicketViewSet(viewsets.ModelViewSet):
    serializer_class = SupportTicketSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination

    def get_queryset(self):
        if self.request.user.role == 'admin':
            return SupportTicket.objects.all()
        return SupportTicket.get_active().filter(user=self.request.user)

    def perform_create(self, serializer):
        ticket = serializer.save(user=self.request.user)
        admin = User.objects.filter(role='admin').first()
        if admin:
            Notification.objects.create(
                user=admin,
                notification_type='Support',
                message=f"New support ticket #{ticket.id} from {self.request.user.username}"
            )

    @action(detail=True, methods=['post'], permission_classes=[IsAdmin])
    def update_status(self, request, pk=None):
        ticket = self.get_object()
        new_status = request.data.get('status')
        if new_status in [choice[0] for choice in SupportTicket.STATUS_CHOICES]:
            ticket.status = new_status
            ticket.save()
            Notification.objects.create(
                user=ticket.user,
                notification_type='Support',
                message=f"Your ticket #{ticket.id} is now {new_status}"
            )
            return Response({'status': f'Ticket updated to {new_status}'})
        return Response({'error': 'Invalid status'}, status=400)