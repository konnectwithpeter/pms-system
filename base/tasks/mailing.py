# In base/tasks.py
from celery import shared_task
from django.utils import timezone
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.mail import send_mail, EmailMessage
from django.conf import settings
from django.contrib.auth import get_user_model  # Import this instead of User
from io import BytesIO
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from base.models import (
    TenantProfile,
    Notification,
    WaterMeterReading,
    RentInvoice,
    WaterPrice,
)
from django.core.files.base import ContentFile
from datetime import datetime


User = get_user_model()  # Use get_user_model() to fetch the User model


@shared_task
def send_email_task(recipient_list, template_name, context):
    """
    Task to send an email asynchronously.

    Args:
    - subject: Subject of the email.
    - recipient_list: List of recipient email addresses.
    - template_name: The email template to use.
    - context: Context data to render the template.
    """

    print("send email...")
    # Render the email content
    message = render_to_string(template_name, context)
    subject = "Welcome to Our Property Management System"
    # Send the email
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,  # Set this in your settings.py
        recipient_list,
        fail_silently=False,
    )


@shared_task
def send_password_reset_email(recipient_list, html_message):
    try:
        subject = "Password Reset"
        plain_message = "Please use a modern email client to view this email."  # Plain text fallback
        # Send the email
        # Send the email with HTML content
        send_mail(
            subject,
            plain_message,  # Plain text message
            settings.DEFAULT_FROM_EMAIL,
            recipient_list,
            fail_silently=False,
            html_message=html_message,  # HTML content here
        )
        print("Password reset email sent successfully.")
    except User.DoesNotExist:
        print("User does not exist.")
    except Exception as e:
        print(f"Error sending email: {e}")


@shared_task
def generate_invoice(tenant_id, previous_reading, current_reading, reading_date):
    print("Generating invoice...")

    try:
        tenant = TenantProfile.objects.get(id=tenant_id)
        water_price = WaterPrice.objects.filter()[0].price_per_unit

        # Get today's date
        today = timezone.now().date()

        # Always set the billing period end to the 10th of the current month
        billing_period_end = today.replace(day=10)

        consumption = current_reading - previous_reading
        water_bill = consumption * water_price

        # Create the invoice record
        invoice = RentInvoice.objects.create(
            recipient=tenant.user,
            monthly_rent=tenant.property.rent_price,
            previous_water_reading=previous_reading,
            current_water_reading=current_reading,
            reading_date=reading_date,
            water_consumption=consumption,
            total_amount=tenant.pending_bill,
            water_bill=water_bill,
            billing_period_end=billing_period_end,
            arrears=tenant.arrears,
            price_per_unit=water_price,
        )

        invoice.save()

        generate_invoice_pdf(tenant, invoice)

        notification = Notification.objects.create(
            recipient=tenant.user,
            title="Monthly Rent and Utility Invoice",
            message=f"Reminder: Your monthly rent of KES {tenant.pending_bill} and water bill of KES {water_bill} are due by {billing_period_end}. Please make the payment to avoid late fees. Thank you!",
            notification_type="Info",
            # Using the custom User model for sender and recipient
            sender=User.objects.filter(user_type="admin")[0],
        )

        notification.save()

    except TenantProfile.DoesNotExist:
        print(f"TenantProfile with id {tenant_id} does not exist.")


def generate_invoice_pdf(tenant, invoice):
    # Render the invoice HTML template
    print("invoice", invoice)
    template = get_template(
        "base/sample_invoice.html"
    )  # Replace with your actual template

    context = {
        "unit": tenant.property.unit,
        "invoice_date": invoice.billing_period_start,
        "due_date": invoice.billing_period_end,
        "previous_reading": invoice.previous_water_reading,
        "current_reading": invoice.current_water_reading,
        "consumption": invoice.water_consumption,
        "price_per_unit": invoice.price_per_unit,
        "water_bill": invoice.water_bill,
        "monthly_rent": invoice.monthly_rent,
        "arrears": invoice.arrears,
        "total_amount": invoice.total_amount,
        "invoice_month_year": datetime.now().strftime("%B %Y"),
    }
    html = template.render(context)

    # Create a PDF from the rendered HTML
    pdf_file = BytesIO()
    pisa_status = pisa.CreatePDF(html, dest=pdf_file)

    if pisa_status.err:
        print(f"Error generating PDF for {tenant.user.email}")
        return None

    pdf_file.seek(0)

    # Attach the PDF to the tenant's profile or email it
    filename = f"Invoice_{tenant.user.id}_{timezone.now().date()}.pdf"

    invoice.file.save(filename, ContentFile(pdf_file.getvalue()))
    invoice.save()
    print("Invoice generated and saved successfully.")
    pdf_file.seek(0)  # Reset stream after saving

    # Option 2: Send the PDF via email
    send_invoice_email(tenant.id, filename, pdf_file.read())


@shared_task
def send_invoice_email(tenant_id, filename, pdf_data):
    tenant = TenantProfile.objects.get(id=tenant_id)  # Retrieve tenant instance

    subject = "Your Monthly Rent Invoice"
    message = (
        f"Dear {tenant.user.first_name},\n\n"
        f"Please find attached your rent invoice for this month. Your total due is KES {tenant.pending_bill}.\n"
        f"Thank you for being a valued tenant.\n"
    )
    email = EmailMessage(
        subject, message, settings.DEFAULT_FROM_EMAIL, [tenant.user.email]
    )
    print(f"Attempting to send email to {tenant.user.email}...")

    # Attach the PDF
    email.attach(filename, pdf_data, "application/pdf")

    try:
        email.send()
        print(f"Email sent to {tenant.user.email} successfully.")
    except Exception as e:
        print(f"Failed to send email to {tenant.user.email}. Error: {e}")


@shared_task
def send_reminders():
    pass
