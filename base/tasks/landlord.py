from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils.timezone import now
from datetime import timedelta
from io import BytesIO
from reportlab.pdfgen import canvas
from base.models import LandlordProfile, ServiceFeeInvoice
from celery import shared_task
import time


@shared_task
def print_numbers():
    for i in range(1, 11):
        print(f"Number: {i}")


# @shared_task
# def generate_service_fee_invoices():
#     landlords = LandlordProfile.objects.all()
#     for landlord in landlords:
#         # Get the total number of units the landlord owns
#         total_units = landlord.properties.count()
#         amount = total_units * 4000  # 4000 per unit
        
#         # Create a new service fee invoice
#         invoice = ServiceFeeInvoice.objects.create(
#             landlord=landlord,
#             total_units=total_units,
#             amount=amount,
#             due_date=now() + timedelta(days=30),  # Set due date 30 days later
#         )
        
#         # Generate PDF
#         pdf_content = generate_invoice_pdf(landlord, invoice)
#         pdf_filename = f"service_fee_invoice_{landlord.user.email}_{now().strftime('%Y-%m-%d')}.pdf"
#         invoice.file.save(pdf_filename, pdf_content)
        
#         # Update total billed
#         landlord.total_billed += amount
#         landlord.save()
        
#         # Send the email
#         send_invoice_email(landlord.user.email, invoice, pdf_filename)
        
#     return "Service fee invoices generated and sent."

# ### 2. Generate PDF (`utils.py`)
# def generate_invoice_pdf(landlord, invoice):
#     buffer = BytesIO()
#     p = canvas.Canvas(buffer)
    
#     # Write content to the PDF
#     p.drawString(100, 750, f"Service Fee Invoice for {landlord.user.first_name} {landlord.user.last_name}")
#     p.drawString(100, 720, f"Total Units: {invoice.total_units}")
#     p.drawString(100, 690, f"Amount Due: KES {invoice.amount}")
#     p.drawString(100, 660, f"Due Date: {invoice.due_date.strftime('%Y-%m-%d')}")
    
#     # Finalize the PDF
#     p.showPage()
#     p.save()
    
#     buffer.seek(0)
#     return buffer

# ### 3. Send Email (`utils.py`)
# from django.core.mail import EmailMessage

# def send_invoice_email(email, invoice, pdf_filename):
#     subject = f"Service Fee Invoice - {invoice.issued_date.strftime('%Y-%m-%d')}"
#     message = render_to_string('email/invoice_email.html', {'invoice': invoice})
#     email_message = EmailMessage(subject, message, to=[email])
    
#     # Attach the PDF
#     email_message.attach(pdf_filename, invoice.file.read(), 'application/pdf')
    
#     # Send the email
#     email_message.send()


