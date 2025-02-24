from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError

class User(AbstractUser):
    ROLE_CHOICES = [
        ('tenant', 'Tenant'),
        ('landlord', 'Landlord'),
        ('hotel_manager', 'Hotel Manager'),
        ('admin', 'Admin'),
    ]
    phone_validator = RegexValidator(
        regex=r'^(?:\+255[6-7]\d{8}|0[6-7]\d{8})$',
        message='Phone number must start with +255 or 0, followed by 6 or 7, then 8 digits (e.g., +255712345678 or 0712345678).'
    )

    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=13, unique=True, blank=False, validators=[phone_validator])
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')], null=True, blank=True)
    profile_picture_url = models.TextField(null=True, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='tenant')
    groups = models.ManyToManyField(Group, related_name='custom_user_groups', blank=True)
    user_permissions = models.ManyToManyField(Permission, related_name='custom_user_permissions', blank=True)

    def __str__(self):
        return f"{self.username} ({self.role})"

    class Meta:
        indexes = [
            models.Index(fields=['phone_number'], name='idx_phone_number'),
            models.Index(fields=['role'], name='idx_role'),
        ]

class Location(models.Model):
    address = models.TextField()
    city = models.CharField(max_length=100)
    region = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    latitude = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    longitude = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True)
    postal_code = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.address}, {self.city}"

class Property(models.Model):
    PROPERTY_TYPE_CHOICES = [
        ('Apartment', 'Apartment'),
        ('House', 'House'),
        ('Studio', 'Studio'),
        ('Villa', 'Villa'),
        ('Hotel', 'Hotel'),
        ('Airbnb', 'Airbnb'),
        ('Other', 'Other'),
    ]
    AVAILABILITY_CHOICES = [
        ('Available', 'Available'),
        ('Rented', 'Rented'),
        ('Booked', 'Booked'),
    ]
    RENTAL_TYPE_CHOICES = [
        ('long-term', 'Long-Term'),
        ('short-term', 'Short-Term'),
    ]

    owner = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role__in': ['landlord', 'hotel_manager']}, related_name='properties')
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True)
    property_name = models.CharField(max_length=100)
    property_type = models.CharField(max_length=50, choices=PROPERTY_TYPE_CHOICES)
    is_multi_room = models.BooleanField(default=False)
    rental_type = models.CharField(max_length=20, choices=RENTAL_TYPE_CHOICES)
    number_of_bedrooms = models.IntegerField(null=True, blank=True)
    number_of_bathrooms = models.IntegerField(null=True, blank=True)
    square_footage = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    description = models.TextField()
    price_per_month = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    price_per_night = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    availability_status = models.CharField(max_length=20, choices=AVAILABILITY_CHOICES, default='Available')
    amenities = models.ManyToManyField('Amenity', through='PropertyAmenity', related_name='properties')
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if self.rental_type == 'short-term' and not self.price_per_night:
            raise ValidationError("Price per night is required for short-term rentals.")
        if self.rental_type == 'long-term' and not self.price_per_month:
            raise ValidationError("Price per month is required for long-term rentals.")

    def __str__(self):
        return f"{self.property_name} ({self.property_type})"

    class Meta:
        indexes = [
            models.Index(fields=['owner'], name='idx_property_owner'),
            models.Index(fields=['location'], name='idx_property_location'),
        ]

class Room(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='rooms')
    room_number = models.CharField(max_length=20)
    price_per_night = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    available = models.BooleanField(default=True)

    def __str__(self):
        return f"Room {self.room_number} at {self.property.property_name}"

class Booking(models.Model):
    RENTAL_TYPE_CHOICES = [
        ('short-term', 'Short-Term'),
        ('long-term', 'Long-Term'),
    ]
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Confirmed', 'Confirmed'),
        ('Cancelled', 'Cancelled'),
        ('Completed', 'Completed'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='bookings')
    room = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True, blank=True)
    start_date = models.DateField()
    end_date = models.DateField()
    rental_type = models.CharField(max_length=20, choices=RENTAL_TYPE_CHOICES)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    monthly_rent = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    security_deposit = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Booking for {self.property.property_name} by {self.user.username}"

class Payment(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('Bank Transfer', 'Bank Transfer'),
        ('Credit Card', 'Credit Card'),
        ('Mobile Money', 'Mobile Money'),
        ('Cash', 'Cash'),
    ]
    PAYMENT_STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Completed', 'Completed'),
        ('Failed', 'Failed'),
    ]

    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHOD_CHOICES)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='Pending')

    def __str__(self):
        return f"Payment of {self.amount} for {self.booking}"

class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='reviews')
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    review_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review of {self.property.property_name} by {self.user.username}"

class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    content = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    read_status = models.CharField(max_length=20, choices=[('Unread', 'Unread'), ('Read', 'Read')], default='Unread')

    def __str__(self):
        return f"Message from {self.sender.username} to {self.receiver.username}"

class PropertyMedia(models.Model):
    MEDIA_TYPE_CHOICES = [
        ('image', 'Image'),
        ('video', 'Video'),
    ]
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='media')
    file = models.FileField(upload_to='property_media/', null=True, blank=True)
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPE_CHOICES)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.media_type.capitalize()} for {self.property.property_name}"

class Notification(models.Model):
    NOTIFICATION_TYPE_CHOICES = [
        ('Alert', 'Alert'),
        ('Reminder', 'Reminder'),
        ('Message', 'Message'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPE_CHOICES)
    message = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    read_status = models.CharField(max_length=20, choices=[('Unread', 'Unread'), ('Read', 'Read')], default='Unread')

    def __str__(self):
        return f"{self.notification_type} for {self.user.username}"

class BookingInquiry(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Reviewed', 'Reviewed'),
        ('Resolved', 'Resolved'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='inquiries')
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='inquiries')
    inquiry_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    message = models.TextField()

    def __str__(self):
        return f"Inquiry for {self.property.property_name} by {self.user.username}"

class Amenity(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class PropertyAmenity(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='property_amenities')
    amenity = models.ForeignKey(Amenity, on_delete=models.CASCADE, related_name='property_amenities')

    class Meta:
        unique_together = ('property', 'amenity')

    def __str__(self):
        return f"{self.amenity.name} for {self.property.property_name}"

class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='favorited_by')
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'property')

    def __str__(self):
        return f"{self.property.property_name} favorited by {self.user.username}"

class Manager(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='managed_properties')
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='managers')
    role = models.CharField(max_length=50)
    assigned_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} managing {self.property.property_name}"