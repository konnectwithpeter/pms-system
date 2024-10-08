from unfold.admin import ModelAdmin
from django.contrib import admin
from base.models import *
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.utils.safestring import mark_safe


class TenantProfileAdmin(ModelAdmin):

    list_display = (
        "user",
        "estate",
        "block_unit",
        "rent_status",
        "pending_bill",
        "total_billed",
        "total_paid",
        "invoice_dropdown",  # Add this line
    )

    list_filter = ("rent_status", "property__estate")
    search_fields = ("user__email", "property__unit", "property__block")
    ordering = ("-move_in_date",)

    # Specify fields that should be read-only in the admin form
    readonly_fields = ("move_in_date", "total_billed", "total_paid")

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "user",
                    "property",
                    "move_in_date",
                    "move_out_date",
                )
            },
        ),
        (
            "Billing Information",
            {
                "fields": (
                    "pending_bill",
                    "total_billed",
                    "total_paid",
                    "rent_status",
                ),
            },
        ),
    )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.select_related("user", "property")
        return queryset

    def estate(self, obj):
        return obj.property.estate

    def block_unit(self, obj):
        return f"{obj.property.block} [{obj.property.unit}]"

    def total_billed(self, obj):
        return obj.calculate_total_billed()  # Replace with actual calculation logic

    def total_paid(self, obj):
        return obj.calculate_total_paid()  # Replace with actual logic

    def invoice_dropdown(self, obj):
        # Query both RentInvoice and WaterBillInvoice related to this tenant
        rent_invoices = RentInvoice.objects.filter(recipient=obj.user)

        # Combine both invoice types
        invoices_html = "<table style='width:100%; border-collapse: collapse; border: 1px solid #ddd;'>"
        invoices_html += "<tr><th>Invoice Type</th><th>Amount</th><th>Issued Date</th><th>Status</th></tr>"

        for invoice in rent_invoices:
            invoice_type = "Rent"
            invoices_html += "<tr>"
            invoices_html += f"<td>{invoice_type}</td>"
            invoices_html += f"<td>{invoice.total_amount}</td>"
            invoices_html += f"<td>{invoice.created_at}</td>"
            invoices_html += f"<td>{'Paid' if invoice.paid else 'Pending'}</td>"
            invoices_html += "</tr>"

        invoices_html += "</table>"

        return mark_safe(
            f"""
        <button class="btn btn-secondary" onclick="openModal('{invoices_html.replace("'", "\\'").replace('\n', '')}');">View Invoices</button>

        <div class="modal" id="invoiceModal" style="display:none;">
            <div class="modal-content" style="padding: 20px;">
                <span class="close" onclick="closeModal();">&times;</span>
                <h2>Invoices</h2>
                <div id="invoiceTable" style="overflow-x:auto;"></div>
            </div>
        </div>

        <script>
            function openModal(invoicesHtml) {{
                document.getElementById('invoiceTable').innerHTML = invoicesHtml;
                document.getElementById('invoiceModal').style.display = 'block';
            }}
            function closeModal() {{
                document.getElementById('invoiceModal').style.display = 'none';
            }}
            window.onclick = function(event) {{
                if (event.target === document.getElementById('invoiceModal')) {{
                    closeModal();
                }}
            }};
        </script>
        """
        )

        invoice_dropdown.short_description = (
            "Invoices"  # Add a short description for the dropdown
        )


# Register the TenantProfileAdmin with the TenantProfile model
admin.site.register(TenantProfile, TenantProfileAdmin)
