from django.db import models
from django.contrib.auth.models import AbstractUser , Group, Permission


# Custom User Model (For Tenants and Landlords)
class User(AbstractUser):
    phone_number = models.CharField(max_length=20, unique=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')], null=True, blank=True)
    profile_picture_url = models.TextField(null=True, blank=True)
    is_landlord = models.BooleanField(default=False)

    groups = models.ManyToManyField(
        Group,
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to...',
        related_name='users_user_groups',  # Unique related_name
        related_query_name='user',
    )

    # Update user_permissions field
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user...',
        related_name='users_user_permissions',  # Unique related_name
        related_query_name='user',
    )
# Location Model
class Location(models.Model):
    address = models.TextField()
    city = models.CharField(max_length=100)
    region = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    latitude = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    longitude = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True)
    postal_code = models.CharField(max_length=20)

# Property Model
class Property(models.Model):
    landlord = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'is_landlord': True})
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True)
    property_name = models.CharField(max_length=100)
    property_type = models.CharField(max_length=50, choices=[('Apartment', 'Apartment'), ('House', 'House'), ('Studio', 'Studio'), ('Villa', 'Villa'), ('Other', 'Other')])
    number_of_bedrooms = models.IntegerField()
    number_of_bathrooms = models.IntegerField()
    square_footage = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    price_per_month = models.DecimalField(max_digits=10, decimal_places=2)
    availability_status = models.CharField(max_length=20, choices=[('Available', 'Available'), ('Rented', 'Rented')], default='Available')
    amenities = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

# Rental Agreement Model
class RentalAgreement(models.Model):
    tenant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rental_agreements')
    landlord = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_agreements')
    property = models.ForeignKey(Property, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    monthly_rent = models.DecimalField(max_digits=10, decimal_places=2)
    security_deposit = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=[('Active', 'Active'), ('Completed', 'Completed'), ('Terminated', 'Terminated')], default='Active')
    created_at = models.DateTimeField(auto_now_add=True)

# Payment Model
class Payment(models.Model):
    agreement = models.ForeignKey(RentalAgreement, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)
    payment_method = models.CharField(max_length=50, choices=[('Bank Transfer', 'Bank Transfer'), ('Credit Card', 'Credit Card'), ('Mobile Money', 'Mobile Money'), ('Cash', 'Cash')])
    payment_status = models.CharField(max_length=20, choices=[('Pending', 'Pending'), ('Completed', 'Completed'), ('Failed', 'Failed')], default='Pending')

# Review Model
class Review(models.Model):
    tenant = models.ForeignKey(User, on_delete=models.CASCADE)
    property = models.ForeignKey(Property, on_delete=models.CASCADE)
    rating = models.IntegerField()
    review_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

# Message Model
class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    content = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    read_status = models.CharField(max_length=20, choices=[('Unread', 'Unread'), ('Read', 'Read')], default='Unread')

# Property Image Model
class PropertyImage(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE)
    image_url = models.TextField()
    uploaded_at = models.DateTimeField(auto_now_add=True)

# Notification Model
class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    notification_type = models.CharField(max_length=50, choices=[('Alert', 'Alert'), ('Reminder', 'Reminder'), ('Message', 'Message')])
    message = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    read_status = models.CharField(max_length=20, choices=[('Unread', 'Unread'), ('Read', 'Read')], default='Unread')

# Booking Inquiry Model
class BookingInquiry(models.Model):
    tenant = models.ForeignKey(User, on_delete=models.CASCADE)
    property = models.ForeignKey(Property, on_delete=models.CASCADE)
    inquiry_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[('Pending', 'Pending'), ('Reviewed', 'Reviewed'), ('Resolved', 'Resolved')], default='Pending')
    message = models.TextField()
