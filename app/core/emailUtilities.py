from scholarSparkObservability.core import OTelSetup
from fastapi import BackgroundTasks
import httpx
from .config import settings

def get_otel():
    """Lazy initialization of OpenTelemetry instance"""
    return OTelSetup.get_instance()

async def send_reset_email(email: str, reset_link: str):
    """
    Send password reset email to user
    
    Args:
        email: User's email address
        reset_link: Password reset link
    """
    otel = get_otel()
    with otel.create_span("send_reset_email") as span:
        try:
            # TODO: Implement actual email sending logic
            # For now, just print to console in development
            print(f"Password reset email would be sent to {email}")
            print(f"Reset link: {reset_link}")
            
            # In production, you would integrate with an email service
            # Example with an email service API:
            # async with httpx.AsyncClient() as client:
            #     await client.post(
            #         "https://api.emailservice.com/v1/send",
            #         json={
            #             "to": email,
            #             "subject": "Password Reset Request",
            #             "template": "password_reset",
            #             "variables": {
            #                 "reset_link": reset_link
            #             }
            #         }
            #     )
            
        except Exception as e:
            otel.record_exception(span, e)
            raise