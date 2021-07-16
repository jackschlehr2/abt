import stripe

from django.shortcuts import render, get_object_or_404, redirect
from django.core.exceptions import ObjectDoesNotExist
from django.contrib import messages
from django.views.generic import ListView, DetailView, View
from .models import Item, Order, OrderItem, Address, Payment, UserProfile
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import CheckoutForm
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


stripe.api_key = settings.STRIPE_SECRET_KEY


def products(requests):
    context = {
        'items': Item.objects.all()
    }
    return render(request, "products.html", context)


def is_valid_form(values):
    valid = True
    for field in values:
        if field == '':
            valid = False
    return valid


class CheckoutView(View):
    def get(self, *args, **kwargs):
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            form = CheckoutForm()
            context = {
                'form': form,
                'order': order,
            }

            shipping_address_qs = Address.objects.filter(
                user=self.request.user,
                address_type='S',
            )
            if shipping_address_qs.exists():
                context.update(
                    {'default_shipping_address': shipping_address_qs[0]})

            billing_address_qs = Address.objects.filter(
                user=self.request.user,
                address_type='B',
            )
            if billing_address_qs.exists():
                context.update(
                    {'default_billing_address': billing_address_qs[0]})
            return render(self.request, "checkout.html", context)
        except ObjectDoesNotExist:
            messages.info(self.request, "You do not have an active order")
            return redirect("core:checkout")

    def post(self, *args, **kwargs):
        form = CheckoutForm(self.request.POST or None)
        try:
            if not form.is_valid():
                print("err form")
            order = Order.objects.get(user=self.request.user, ordered=False)
            shipping_address1 = form.cleaned_data.get(
                'shipping_address')
            shipping_address2 = form.cleaned_data.get(
                'shipping_address2')
            shipping_zip = form.cleaned_data.get('shipping_zip')

            if is_valid_form([shipping_address1, shipping_zip]):
                print('valid')
                shipping_address = Address(
                    user=self.request.user,
                    street_address=shipping_address1,
                    apartment_address=shipping_address2,
                    zip=shipping_zip,
                    address_type='S'
                )
                shipping_address.save()

                order.shipping_address = shipping_address
                order.save()

                set_default_shipping = form.cleaned_data.get(
                    'set_default_shipping')
                if set_default_shipping:
                    shipping_address.default = True
                    shipping_address.save()

            else:
                messages.info(
                    self.request, "Please fill in the required shipping address fields")

            same_billing_address = form.cleaned_data.get(
                'same_billing_address')

            if same_billing_address:
                billing_address = shipping_address
                billing_address.pk = None
                billing_address.save()
                billing_address.address_type = 'B'
                billing_address.save()
                order.billing_address = billing_address
                order.save()

            else:
                print("User is entering a new billing address")
                billing_address1 = form.cleaned_data.get(
                    'billing_address')
                billing_address2 = form.cleaned_data.get(
                    'billing_address2')
                billing_zip = form.cleaned_data.get('billing_zip')

                if is_valid_form([billing_address1, billing_country, billing_zip]):
                    billing_address = Address(
                        user=self.request.user,
                        street_address=billing_address1,
                        apartment_address=billing_address2,
                        zip=billing_zip,
                        address_type='B'
                    )
                    billing_address.save()

                    order.billing_address = billing_address
                    order.save()

                else:
                    messages.info(
                        self.request, "Please fill in the required billing address fields")

            return redirect('core:payment')

        except ObjectDoesNotExist:
            messages.warning(self.request, "You do not have an active order")
            return redirect("core:order-summary")


class PaymentView(View):
    model = Item
    template_name = "payment.html"

    def get(self, *args, **kwargs):
        order = Order.objects.get(user=self.request.user, ordered=False)
        if order.billing_address:
            context = {
                'order': order,
                'DISPLAY_COUPON_FORM': False,
                'STRIPE_PUBLIC_KEY': settings.STRIPE_PUBLIC_KEY
            }
            userprofile = self.request.user.userprofile
            return render(self.request, "payment.html", context)
        else:
            messages.warning(
                self.request, "You have not added a billing address")
            return redirect("core:checkout")

        return render(self.request, "payment.html")

    # def post(self, *args, **kwargs):
    #     # TODO fix this
    #     YOUR_DOMAIN = "http://127.0.0.1:8000/"
    #     product_id = self.kwargs["pk"]
    #     product = Product.objects.get(id=product_id)
    #     order = Order.objects.get(user=self.request.user, ordered=False)
    #     form = PaymentForm(self.request.POST)
    #     userprofile = UserProfile.objects.get(user=self.request.user)
    #     checkout_session = stripe.checkout.Session.create(
    #         payment_method_types=['card'],
    #         line_items=[
    #             {
    #                 'price_data': {
    #                     'currency': 'usd',
    #                     'unit_amount': 2000,
    #                     'product_data': {
    #                         'name': 'Stubborn Attachments',
    #                         'images': ['https://i.imgur.com/EHyR2nP.png'],
    #                     },
    #                 },
    #                 'quantity': 1,
    #             },
    #         ],
    #         metadata={
    #             "product_id": product.id
    #         },
    #         mode='payment',
    #         success_url=YOUR_DOMAIN + '/success.html',
    #         cancel_url=YOUR_DOMAIN + '/cancel.html',
    #     )

    #     return JsonResponse({
    #         'id': checkout_session.id,
    #     })


