import requests
import json
from django.conf import settings
from datetime import datetime
import hashlib

class AzamPayService:
    @staticmethod
    def generate_auth_token():
        """Generate AzamPay authentication token"""
        url = f"{settings.AZAMPAY_BASE_URL}/api/v1/oauth/token"
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        payload = {
            "appName": settings.AZAMPAY_APP_NAME,
            "clientId": settings.AZAMPAY_CLIENT_ID,
            "clientSecret": settings.AZAMPAY_CLIENT_SECRET
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json().get('accessToken')
        except requests.RequestException as e:
            raise Exception(f"AzamPay auth failed: {str(e)}")

    @staticmethod
    def initiate_payment(amount, phone, reference, callback_url):
        """Initiate mobile payment via AzamPay"""
        token = AzamPayService.generate_auth_token()
        url = f"{settings.AZAMPAY_BASE_URL}/api/v1/Partner/PostCheckout"
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            "amount": str(amount),
            "currencyCode": "TZS",
            "externalId": reference,
            "merchantAccountNumber": settings.AZAMPAY_MERCHANT_ACCOUNT,
            "merchantMobileNumber": settings.AZAMPAY_MERCHANT_PHONE,
            "mobileNumber": phone,
            "otp": "0000",  # For sandbox/testing
            "provider": "Airtel",
            "referenceId": reference,
            "additionalProperties": {
                "paymentDetails": "Product purchase",
                "callbackUrl": callback_url
            }
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise Exception(f"AzamPay payment initiation failed: {str(e)}")

    @staticmethod
    def verify_payment(transaction_id):
        """Verify payment status with AzamPay"""
        token = AzamPayService.generate_auth_token()
        url = f"{settings.AZAMPAY_BASE_URL}/api/v1/Partner/GetTransactionStatus"
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            "referenceId": transaction_id
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise Exception(f"AzamPay verification failed: {str(e)}")