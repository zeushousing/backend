from django.test import TestCase, Client
from rest_framework.test import APIClient
from .models import User, Property, PropertyMedia
from django.core.exceptions import ValidationError

class PropertyTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='landlord', email='landlord@example.com', phone_number='+255712345678', password='testpass', role='landlord')
        self.property = Property.objects.create(owner=self.user, property_name='Test Property', rental_type='short-term', price_per_night=100)

    def test_property_creation(self):
        self.assertEqual(self.property.property_name, 'Test Property')

    def test_property_media_upload(self):
        media = PropertyMedia.objects.create(property=self.property, file='test.jpg', media_type='image')
        self.assertEqual(media.media_type, 'image')

    def test_property_creation_invalid(self):
        with self.assertRaises(ValidationError):
            invalid_property = Property(owner=self.user, property_name='Invalid', rental_type='short-term')
            invalid_property.full_clean()  # Should fail due to missing price_per_night

    def test_user_role_default(self):
        user = User.objects.create_user(username='tenant', email='tenant@example.com', phone_number='+255712345679', password='test')
        self.assertEqual(user.role, 'tenant')

def test_booking_creation(self):
    booking = Booking.objects.create(
        user=self.user, property=self.property, start_date='2025-03-01', end_date='2025-03-05',
        rental_type='short-term', total_price=400
    )
    self.assertEqual(booking.total_price, 400)