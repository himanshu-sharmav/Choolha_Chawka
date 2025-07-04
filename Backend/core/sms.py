from django.conf import settings
from twilio.rest import Client
import logging

logger = logging.getLogger(__name__)

def get_twilio_client():
    """Return a Twilio client instance"""
    return Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

def send_sms(to_number, message):
    """
    Send an SMS message using Twilio
    
    Args:
        to_number: Recipient phone number (should include country code)
        message: SMS message content
        
    Returns:
        dict: Response containing success status and message SID or error
    """
    try:
        # Format phone number if needed (ensure it has +91 prefix for India)
        if not to_number.startswith('+'):
            to_number = f"+91{to_number.lstrip('0')}"
            
        client = get_twilio_client()
        message = client.messages.create(
            body=message,
            from_=settings.TWILIO_PHONE_NUMBER,
            to=to_number
        )
        
        logger.info(f"SMS sent to {to_number}: {message.sid}")
        return {
            'success': True,
            'message_sid': message.sid
        }
    except Exception as e:
        logger.error(f"Failed to send SMS to {to_number}: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

def send_otp(phone_number, otp):
    """
    Send an OTP via SMS
    
    Args:
        phone_number: The user's phone number
        otp: The OTP code to send
        
    Returns:
        dict: Response from send_sms
    """
    message = f"Your Choolha Chowka verification code is: {otp}. Valid for 15 minutes."
    return send_sms(phone_number, message)
