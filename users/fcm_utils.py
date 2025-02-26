# users/fcm_utils.py
from pyfcm import FCMNotification
from django.conf import settings

def send_fcm_notification(user, title, body):
    """
    Send a push notification to a user's device via FCM.
    
    Args:
        user: User instance with an fcm_token
        title: Notification title (string)
        body: Notification message (string)
    Returns:
        bool: True if successful, False otherwise
    """
    if not user.fcm_token:
        return False
    
    push_service = FCMNotification(api_key=settings.FCM_SERVER_KEY)
    try:
        result = push_service.notify_single_device(
            registration_id=user.fcm_token,
            message_title=title,
            message_body=body
        )
        return result.get('success', 0) == 1
    except Exception as e:
        print(f"FCM error: {e}")
        return False