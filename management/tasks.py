from celery import shared_task
from django.utils.timezone import now
from django.core.mail import send_mail
from django.conf import settings


@shared_task
def generate_and_email_invoices():
    today = now()
    from management.models import UserInvoice

    if today.day == 1:  # Beginning of the month
        recurring_invoices = UserInvoice.objects.filter(recurring=True)
        for invoice in recurring_invoices:
            email_invoice(invoice)


def email_invoice(invoice):
    subject = f"Invoice {invoice.id}"
    message = f"Hello {invoice.user.first_name},\n\n"
    message += f"Here is your invoice:\n\n"

    for item in invoice.bill_items.all():
        message += f"- {item.title}: ${item.amount}\n"

    message += f"\nTotal: ${invoice.total_amount}\n\n"
    message += "Thank you for your business!"

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [invoice.user.email],
        fail_silently=False,
    )


@shared_task
def email_invoice_task(invoice_id):
    from management.models import UserInvoice

    try:
        invoice = UserInvoice.objects.prefetch_related("bill_items").get(id=invoice_id)
        subject = f"Invoice {invoice.id}"
        message = f"Hello {invoice.user.first_name},\n\n"
        message += f"Here is your invoice:\n\n"

        for item in invoice.bill_items.all():
            message += f"- {item.title}: ${item.amount}\n"

        message += f"\nTotal: ${invoice.total_amount}\n\n"
        message += "Thank you for your business!"

        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [invoice.user.email],
            fail_silently=False,
        )
    except UserInvoice.DoesNotExist:
        # Handle the missing invoice gracefully
        pass
