import os
import stripe
from django.shortcuts import render, get_object_or_404, redirect
from django.core.exceptions import ObjectDoesNotExist
from django.views.generic import ListView, DetailView, View
from .models import Item, Order, OrderItem, UserProfile
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.conf import settings
from django.contrib import messages
from django.http import JsonResponse


def products(requests):
    context = {
        'items': Item.objects.all()
    }
    return render(request, "products.html", context)


def create_checkout_session(request):
    try:
        stripe.api_key = settings.STRIPE_SECRET_KEY
        order = Order.objects.get(user=request.user)
    except Exception as e:
        print(e)

    DEVELOPMENT_MODE = os.getenv("DEVELOPMENT_MODE", "False") == "True"
    if DEVELOPMENT_MODE == True:
        YOUR_DOMAIN = 'http://127.0.0.1:8000'
        ship_rate = 'shr_1JDwVPFVzms5crHWCjcYKk16'
        tax_rate = 'txr_1JDwWeFVzms5crHWOIT4FZNx'
    else:
        YOUR_DOMAIN = 'https://' + os.getenv("DJANGO_ALLOWED_HOSTS")
        ship_rate = 'shr_1JLLNAFVzms5crHWPyOmJdTf'
        tax_rate = 'txr_1JI5ClFVzms5crHWRYVctqwo'
    try:

        line_items = []
        for order_item in order.get_items():
            line_items.append({
                'price_data': {
                    'currency': 'usd',
                    'unit_amount': int(order_item.get_item_price())*100,
                    'product_data': {
                        'name': order_item.get_name(),
                    },
                },
                'tax_rates': [tax_rate],
                'quantity': order_item.get_quantity(),
            })

        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            shipping_rates=[ship_rate],
            shipping_address_collection={
                'allowed_countries': ['US'],
            },
            line_items=line_items,
            mode='payment',
            success_url=YOUR_DOMAIN + '/',
            cancel_url=YOUR_DOMAIN + '/order-summary',
        )
        return redirect(checkout_session.url, code=303)
    except Exception as e:
        print(e)
        messages.info(request, "Stripe Error has occurred")
        return redirect("/")


class HomeView(ListView):
    model = Item
    template_name = 'home.html'


class ProductsView(ListView):
    model = Item
    template_name = 'product_page.html'


class ItemDetailView(DetailView):
    model = Item
    template_name = 'product.html'

    def post(self, *args, **kwargs):
        if self.request.is_ajax and self.request.method == "POST":
            size = self.request.POST.get('size')
            slug = kwargs['slug']
            success = add_to_cart(self.request, slug, size)
            if not success:
                return JsonResponse({"error": ""}, status=200)
            return JsonResponse({"success": ""}, status=200)


class AboutView(ListView):
    model = Item
    template_name = 'about.html'


class OrderSummaryView(LoginRequiredMixin, View):
    def get(self, *arg, **kwargs):
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            context = {'object': order}
            return render(self.request, 'order_summary.html', context)
        except ObjectDoesNotExist:
            return redirect("/")

    def get_order(user):
        return Order.objects.get(user=user, ordered=False)


def get_inventory(request, slug):
    if request.is_ajax and request.method == "GET":
        item = get_object_or_404(Item, slug=slug)
        selected_size = request.GET.get("size", None)
        if in_stock(item, selected_size):
            return JsonResponse({"in_stock": True}, status=200)
        else:
            return JsonResponse({"in_stock": False}, status=200)
    return JsonResponse({}, status=400)


def in_stock(item, selected_size, quantity=1):
    if selected_size == None:
        selected_size = -1
    else:
        selected_size = int(selected_size)
    if selected_size == 0 and item.size_small >= quantity:
        return True
    elif selected_size == 1 and item.size_medium >= quantity:
        return True
    elif selected_size == 2 and item.size_large >= quantity:
        return True
    elif selected_size == 3 and item.size_extra_large >= quantity:
        return True
    return False


@ login_required
def add_to_cart(request, slug, size):
    item = get_object_or_404(Item, slug=slug)
    order_item, created = OrderItem.objects.get_or_create(
        item=item,
        user=request.user,
        ordered=False,
        selected_size=size
    )
    if not created and in_stock(item, size, order_item.quantity+1):
        success = change_quantity(request, slug, size, 1)
    elif created and in_stock(item, size, 1):
        success = change_quantity(request, slug, size, 1)
    else:
        messages.info(request, "This product has extremely limited quantity")
    return redirect("core:order-summary")


@ login_required
def remove_single_item_from_cart(request, slug, size):
    success = change_quantity(request, slug, size, -1)
    return redirect("core:order-summary")


def change_quantity(request, slug, size, quantity):
    item = get_object_or_404(Item, slug=slug)

    order_item, created = OrderItem.objects.get_or_create(
        item=item,
        user=request.user,
        ordered=False,
        selected_size=size
    )
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        if order.items.filter(item__slug=item.slug, selected_size=size).exists():
            order_item.quantity += quantity
            order_item.save()
            if order_item.quantity <= 0:
                order.items.remove(order_item)
                order_item.delete()
                messages.info(request, "This item was removed from your cart")
            else:
                messages.info(request, "This item quantity was updated")
        else:
            order.items.add(order_item)
            messages.info(request, "This item was added to your order")
    else:
        ordered_date = timezone.now()
        order = Order.objects.create(
            user=request.user, ordered_date=ordered_date)
        order.items.add(order_item)
    return True
