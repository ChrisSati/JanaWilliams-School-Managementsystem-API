# urls.py
from django.urls import path
from .views import RequestResetCodeView, VerifyResetCodeView, SetNewPasswordView

urlpatterns = [
    path('request-reset-code/', RequestResetCodeView.as_view(), name='request-reset-code'),
    path('verify-reset-code/', VerifyResetCodeView.as_view(), name='verify-reset-code'),
    path('set-new-password/', SetNewPasswordView.as_view(), name='set-new-password'),
]
