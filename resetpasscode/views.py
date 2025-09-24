# password_reset/views.py
import logging
import random
from datetime import timedelta
from django.utils import timezone
from django.core.mail import send_mail
from django.contrib.auth.hashers import make_password
from django.core.mail import EmailMultiAlternatives
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from users.models import User
from .models import PasswordResetCode



# Set up logger
logger = logging.getLogger(__name__)

class RequestResetCodeView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        logger.info(f"Received email: {email}")  # Log the received email

        try:
            user = User.objects.get(email=email)
            code = str(random.randint(100000, 999999))

            # Save code to DB
            PasswordResetCode.objects.create(user=user, code=code)

            subject = "Jana Williams Educational Foundation - Password Reset Code"
            to = [user.email]
            from_email = None

            # Plain text fallback for non-HTML clients
            text_content = (
                f"Hi {user.username},\n\n"
                f"Your password reset code is: {code}\n"
                "It will expire in 10 minutes."
            )

            # HTML content with styles for the code
            html_content = f"""
            <html>
             <body>
  <div style="
      background-color: #001f3f; 
      color: white; 
      text-align: center; 
      padding: 15px; 
      font-size: 20px; 
      font-weight: bold;">
    JW - Educational Foundation (Password Reset)
  </div>

  <p style="text-align:left;">Hi {user.username},</p>
  <div style="text-align:center;">
    <p>Your password reset code is:</p>
    <h2 style="
        font-weight: bold; 
        background-color: #f0f0f0; 
        color: #003366;
        padding: 10px; 
        border-radius: 5px;
        display: inline-block;">
      {code}
    </h2>
    <p>This code will expire in 10 minutes. After which you will have to reapply to reset your forgotten Password. Thank you!</p>
  </div>
</body>

            </html>
            """

            email = EmailMultiAlternatives(subject, text_content, from_email, to)
            email.attach_alternative(html_content, "text/html")
            email.send()

            return Response({"message": "Reset code sent to your email."}, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            logger.error(f"User with email {email} does not exist.")  # Log error if user not found
            return Response({"error": "User with this email does not exist."}, status=status.HTTP_400_BAD_REQUEST)

class VerifyResetCodeView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        code = request.data.get("code")

        logger.info(f"Received email: {email} and code: {code}")  # Log received data

        try:
            user = User.objects.get(email=email)
            reset_entry = PasswordResetCode.objects.filter(user=user, code=code).last()

            if not reset_entry:
                logger.error(f"No reset entry found for user {email} with code {code}")
                return Response({"error": "Invalid code."}, status=status.HTTP_400_BAD_REQUEST)

            if timezone.now() - reset_entry.created_at > timedelta(minutes=10):
                logger.error(f"Reset code for {email} expired.")
                return Response({"error": "Code expired."}, status=status.HTTP_400_BAD_REQUEST)

            logger.info(f"Reset code for {email} verified successfully.")
            return Response({"message": "Code verified."}, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            logger.error(f"User with email {email} does not exist.")
            return Response({"error": "Invalid user."}, status=status.HTTP_400_BAD_REQUEST)


class SetNewPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        print(f"Request data: {request.data}")  # Debugging log

        email = request.data.get("email")
        code = request.data.get("code")
        new_password = request.data.get("new_password")

        if not email or not code or not new_password:
            return Response({"error": "Missing email, code, or new password."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
            reset_entry = PasswordResetCode.objects.filter(user=user, code=code).last()

            if not reset_entry:
                return Response({"error": "Invalid code."}, status=status.HTTP_400_BAD_REQUEST)

            if timezone.now() - reset_entry.created_at > timedelta(minutes=10):
                return Response({"error": "Code expired."}, status=status.HTTP_400_BAD_REQUEST)

            user.password = make_password(new_password)
            user.save()

            reset_entry.delete()  # Delete the reset code after use

            return Response({"message": "Password reset successful."}, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response({"error": "Invalid user."}, status=status.HTTP_400_BAD_REQUEST)
