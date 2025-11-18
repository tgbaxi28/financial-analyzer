"""Email service using AWS SES."""
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

from app.config import settings
from app.utils.logger import logger


class EmailService:
    """Service for sending emails via AWS SES."""

    def __init__(self):
        """Initialize AWS SES client."""
        self.ses_enabled = self._check_ses_configuration()
        
        if self.ses_enabled:
            try:
                self.ses_client = boto3.client(
                    'ses',
                    region_name=settings.AWS_REGION,
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
                )
                self.sender_email = settings.SES_SENDER_EMAIL
                logger.info("AWS SES email service initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize SES client: {str(e)}. Falling back to development mode.")
                self.ses_enabled = False
        else:
            logger.warning("AWS SES not configured. Running in development mode - emails will be logged only.")
            self.ses_client = None
            self.sender_email = None

    def _check_ses_configuration(self) -> bool:
        """Check if AWS SES is properly configured."""
        required_configs = [
            settings.AWS_ACCESS_KEY_ID,
            settings.AWS_SECRET_ACCESS_KEY,
            settings.AWS_REGION,
            settings.SES_SENDER_EMAIL
        ]
        return all(config for config in required_configs)

    def send_magic_link(self, recipient_email: str, magic_link: str) -> bool:
        """
        Send magic link email for authentication.

        Args:
            recipient_email: Recipient's email address
            magic_link: Magic link URL

        Returns:
            True if email sent successfully, False otherwise
        """
        # Development mode - log the magic link instead of sending email
        if not self.ses_enabled:
            # Extract token from magic_link for easier copy-paste
            token = magic_link.split("token=")[-1] if "token=" in magic_link else magic_link
            
            logger.warning("=" * 80)
            logger.warning("AWS SES NOT CONFIGURED - DEVELOPMENT MODE")
            logger.warning("=" * 80)
            logger.warning(f"📧 Magic Link for: {recipient_email}")
            logger.warning(f"🔗 Full Link: {magic_link}")
            logger.warning(f"🎫 Token Only: {token}")
            logger.warning(f"⏰ Expires in: {settings.MAGIC_LINK_EXPIRE_MINUTES} minutes")
            logger.warning("=" * 80)
            logger.warning("For Gradio UI: Copy the TOKEN ONLY and paste in verification field")
            logger.warning("For direct access: Click or paste the FULL LINK in browser")
            logger.warning("=" * 80)
            return True

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

        except (ClientError, NoCredentialsError) as e:
            error_msg = e.response['Error']['Message'] if hasattr(e, 'response') else str(e)
            logger.error(f"Failed to send magic link email to {recipient_email}: {error_msg}")
            logger.warning("Falling back to development mode - logging magic link")
            logger.warning("=" * 80)
            logger.warning(f"📧 Magic Link for: {recipient_email}")
            logger.warning(f"🔗 Link: {magic_link}")
            logger.warning("=" * 80)
            return True  # Return True to not fail the registration
        except Exception as e:
            logger.error(f"Unexpected error sending email to {recipient_email}: {str(e)}")
            logger.warning("=" * 80)
            logger.warning(f"📧 Magic Link for: {recipient_email}")
            logger.warning(f"🔗 Link: {magic_link}")
            logger.warning("=" * 80)
            return True  # Return True to not fail the registration

    def send_welcome_email(self, recipient_email: str, first_name: str) -> bool:
        """
        Send welcome email to new user.

        Args:
            recipient_email: Recipient's email address
            first_name: User's first name

        Returns:
            True if email sent successfully, False otherwise
        """
        # Development mode - log instead of sending email
        if not self.ses_enabled:
            logger.info(f"📧 [DEV MODE] Welcome email for: {first_name} ({recipient_email})")
            return True

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

        except (ClientError, NoCredentialsError) as e:
            error_msg = e.response['Error']['Message'] if hasattr(e, 'response') else str(e)
            logger.warning(f"Could not send welcome email to {recipient_email}: {error_msg}")
            return True  # Return True to not fail the registration
        except Exception as e:
            logger.warning(f"Could not send welcome email to {recipient_email}: {str(e)}")
            return True  # Return True to not fail the registration


# Global email service instance
email_service = EmailService()
