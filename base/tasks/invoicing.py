from management.models import *
from celery import shared_task
from django.utils import timezone

from django.core.mail import send_mail, EmailMessage
from django.conf import settings
from django.contrib.auth import get_user_model  # Import this instead of User
from io import BytesIO
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa

from django.core.files.base import ContentFile
from datetime import datetime



@shared_task
def generate_utility_invoice(
    tenant_id, previous_reading, current_reading, reading_date
):
    print("Generating invoice...")

    try:
        tenant = Tenant.objects.get(id=tenant_id)
        water_price = WaterUnitPrice.objects.filter()[0].price_per_unit

        # Get today's date
        today = timezone.now().date()

        # Always set the billing period end to the 10th of the current month
        due_date = today.replace(day=10)

        consumption = current_reading - previous_reading
        water_bill = consumption * water_price

        # Create the invoice record
        invoice = TenantInvoice.objects.create(
            tenant=tenant,
            property=tenant.property,
            previous_water_reading=previous_reading,
            current_water_reading=current_reading,
            reading_date=reading_date,
            water_consumption=consumption,
            amount=water_bill,
            due_date=due_date,
            price_per_unit=water_price,
        )

        invoice.save()

        total_invoices = TenantInvoice.objects.filter(tenant=tenant).aggregate(
            total=Sum("amount")
        )["total"]
       
        tenant.total_billed = total_invoices
        tenant.save()

        generate_invoice_pdf(tenant, invoice)

    except Tenant.DoesNotExist:
        print(f"Tenant with id {tenant_id} does not exist.")


def generate_invoice_pdf(tenant, invoice):
    print("generating invoice pdf")
    # Render the invoice HTML template
    print("invoice", invoice)
    template = get_template(
        "base/utility_invoice.html"
    )  # Replace with your actual template

    context = {
        "unit": tenant.property.unit,
        "invoice_date": invoice.reading_date,
        "due_date": invoice.due_date,
        "previous_reading": invoice.previous_water_reading,
        "current_reading": invoice.current_water_reading,
        "consumption": invoice.water_consumption,
        "price_per_unit": invoice.price_per_unit,
        "water_bill": float(invoice.amount),
        "total_amount": float(invoice.amount),
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
    tenant = Tenant.objects.get(id=tenant_id)  # Retrieve tenant instance

    subject = "Your Monthly Water Bill Invoice"
    message = (
        f"Dear {tenant.user.first_name},\n\n"
        f"Please find attached your water bill invoice for this month. Your total due is KES {tenant.pending_bill}.\n"
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
