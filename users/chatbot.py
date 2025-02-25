from google.cloud import dialogflow_v2 as dialogflow
from django.conf import settings
import os
from .models import Booking, Property, Message, User, Notification

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = settings.DIALOGFLOW_CREDENTIALS

def detect_intent(text, session_id, project_id='zeuschatbot-wesq'):  # Replace with your Dialogflow project ID
    session_client = dialogflow.SessionsClient()
    session = session_client.session_path(project_id, session_id)
    text_input = dialogflow.TextInput(text=text, language_code='en')
    query_input = dialogflow.QueryInput(text=text_input)
    response = session_client.detect_intent(
        request={"session": session, "query_input": query_input}
    )
    intent_name = response.query_result.intent.display_name
    property_name = response.query_result.parameters.get('property_name', None)
    return response.query_result.fulfillment_text, intent_name, property_name

def handle_chatbot_request(user, message):
    session_id = str(user.id)
    response_text, intent_name, property_name = detect_intent(message, session_id)

    if intent_name == 'CheckBookingStatus':
        latest_booking = Booking.objects.filter(user=user).order_by('-created_at').first()
        if latest_booking:
            response_text = f"Your latest booking for {latest_booking.property.property_name} is {latest_booking.status}."
        else:
            response_text = "You have no bookings yet."
    elif intent_name == 'ListProperties':
        properties = Property.objects.filter(availability_status='Available')[:5]
        if properties:
            response_text = "Here are some available properties: " + ", ".join(p.property_name for p in properties)
        else:
            response_text = "No available properties found."
    elif intent_name == 'SupportRequest':
        admin = User.objects.filter(role='admin').first()
        if admin:
            Message.objects.create(
                sender=user,
                receiver=admin,
                content=f"Support request from {user.username}: {message}"
            )
            Notification.objects.create(
                user=admin,
                notification_type='Support',
                message=f"New support request from {user.username}"
            )
            response_text = "Your request has been forwarded to our support team. We’ll get back to you soon!"
        else:
            response_text = "Sorry, no support staff available right now."
    elif intent_name == 'PropertyDetails' and property_name:
        property = Property.objects.filter(property_name__icontains=property_name).first()
        if property:
            price = f"${property.price_per_night}/night" if property.price_per_night else f"${property.price_per_month}/month"
            response_text = f"{property.property_name} is {property.availability_status}. Price: {price}."
        else:
            response_text = f"I couldn’t find a property named '{property_name}'. Try another name."
    # Fallback for unrecognized intents or missing parameters
    if not intent_name or (intent_name == 'PropertyDetails' and not property_name):
        response_text = "I didn’t understand that. Try asking about your booking status, available properties, or request support."

    Message.objects.create(
        sender=user,
        receiver=user,
        content=f"User: {message}\nBot: {response_text}"
    )
    return response_text