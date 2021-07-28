from django.db import models
from django.db.models.signals import post_save
from django.conf import settings
from django.shortcuts import reverse
from datetime import datetime


CATEGORY_CHOICES = (
    ('S', 'Shirt'),
    ('SW', 'Sport Wear'),
    ('OW', 'Outwear'),
)

LABEL_CHOICES = (
    ('P', 'primary'),
    ('S', 'secondary'),
    ('D', 'danger'),
)

ADDRESS_CHOICES = (
    ('B', 'Billing'),
    ('S', 'Shipping'),
)


class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    stripe_customer_id = models.CharField(max_length=50, blank=True, null=True)
    one_click_purchasing = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username


class Item(models.Model):
    title = models.CharField(max_length=100, default="default")
    price = models.IntegerField(default=100)
    slug = models.SlugField(null=True)
    description = models.TextField(default="Default description")
    size_small = models.IntegerField(default=0)
    size_medium = models.IntegerField(default=0)
    size_large = models.IntegerField(default=0)
    size_extra_large = models.IntegerField(default=0)
    image = models.ImageField(upload_to='static_in_env', blank=True, null=True)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("core:product", kwargs={
            'slug': self.slug
        })

    def get_add_to_cart_url(self):
        return reverse("core:add-to-cart", kwargs={
            'slug': self.slug,
        })

    def get_remove_cart_url(self):
        return reverse("core:remove-from-cart", kwargs={
            'slug': self.slug
        })


class OrderItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE, blank=True, null=True)
    ordered = models.BooleanField(default=False)
    item = models.ForeignKey(
        Item, on_delete=models.CASCADE, blank=True, null=True)
    quantity = models.IntegerField(default=1)
    selected_size = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.quantity} of {self.selected_size} {self.item.title}"

    def get_final_price(self):
        return self.quantity * self.item.price

    def get_item_price(self):
        return self.item.price

    def get_quantity(self):
        return self.quantity

    def get_name(self):
        return self.item.title

    def get_image(self):
        return self.item.image

    def get_size(self):
        switcher = {
            0: 'S',
            1: 'M',
            2: 'L',
            3: 'XL'
        }
        return switcher.get(self.selected_size, "invalid size")


class Order(models.Model):

    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE,  blank=True, null=True)

    items = models.ManyToManyField(OrderItem)
    start_date = models.DateTimeField(auto_now=True, blank=True)
    ordered_date = models.DateTimeField(auto_now=True, blank=True)
    being_delivered = models.BooleanField(default=False)
    received = models.BooleanField(default=False)
    ordered = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username

    def get_sub_total(self):
        total = 0
        for order_item in self.items.all():
            total += order_item.get_final_price()
        return '{:.2f}'.format(total)

    def get_tax(self):
        return '{:.2f}'.format((float(self.get_sub_total())*.07))

    def get_shipping(self):
        return '{:.2f}'.format(8.0)

    def get_total(self):
        return '{:.2f}'.format(float(self.get_sub_total()) + float(self.get_tax()) + float(self.get_shipping()))

    def get_items(self):
        items = []
        for order_item in self.items.all():
            items.append(order_item)
        return items

    def get_number_items(self):
        count = 0
        for order_item in self.items.all():
            count += order_item.get_quantity()
        return count


class Address(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE,  blank=True, null=True)
    street_address = models.CharField(max_length=100)
    apartment_address = models.CharField(max_length=100)
    zip = models.CharField(max_length=100)
    address_type = models.CharField(max_length=1, choices=ADDRESS_CHOICES)

    def __str__(self):
        return self.user.username


class Payment(models.Model):
    stripe_charge_id = models.CharField(max_length=50)
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.SET_NULL, blank=True, null=True)
    amount = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username


def userprofile_receiver(sender, instance, created, *args, **kwargs):
    if created:
        userprofile = UserProfile.objects.create(user=instance)


post_save.connect(userprofile_receiver, sender=settings.AUTH_USER_MODEL)
