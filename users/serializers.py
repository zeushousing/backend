from rest_framework import serializers
from .models import (
    User, Location, Property, Booking, Payment, Review, Message, PropertyMedia,
    Notification, BookingInquiry, Room, Amenity, PropertyAmenity, Favorite, Manager,
    MaintenanceRequest, SupportTicket
)

class UserSerializer(serializers.ModelSerializer):
    profile_picture = serializers.ImageField(required=False)
    profile_picture_url = serializers.SerializerMethodField()

    def get_profile_picture_url(self, obj):
        request = self.context.get('request')
        return request.build_absolute_uri(obj.profile_picture.url) if obj.profile_picture else None

    def validate_phone_number(self, value):
        import re
        if not re.match(r'^(?:\+255[6-7]\d{8}|0[6-7]\d{8})$', value):
            raise serializers.ValidationError('Phone number must start with +255 or 0, followed by 6 or 7, then 8 digits.')
        return value

    def validate_profile_picture(self, value):
        if value:
            ext = value.name.split('.')[-1].lower()
            allowed_types = ['jpg', 'jpeg', 'png', 'gif']
            if ext not in allowed_types:
                raise serializers.ValidationError("Only JPG, JPEG, PNG, and GIF image files are allowed.")
        return value

    def validate_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long.")
        if not any(char.isdigit() for char in value):
            raise serializers.ValidationError("Password must contain at least one digit.")
        if not any(char.isupper() for char in value):
            raise serializers.ValidationError("Password must contain at least one uppercase letter.")
        return value

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)

    def update(self, instance, validated_data):
        if 'password' in validated_data:
            instance.set_password(validated_data.pop('password'))
        return super().update(instance, validated_data)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'name', 'email', 'phone_number', 'date_of_birth', 'gender',
            'profile_picture', 'profile_picture_url', 'role', 'password', 'fcm_token'
        ]
        extra_kwargs = {
            'profile_picture': {'required': False},
            'password': {'write_only': True},
            'fcm_token': {'required': False}  # Optional for FCM token
        }

class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ['id', 'address', 'city', 'region', 'country', 'latitude', 'longitude', 'postal_code']

class PropertyMediaSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()

    def get_file_url(self, obj):
        request = self.context.get('request')
        return request.build_absolute_uri(obj.file.url) if obj.file else None

    class Meta:
        model = PropertyMedia
        fields = ['id', 'property', 'file', 'file_url', 'media_type', 'uploaded_at']

class PropertySerializer(serializers.ModelSerializer):
    location = LocationSerializer(read_only=True)
    owner = UserSerializer(read_only=True)
    media = PropertyMediaSerializer(many=True, read_only=True)
    distance = serializers.FloatField(read_only=True)

    class Meta:
        model = Property
        fields = [
            'id', 'owner', 'location', 'property_name', 'property_type', 'rental_type',
            'price_per_night', 'price_per_month', 'availability_status', 'media', 'distance',
            'is_multi_room', 'number_of_bedrooms', 'number_of_bathrooms', 'square_footage', 'description'
        ]

    def validate(self, data):
        if data['rental_type'] == 'short-term' and not data.get('price_per_night'):
            raise serializers.ValidationError("Price per night is required for short-term rentals.")
        elif data['rental_type'] == 'long-term' and not data.get('price_per_month'):
            raise serializers.ValidationError("Price per month is required for long-term rentals.")
        return data

class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = ['id', 'property', 'room_number', 'floor_number', 'price_per_night', 'available']

class BookingSerializer(serializers.ModelSerializer):
    duration = serializers.SerializerMethodField()
    property = PropertySerializer(read_only=True)

    def get_duration(self, obj):
        return (obj.end_date - obj.start_date).days

    class Meta:
        model = Booking
        fields = '__all__'

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['id', 'booking', 'amount', 'payment_date', 'payment_method', 'payment_status', 'stripe_payment_intent_id']

class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = '__all__'

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = '__all__'

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'user', 'notification_type', 'message', 'sent_at', 'read_status']
        extra_kwargs = {'user': {'read_only': True}}  # User set by view, not request

class BookingInquirySerializer(serializers.ModelSerializer):
    class Meta:
        model = BookingInquiry
        fields = '__all__'

class MaintenanceRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = MaintenanceRequest
        fields = '__all__'

class AmenitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Amenity
        fields = '__all__'

class PropertyAmenitySerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyAmenity
        fields = '__all__'

class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = '__all__'

class ManagerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Manager
        fields = '__all__'

class SupportTicketSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    class Meta:
        model = SupportTicket
        fields = ['id', 'user', 'subject', 'description', 'status', 'created_at', 'updated_at']