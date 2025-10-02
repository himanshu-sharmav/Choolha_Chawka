"""
Alternative email backend using Resend REST API instead of SMTP
This can be more reliable than SMTP in containerized environments
"""

import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

def send_email_via_resend_api(to_email, subject, html_content, text_content=None):
    """
    Send email using Resend REST API instead of SMTP
    """
    try:
        api_key = settings.EMAIL_HOST_PASSWORD  # RESEND_API_KEY
        api_url = "https://api.resend.com/emails"
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "from": settings.DEFAULT_FROM_EMAIL,
            "to": [to_email],
            "subject": subject,
            "html": html_content,
            "text": text_content or html_content
        }
        
        logger.info(f"📧 Sending email via Resend API to {to_email}")
        response = requests.post(api_url, json=payload, headers=headers, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"✅ Email sent via Resend API: {result.get('id')}")
            return True, result.get('id')
        else:
            error_msg = f"Resend API error: {response.status_code} - {response.text}"
            logger.error(f"❌ {error_msg}")
            return False, error_msg
            
    except Exception as e:
        error_msg = f"Resend API exception: {str(e)}"
        logger.error(f"❌ {error_msg}")
        return False, error_msg
