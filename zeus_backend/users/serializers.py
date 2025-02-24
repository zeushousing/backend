from rest_framework import serializers
from .models import (
    User, Location, Property, Booking, Payment, Review, Message, PropertyMedia,
    Notification, BookingInquiry, Room, Amenity, PropertyAmenity, Favorite, Manager
)

class UserSerializer(serializers.ModelSerializer):
    def validate_phone_number(self, value):
        import re
        if not re.match(r'^(?:\+255[6-7]\d{8}|0[6-7]\d{8})$', value):
            raise serializers.ValidationError('Phone number must start with +255 or 0, followed by 6 or 7, then 8 digits.')
        return value

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)

    def update(self, instance, validated_data):
        if 'password' in validated_data:
            instance.set_password(validated_data.pop('password'))
        return super().update(instance, validated_data)

    class Meta:
        model = User
        exclude = ['password']

class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = '__all__'

# Moved PropertyMediaSerializer up
class PropertyMediaSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()

    def get_file_url(self, obj):
        request = self.context.get('request')
        return request.build_absolute_uri(obj.file.url) if obj.file else None

    def validate_file(self, value):
        if value:
            ext = value.name.split('.')[-1].lower()
            if self.instance.media_type == 'image' and ext not in ['jpg', 'jpeg', 'png', 'gif']:
                raise serializers.ValidationError("Only image files (jpg, jpeg, png, gif) allowed.")
            if self.instance.media_type == 'video' and ext not in ['mp4', 'mov', 'avi']:
                raise serializers.ValidationError("Only video files (mp4, mov, avi) allowed.")
        return value

    class Meta:
        model = PropertyMedia
        fields = ['id', 'property', 'file', 'file_url', 'media_type', 'uploaded_at']

# Now PropertySerializer can reference PropertyMediaSerializer
class PropertySerializer(serializers.ModelSerializer):
    location = LocationSerializer(read_only=True)
    owner = UserSerializer(read_only=True)
    media = PropertyMediaSerializer(many=True, read_only=True)

    class Meta:
        model = Property
        fields = ['id', 'owner', 'location', 'property_name', 'property_type', 'rental_type', 'price_per_night', 'price_per_month', 'availability_status', 'media']

    def validate(self, data):
        if data['rental_type'] == 'short-term' and not data.get('price_per_night'):
            raise serializers.ValidationError("Price per night is required for short-term rentals.")
        elif data['rental_type'] == 'long-term' and not data.get('price_per_month'):
            raise serializers.ValidationError("Price per month is required for long-term rentals.")
        return data

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
        fields = '__all__'

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
        fields = '__all__'

class BookingInquirySerializer(serializers.ModelSerializer):
    class Meta:
        model = BookingInquiry
        fields = '__all__'

class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
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