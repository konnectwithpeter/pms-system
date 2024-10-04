import factory
from faker import Faker
from .models import User, Property, MaintenanceRequest, Payment

faker = Faker()

class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    email = factory.LazyAttribute(lambda _: faker.email())
    first_name = factory.LazyAttribute(lambda _: faker.first_name())
    last_name = factory.LazyAttribute(lambda _: faker.last_name())
    user_type = factory.LazyAttribute(lambda _: faker.random_element(elements=('landlord', 'tenant', 'admin')))
    profile_picture = factory.django.ImageField(color='blue')

class PropertyFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Property

    landlord = factory.SubFactory(UserFactory)
    title = factory.LazyAttribute(lambda _: faker.sentence(nb_words=6))
    image1 = factory.django.ImageField(color='red')
    description = factory.LazyAttribute(lambda _: faker.text(max_nb_chars=200))
    address = factory.LazyAttribute(lambda _: faker.address())
    rent_price = factory.LazyAttribute(lambda _: faker.random_number(digits=5))
    available = factory.LazyAttribute(lambda _: faker.boolean())
    created_at = factory.LazyAttribute(lambda _: faker.date_time_this_year())
    updated_at = factory.LazyAttribute(lambda _: faker.date_time_this_year())

class MaintenanceRequestFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = MaintenanceRequest

    property = factory.SubFactory(PropertyFactory)
    tenant = factory.SubFactory(UserFactory)
    description = factory.LazyAttribute(lambda _: faker.text(max_nb_chars=200))
    status = factory.LazyAttribute(lambda _: faker.random_element(elements=('Pending', 'In Progress', 'Resolved')))
    submitted_at = factory.LazyAttribute(lambda _: faker.date_time_this_year())

class PaymentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Payment

    property = factory.SubFactory(PropertyFactory)
    tenant = factory.SubFactory(UserFactory)
    amount = factory.LazyAttribute(lambda _: faker.random_number(digits=5))
    payment_date = factory.LazyAttribute(lambda _: faker.date_time_this_year())
    status = factory.LazyAttribute(lambda _: faker.random_element(elements=('Paid', 'Pending', 'Failed')))