class StripeIntentView(View):
    def post(self, request, *args, **kwargs):
        try:
            req_json = json.loads(request.body)
            customer = stripe.Customer.create(email=req_json['email'])
            product_id = self.kwargs["pk"]
            product = Product.objects.get(id=product_id)
            intent = stripe.PaymentIntent.create(
                amount=product.price,
                currency='usd',
                customer=customer['id'],
                metadata={
                    "product_id": product.id
                }
            )
            return JsonResponse({
                'clientSecret': intent['client_secret']
            })
        except Exception as e:
            return JsonResponse({'error': str(e)})


@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        # Invalid payload
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return HttpResponse(status=400)

    # Handle the checkout.session.completed event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']

        customer_email = session["customer_details"]["email"]
        product_id = session["metadata"]["product_id"]

        product = Product.objects.get(id=product_id)

        send_mail(
            subject="Here is your product",
            message=f"Thanks for your purchase. Here is the product you ordered. The URL is {product.url}",
            recipient_list=[customer_email],
            from_email="matt@test.com"
        )

        # TODO - decide whether you want to send the file or the URL

    elif event["type"] == "payment_intent.succeeded":
        intent = event['data']['object']

        stripe_customer_id = intent["customer"]
        stripe_customer = stripe.Customer.retrieve(stripe_customer_id)

        customer_email = stripe_customer['email']
        product_id = intent["metadata"]["product_id"]

        product = Product.objects.get(id=product_id)

        send_mail(
            subject="Here is your product",
            message=f"Thanks for your purchase. Here is the product you ordered. The URL is {product.url}",
            recipient_list=[customer_email],
            from_email="matt@test.com"
        )

    return HttpResponse(status=200)


class HomeView(ListView):
    model = Item
    paginate_by = 10
    template_name = 'home.html'


class ItemDetailView(DetailView):
    model = Item
    template_name = 'product.html'


class OrderSummaryView(LoginRequiredMixin, View):
    def get(self, *arg, **kwargs):
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            context = {
                'object': order
            }
            return render(self.request, 'order_summary.html', context)
        except ObjectDoesNotExist:
            messages.error(self.request, "You do not have an active orderr")
            return redirect("/")


@login_required
def add_to_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_item, created = OrderItem.objects.get_or_create(
        item=item,
        user=request.user,
        ordered=False
    )
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        # check if the order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item.quantity += 1
            order_item.save()
            messages.info(request, "This item quantity was updated.")
            return redirect("core:order-summary")
        else:
            order.items.add(order_item)
            messages.info(request, "This item was added to your cart.")
            return redirect("core:order-summary")
    else:
        ordered_date = timezone.now()
        order = Order.objects.create(
            user=request.user, ordered_date=ordered_date)
        order.items.add(order_item)
        messages.info(request, "This item was added to your cart.")
        return redirect("core:order-summary")


@login_required
def remove_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(
                user=request.user, item=item, ordered=False)[0]
            order.items.remove(order_item)
            messages.info(request, "this item was removed from your cart")
            return redirect("core:order-summary", slug=slug)
        else:
            messages.info(request, "this item was was not in your cart")
            return redirect("core:product", slug=slug)
    else:
        messages.info(request, "You do not have an active order")
        return redirect("core:product", slug=slug)


@login_required
def remove_single_item_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(
                user=request.user, item=item, ordered=False)[0]
            order_item.quantity -= 1
            order_item.save()
            messages.info(request, "this item quantity was updated")
            return redirect("core:order-summary")
        else:
            messages.info(request, "this item was was not in your cart")
            return redirect("core:product", slug=slug)
    else:
        messages.info(request, "You do not have an active order")
        return redirect("core:product", slug=slug)
