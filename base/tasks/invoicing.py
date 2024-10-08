

def generate_rent_invoices():
    tenants = Tenant.objects.all()
    for tenant in tenants:
        rent_amount = tenant.rented_property.rent_amount
        RentInvoice.objects.create(
            tenant=tenant,
            property=tenant.rented_property,
            amount=rent_amount,
            due_date=timezone.now() + timedelta(days=30)
        )

def generate_service_fee_invoices():
    landlords = Landlord.objects.all()
    for landlord in landlords:
        total_units = Property.objects.filter(landlord=landlord).count()
        service_fee_amount = total_units * 4000
        ServiceFeeInvoice.objects.create(
            landlord=landlord,
            total_units=total_units,
            amount=service_fee_amount,
            due_date=timezone.now() + timedelta(days=30)
        )

def generate_water_bill_invoices():
    tenants = Tenant.objects.all()
    for tenant in tenants:
        water_usage = calculate_water_usage(tenant)
        water_bill_amount = water_usage * 50
        WaterBillInvoice.objects.create(
            tenant=tenant,
            property=tenant.rented_property,
            amount=water_bill_amount,
            meter_reading=water_usage,
            due_date=timezone.now() + timedelta(days=30)
        )
