from django.urls import path, include
from .views import (
    ItemDetailView,
    CheckoutView,
    HomeView,
    OrderSummaryView,
    add_to_cart,
    remove_from_cart,
    remove_single_item_from_cart,
    PaymentView,
    stripe_webhook,
    StripeIntentView
)

app_name = 'core'

urlpatterns = [
    path('', HomeView.as_view(), name="home"),
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    path('order-summary/', OrderSummaryView.as_view(), name='order-summary'),
    path('product/<slug>/', ItemDetailView.as_view(), name="product"),
    path('add-to-cart/<slug>/', add_to_cart, name="add-to-cart"),
    path('remove-from-cart/<slug>/', remove_from_cart, name="remove-from-cart"),
    path('remove-single-item-from-cart/<slug>/',
         remove_single_item_from_cart, name="remove-single-item-from-cart"),
    path('payment/', PaymentView.as_view(), name='payment'),
    path('create-payment-intent/',
         StripeIntentView.as_view(), name='create-payment-intent'),
    path('webhooks/stripe/', stripe_webhook, name='stripe-webhook')


]
