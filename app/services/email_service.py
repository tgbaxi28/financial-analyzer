"""Email service using AWS SES."""
import boto3
from botocore.exceptions import ClientError
from typing import Optional

from app.config import settings
from app.utils.logger import logger


class EmailService:
    """Service for sending emails via AWS SES."""

    def __init__(self):
        """Initialize AWS SES client."""
        self.ses_client = boto3.client(
            'ses',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        self.sender_email = settings.SES_SENDER_EMAIL

    def send_magic_link(self, recipient_email: str, magic_link: str) -> bool:
        """
        Send magic link email for authentication.

        Args:
            recipient_email: Recipient's email address
            magic_link: Magic link URL

        Returns:
            True if email sent successfully, False otherwise
        """
        subject = f"Login to {settings.APP_NAME}"

        html_body = f"""
        <html>
        <head></head>
        <body>
            <h2>Welcome to {settings.APP_NAME}</h2>
            <p>Click the link below to login to your account:</p>
            <p>
                <a href="{magic_link}" style="
                    background-color: #4CAF50;
                    color: white;
                    padding: 14px 20px;
                    text-align: center;
                    text-decoration: none;
                    display: inline-block;
                    border-radius: 4px;
                ">Login to {settings.APP_NAME}</a>
            </p>
            <p>Or copy and paste this link in your browser:</p>
            <p>{magic_link}</p>
            <p><strong>This link will expire in {settings.MAGIC_LINK_EXPIRE_MINUTES} minutes.</strong></p>
            <p>If you didn't request this login link, you can safely ignore this email.</p>
            <hr>
            <p style="color: #666; font-size: 12px;">
                This is an automated message from {settings.APP_NAME}. Please do not reply to this email.
            </p>
        </body>
        </html>
        """

        text_body = f"""
        Welcome to {settings.APP_NAME}

        Click the link below to login to your account:
        {magic_link}

        This link will expire in {settings.MAGIC_LINK_EXPIRE_MINUTES} minutes.

        If you didn't request this login link, you can safely ignore this email.

        ---
        This is an automated message from {settings.APP_NAME}. Please do not reply to this email.
        """

        try:
            response = self.ses_client.send_email(
                Source=self.sender_email,
                Destination={
                    'ToAddresses': [recipient_email]
                },
                Message={
                    'Subject': {
                        'Data': subject,
                        'Charset': 'UTF-8'
                    },
                    'Body': {
                        'Text': {
                            'Data': text_body,
                            'Charset': 'UTF-8'
                        },
                        'Html': {
                            'Data': html_body,
                            'Charset': 'UTF-8'
                        }
                    }
                }
            )

            logger.info(f"Magic link email sent to {recipient_email}. MessageId: {response['MessageId']}")
            return True

        except ClientError as e:
            logger.error(f"Failed to send magic link email to {recipient_email}: {e.response['Error']['Message']}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending email to {recipient_email}: {str(e)}")
            return False

    def send_welcome_email(self, recipient_email: str, first_name: str) -> bool:
        """
        Send welcome email to new user.

        Args:
            recipient_email: Recipient's email address
            first_name: User's first name

        Returns:
            True if email sent successfully, False otherwise
        """
        subject = f"Welcome to {settings.APP_NAME}!"

        html_body = f"""
        <html>
        <head></head>
        <body>
            <h2>Welcome to {settings.APP_NAME}, {first_name}!</h2>
            <p>Thank you for registering. Your account has been successfully created.</p>
            <p>You can now:</p>
            <ul>
                <li>Upload your financial documents (bank statements, investment portfolios, etc.)</li>
                <li>Add family members to track their finances</li>
                <li>Get AI-powered insights on your financial data</li>
                <li>View comprehensive dashboards and analytics</li>
            </ul>
            <p>We're committed to keeping your financial data secure and private.</p>
            <p>If you have any questions, feel free to reach out to our support team.</p>
            <hr>
            <p style="color: #666; font-size: 12px;">
                This is an automated message from {settings.APP_NAME}. Please do not reply to this email.
            </p>
        </body>
        </html>
        """

        text_body = f"""
        Welcome to {settings.APP_NAME}, {first_name}!

        Thank you for registering. Your account has been successfully created.

        You can now:
        - Upload your financial documents (bank statements, investment portfolios, etc.)
        - Add family members to track their finances
        - Get AI-powered insights on your financial data
        - View comprehensive dashboards and analytics

        We're committed to keeping your financial data secure and private.

        If you have any questions, feel free to reach out to our support team.

        ---
        This is an automated message from {settings.APP_NAME}. Please do not reply to this email.
        """

        try:
            response = self.ses_client.send_email(
                Source=self.sender_email,
                Destination={
                    'ToAddresses': [recipient_email]
                },
                Message={
                    'Subject': {
                        'Data': subject,
                        'Charset': 'UTF-8'
                    },
                    'Body': {
                        'Text': {
                            'Data': text_body,
                            'Charset': 'UTF-8'
                        },
                        'Html': {
                            'Data': html_body,
                            'Charset': 'UTF-8'
                        }
                    }
                }
            )

            logger.info(f"Welcome email sent to {recipient_email}. MessageId: {response['MessageId']}")
            return True

        except ClientError as e:
            logger.error(f"Failed to send welcome email to {recipient_email}: {e.response['Error']['Message']}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending welcome email to {recipient_email}: {str(e)}")
            return False


# Global email service instance
email_service = EmailService()
