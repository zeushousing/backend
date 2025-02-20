# from rest_framework import generics
# from .models import User  # Importing the correct model
# from .serializers import UserSerializer

# class UserListCreate(generics.ListCreateAPIView):
#     queryset = User.objects.all()  # Using the correct model
#     serializer_class = UserSerializer
# from rest_framework import viewsets
# from .models import User  # Make sure you're using the correct model
# from .serializers import UserSerializer

# class UserViewSet(viewsets.ModelViewSet):
#     queryset = User.objects.all()
#     serializer_class = UserSerializer
# users/views.py
from rest_framework import viewsets
from .models import (
    User, Location, Property, RentalAgreement, Payment,
    Review, Message, PropertyImage, Notification, BookingInquiry
)
from .serializers import (
    UserSerializer, LocationSerializer, PropertySerializer, RentalAgreementSerializer,
    PaymentSerializer, ReviewSerializer, MessageSerializer, PropertyImageSerializer,
    NotificationSerializer, BookingInquirySerializer
)

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

class LocationViewSet(viewsets.ModelViewSet):
    queryset = Location.objects.all()
    serializer_class = LocationSerializer

class PropertyViewSet(viewsets.ModelViewSet):
    queryset = Property.objects.all()
    serializer_class = PropertySerializer

class RentalAgreementViewSet(viewsets.ModelViewSet):
    queryset = RentalAgreement.objects.all()
    serializer_class = RentalAgreementSerializer

class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer

class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer

class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer

class PropertyImageViewSet(viewsets.ModelViewSet):
    queryset = PropertyImage.objects.all()
    serializer_class = PropertyImageSerializer

class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer

class BookingInquiryViewSet(viewsets.ModelViewSet):
    queryset = BookingInquiry.objects.all()
    serializer_class = BookingInquirySerializer
