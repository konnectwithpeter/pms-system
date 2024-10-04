import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime
from base.models import *
import base64
import json
from django_daraja.mpesa.core import MpesaClient
# Replace with your BusinessShortCode and passkey
BUSINESS_SHORT_CODE = "174379"
PASSKEY = "bfb279f29b9bdbcf158e97dd71a467cd2e0c893059b107f4e6b1a"
CALLBACK_URL = "https://yourdomain.com/mpesa-callback/"  # Your public callback URL


from django.http import HttpResponsePermanentRedirect, HttpResponse, JsonResponse


@csrf_exempt
def index(request):
    print("Processing transaction...")

    # Parse JSON data from the request body
    data = json.loads(request.body)
    
    try:
        invoice = RentInvoice.objects.get(id=data.get("invoice_id"))
    except RentInvoice.DoesNotExist:
        return JsonResponse({"error": "Invoice not found"}, status=404)

    phone_number = data.get("phone_number")
    amount = int(invoice.total_amount)  # Ensure the amount is the invoice total

    # Create the transaction record (status is pending initially)
    transaction = Transaction.objects.create(
        invoice=invoice,
        phone_number=phone_number,
        amount=amount,
        transaction_status="pending"
    )

    # Initialize MPESA client and make the payment request
    cl = MpesaClient()
    account_reference = 'reference'
    transaction_desc = 'Rent Payment'
    callback_url = 'https://your-callback-url.com'  # Update with your callback URL

    response = cl.stk_push(phone_number, amount, account_reference, transaction_desc, callback_url)
    
    print(response.json())
    # Assume `response` contains a success or failure status
    if response.json()['CustomerMessage'] == 'Success. Request accepted for processing':
        transaction.transaction_status = "success"
        transaction.transaction_id = response.json()['MerchantRequestID']
        transaction.save()
        
        # Process payment and update the invoice status
        return JsonResponse({"message": "Payment successful", "transaction_id": transaction.transaction_id})
    
    else:
        transaction.transaction_status = "failed"
        transaction.save()
        return JsonResponse({"error": "Payment failed"}, status=400)