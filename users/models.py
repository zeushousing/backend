# users/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission, UserManager
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator, FileExtensionValidator
from django.core.exceptions import ValidationError
from django.utils import timezone

class ActiveUserManager(UserManager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)

class ActiveManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)

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

    objects = ActiveUserManager()
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=13, unique=True, blank=False, validators=[phone_validator])
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')], null=True, blank=True)
    profile_picture = models.ImageField(
        upload_to='profile_pictures/',
        null=True,
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif'])]
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='tenant')
    groups = models.ManyToManyField(Group, related_name='custom_user_groups', blank=True)
    user_permissions = models.ManyToManyField(Permission, related_name='custom_user_permissions', blank=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    # Added FCM token field
    fcm_token = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="FCM device token for push notifications"
    )

    def delete(self, *args, **kwargs):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()

    @classmethod
    def get_active(cls):
        return cls.objects.all()

    def __str__(self):
        return f"{self.username} ({self.role})"

    class Meta:
        app_label = 'users'
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

    objects = ActiveManager()
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
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    def clean(self):
        if self.rental_type == 'short-term' and not self.price_per_night:
            raise ValidationError("Price per night is required for short-term rentals.")
        if self.rental_type == 'long-term' and not self.price_per_month:
            raise ValidationError("Price per month is required for long-term rentals.")

    def delete(self, *args, **kwargs):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()

    @classmethod
    def get_active(cls):
        return cls.objects.all()

    def __str__(self):
        return f"{self.property_name} ({self.property_type})"

    class Meta:
        indexes = [
            models.Index(fields=['owner'], name='idx_property_owner'),
            models.Index(fields=['location'], name='idx_property_location'),
            models.Index(fields=['property_name'], name='idx_property_name'),
        ]

class Room(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='rooms')
    room_number = models.CharField(max_length=20)
    floor_number = models.IntegerField(null=True, blank=True)
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
    STATUS_TRANSITIONS = {
        'Pending': ['Confirmed', 'Cancelled'],
        'Confirmed': ['Completed', 'Cancelled'],
        'Cancelled': [],
        'Completed': [],
    }

    objects = ActiveManager()
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
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Booking for {self.property.property_name} by {self.user.username}"

    def clean(self):
        if self.rental_type == 'short-term' and not self.total_price:
            raise ValidationError("Total price is required for short-term bookings.")
        if self.rental_type == 'long-term' and not self.monthly_rent:
            raise ValidationError("Monthly rent is required for long-term bookings.")
        if self.start_date >= self.end_date:
            raise ValidationError("End date must be after start date.")
        overlapping_bookings = Booking.objects.filter(
            property=self.property,
            status__in=['Pending', 'Confirmed'],
            start_date__lte=self.end_date,
            end_date__gte=self.start_date
        ).exclude(pk=self.pk)
        if self.property.is_multi_room and self.room:
            overlapping_bookings = overlapping_bookings.filter(room=self.room)
        elif not self.property.is_multi_room:
            overlapping_bookings = overlapping_bookings.filter(room__isnull=True)
        if overlapping_bookings.exists():
            raise ValidationError("This property or room is already booked for the selected dates.")

    def save(self, *args, **kwargs):
        if self.pk:
            old_booking = Booking.objects.get(pk=self.pk)
            if old_booking.status != self.status:
                if self.status not in self.STATUS_TRANSITIONS.get(old_booking.status, []):
                    raise ValidationError(f"Cannot transition from {old_booking.status} to {self.status}")
        
        self.clean()
        
        super().save(*args, **kwargs)
        
        property = self.property
        active_bookings = Booking.objects.filter(
            property=property,
            status__in=['Pending', 'Confirmed'],
            end_date__gte=timezone.now()
        ).exists()
        property.availability_status = 'Booked' if active_bookings else 'Available'
        property.save()

    def delete(self, *args, **kwargs):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()

    @classmethod
    def get_active(cls):
        return cls.objects.all()

    class Meta:
        indexes = [
            models.Index(fields=['start_date', 'end_date'], name='idx_booking_dates'),
        ]

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

    objects = ActiveManager()
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHOD_CHOICES)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='Pending')
    stripe_payment_intent_id = models.CharField(max_length=255, null=True, blank=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Payment of {self.amount} for {self.booking}"

    def delete(self, *args, **kwargs):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()

    @classmethod
    def get_active(cls):
        return cls.objects.all()

class Review(models.Model):
    objects = ActiveManager()
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='reviews')
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    review_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Review of {self.property.property_name} by {self.user.username}"

    def delete(self, *args, **kwargs):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()

    @classmethod
    def get_active(cls):
        return cls.objects.all()

class Message(models.Model):
    objects = ActiveManager()
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    content = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    read_status = models.CharField(max_length=20, choices=[('Unread', 'Unread'), ('Read', 'Read')], default='Unread')
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Message from {self.sender.username} to {self.receiver.username}"

    def delete(self, *args, **kwargs):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()

    @classmethod
    def get_active(cls):
        return cls.objects.all()

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
        ('Support', 'Support'),
    ]
    objects = ActiveManager()
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPE_CHOICES)
    message = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    read_status = models.CharField(max_length=20, choices=[('Unread', 'Unread'), ('Read', 'Read')], default='Unread')
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.notification_type} for {self.user.username}"

    def delete(self, *args, **kwargs):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()

    @classmethod
    def get_active(cls):
        return cls.objects.all()

class BookingInquiry(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Reviewed', 'Reviewed'),
        ('Resolved', 'Resolved'),
    ]
    objects = ActiveManager()
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='inquiries')
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='inquiries')
    inquiry_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    message = models.TextField()
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Inquiry for {self.property.property_name} by {self.user.username}"

    def delete(self, *args, **kwargs):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()

    @classmethod
    def get_active(cls):
        return cls.objects.all()

class MaintenanceRequest(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('In Progress', 'In Progress'),
        ('Resolved', 'Resolved'),
    ]
    objects = ActiveManager()
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='maintenance_requests')
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='maintenance_requests')
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Maintenance for {self.property.property_name} by {self.user.username}"

    def delete(self, *args, **kwargs):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()

    @classmethod
    def get_active(cls):
        return cls.objects.all()

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

class SupportTicket(models.Model):
    STATUS_CHOICES = [
        ('Open', 'Open'),
        ('In Progress', 'In Progress'),
        ('Resolved', 'Resolved'),
    ]
    objects = ActiveManager()
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='support_tickets')
    subject = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Open')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Ticket #{self.id}: {self.subject} by {self.user.username}"

    def delete(self, *args, **kwargs):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()

    @classmethod
    def get_active(cls):
        return cls.objects.all()