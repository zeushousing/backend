from django.test import TestCase
from rest_framework.test import APIClient
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User, Property, Room, Booking, PropertyMedia, Location, SupportTicket, Notification
from .serializers import UserSerializer
import datetime

class BookingTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.landlord = User.objects.create_user(
            username='landlord',
            name='Landlord User',
            email='landlord@example.com',
            phone_number='+255712345678',
            password='Test1234',
            role='landlord'
        )
        self.tenant = User.objects.create_user(
            username='tenant',
            name='Tenant User',
            email='tenant@example.com',
            phone_number='+255712345679',
            password='Test1234',
            role='tenant'
        )
        self.admin = User.objects.create_user(
            username='admin',
            name='Admin User',
            email='admin@example.com',
            phone_number='+255712345680',
            password='Test1234',
            role='admin'
        )
        self.tenant_token = str(RefreshToken.for_user(self.tenant).access_token)
        self.admin_token = str(RefreshToken.for_user(self.admin).access_token)

        self.location = Location.objects.create(
            city='Dar es Salaam',
            latitude=-6.7924,
            longitude=39.2083,
            address='123 Main St',
            country='Tanzania',
            postal_code='12345'
        )
        self.location_nairobi = Location.objects.create(
            city='Nairobi',
            latitude=-1.2921,
            longitude=36.8219,
            address='456 Elm St',
            country='Kenya',
            postal_code='67890'
        )
        self.property = Property.objects.create(
            owner=self.landlord,
            location=self.location,
            property_name='Dar Property 1',
            property_type='Apartment',
            rental_type='short-term',
            price_per_night=100,
            availability_status='Available',
            is_multi_room=True
        )
        self.property_expensive = Property.objects.create(
            owner=self.landlord,
            location=self.location,
            property_name='Dar Property 2',
            property_type='Apartment',
            rental_type='short-term',
            price_per_night=200,
            availability_status='Available'
        )
        self.property_nairobi = Property.objects.create(
            owner=self.landlord,
            location=self.location_nairobi,
            property_name='Nairobi Property',
            property_type='Apartment',
            rental_type='short-term',
            price_per_night=100,
            availability_status='Available'
        )
        self.room = Room.objects.create(
            property=self.property,
            room_number='101',
            floor_number=1,
            price_per_night=50
        )
        self.booking = Booking.objects.create(
            user=self.tenant,
            property=self.property,
            room=self.room,
            start_date=datetime.date.today() + datetime.timedelta(days=1),
            end_date=datetime.date.today() + datetime.timedelta(days=5),
            rental_type='short-term',
            total_price=400,
            status='Pending'
        )

    def test_property_creation(self):
        self.assertEqual(self.property.property_name, 'Dar Property 1')

    def test_property_media_upload(self):
        media = PropertyMedia.objects.create(property=self.property, file='test.jpg', media_type='image')
        self.assertEqual(media.media_type, 'image')

    def test_property_creation_invalid(self):
        with self.assertRaises(DjangoValidationError):
            invalid_property = Property(owner=self.landlord, property_name='Invalid', rental_type='short-term')
            invalid_property.full_clean()

    def test_valid_status_transition(self):
        self.booking.status = 'Confirmed'
        self.booking.save()
        self.assertEqual(self.booking.status, 'Confirmed')
        self.property.refresh_from_db()
        self.assertEqual(self.property.availability_status, 'Booked')

    def test_invalid_status_transition(self):
        self.booking.status = 'Cancelled'
        self.booking.save()
        with self.assertRaises(DjangoValidationError):
            self.booking.status = 'Confirmed'
            self.booking.save()

    def test_overlapping_booking_validation(self):
        with self.assertRaises(DjangoValidationError):
            Booking.objects.create(
                user=self.tenant,
                property=self.property,
                room=self.room,
                start_date=datetime.date.today() + datetime.timedelta(days=2),
                end_date=datetime.date.today() + datetime.timedelta(days=3),
                rental_type='short-term',
                total_price=200,
                status='Pending'
            )

    def test_invalid_date_range(self):
        with self.assertRaises(DjangoValidationError):
            self.booking.start_date = datetime.date.today() + datetime.timedelta(days=5)
            self.booking.end_date = datetime.date.today() + datetime.timedelta(days=1)
            self.booking.save()

    def test_pricing_validation_short_term(self):
        with self.assertRaises(DjangoValidationError):
            Booking.objects.create(
                user=self.tenant,
                property=self.property,
                start_date=datetime.date.today() + datetime.timedelta(days=10),
                end_date=datetime.date.today() + datetime.timedelta(days=15),
                rental_type='short-term',
                total_price=None,
                status='Pending'
            )

    def test_pricing_validation_long_term(self):
        with self.assertRaises(DjangoValidationError):
            Booking.objects.create(
                user=self.tenant,
                property=self.property,
                start_date=datetime.date.today() + datetime.timedelta(days=10),
                end_date=datetime.date.today() + datetime.timedelta(days=40),
                rental_type='long-term',
                monthly_rent=None,
                status='Pending'
            )

    def test_property_availability_reset(self):
        self.booking.status = 'Cancelled'
        self.booking.save()
        self.property.refresh_from_db()
        self.assertEqual(self.property.availability_status, 'Available')

    def test_property_name_index(self):
        Property.objects.create(
            owner=self.landlord,
            property_name='Indexed Property',
            rental_type='short-term',
            price_per_night=100,
            location=self.location
        )
        result = Property.objects.filter(property_name='Indexed Property').exists()
        self.assertTrue(result)

    def test_password_validation(self):
        serializer = UserSerializer(data={
            'username': 'weakpass',
            'name': 'Weak Pass',
            'email': 'weak@example.com',
            'phone_number': '+255712345670',
            'password': 'weak',
            'role': 'tenant'
        })
        with self.assertRaises(ValidationError):
            serializer.is_valid(raise_exception=True)

    def test_soft_deletion_user(self):
        user = User.objects.create_user(
            username='softdelete',
            name='Soft Delete',
            email='soft@example.com',
            phone_number='+255712345670',
            password='Test1234',
            role='tenant'
        )
        user.delete()
        self.assertTrue(user.is_deleted)
        self.assertIsNotNone(user.deleted_at)
        self.assertFalse(User.objects.filter(username='softdelete').exists())

    def test_soft_deletion_property(self):
        prop = Property.objects.create(
            owner=self.landlord,
            property_name='Soft Delete Property',
            rental_type='short-term',
            price_per_night=100,
            location=self.location
        )
        prop.delete()
        self.assertTrue(prop.is_deleted)
        self.assertIsNotNone(prop.deleted_at)
        self.assertFalse(Property.objects.filter(property_name='Soft Delete Property').exists())

    def test_search_by_location(self):
        Property.objects.create(
            owner=self.landlord,
            property_name='City Property',
            rental_type='short-term',
            price_per_night=100,
            location=self.location
        )
        result = Property.objects.filter(location__city='Dar es Salaam').exists()
        self.assertTrue(result)

    def test_nearby_properties(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.tenant_token}')
        response = self.client.get(
            '/api/v1/properties/nearby/?latitude=-6.7924&longitude=39.2083&radius=5&property_type=Apartment&sort_by=price_per_night',
            format='json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.data['results']) > 0)
        self.assertIn('distance', response.data['results'][0])
        prices = [p['price_per_night'] for p in response.data['results'] if p['price_per_night'] is not None]
        self.assertEqual(prices, sorted(prices))
        for prop in response.data['results']:
            self.assertEqual(prop['location']['city'], 'Dar es Salaam')
        self.assertNotIn('Nairobi Property', [p['property_name'] for p in response.data['results']])

    def test_nearby_properties_advanced_filtering(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.tenant_token}')
        response = self.client.get(
            '/api/v1/properties/nearby/?latitude=-6.7924&longitude=39.2083&radius=10&price_per_night_min=50&price_per_night_max=150',
            format='json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['property_name'], 'Dar Property 1')
        self.assertEqual(response.data['results'][0]['location']['city'], 'Dar es Salaam')
        property_names = [p['property_name'] for p in response.data['results']]
        self.assertNotIn('Dar Property 2', property_names)
        self.assertNotIn('Nairobi Property', property_names)

    def test_chatbot_response(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.tenant_token}')
        response = self.client.post(
            '/api/v1/users/chat/',
            {'message': 'Check my booking status'},
            format='json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('Your latest booking', response.data['response'])

    def test_support_ticket_creation(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.tenant_token}')
        response = self.client.post(
            '/api/v1/support/tickets/',
            {'subject': 'Test Issue', 'description': 'I need help'},
            format='json'
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Notification.objects.filter(user=self.admin).count(), 1)

    def test_support_ticket_status_update(self):
        ticket = SupportTicket.objects.create(user=self.tenant, subject='Test', description='Help')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_token}')
        response = self.client.post(
            f'/api/v1/support/tickets/{ticket.id}/update_status/',
            {'status': 'Resolved'},
            format='json'
        )
        self.assertEqual(response.status_code, 200)
        ticket.refresh_from_db()
        self.assertEqual(ticket.status, 'Resolved')
        self.assertEqual(Notification.objects.filter(user=self.tenant).count(), 1)

    def test_update_fcm_token(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.tenant_token}')
        response = self.client.post(
            f'/api/v1/users/{self.tenant.id}/update_fcm_token/',
            {'fcm_token': 'test-device-token'},
            format='json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'FCM token updated')
        self.tenant.refresh_from_db()
        self.assertEqual(self.tenant.fcm_token, 'test-device-token')

    def test_notification_creation_with_fcm(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.tenant_token}')
        response = self.client.post(
            '/api/v1/notifications/',
            {'notification_type': 'Alert', 'message': 'FCM Notification Test'},  # Changed to 'Alert'
            format='json'
        )
        print(response.data)  # Debug output
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Notification.objects.filter(user=self.tenant).count(), 1)
        notification = Notification.objects.get(user=self.tenant, notification_type='Alert')
        self.assertEqual(notification.message, 'FCM Notification Test')