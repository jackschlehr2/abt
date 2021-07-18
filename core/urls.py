from django.urls import path, include
from .views import (
    ItemDetailView,
    HomeView,
    OrderSummaryView,
    add_to_cart,
    remove_from_cart,
    remove_single_item_from_cart,
    stripe_webhook,
    create_checkout_session
)

app_name = 'core'

urlpatterns = [
    path('', HomeView.as_view(), name="home"),
    path('order-summary/', OrderSummaryView.as_view(), name='order-summary'),
    path('product/<slug>/', ItemDetailView.as_view(), name="product"),
    path('add-to-cart/<slug>/', add_to_cart, name="add-to-cart"),
    path('remove-from-cart/<slug>/', remove_from_cart, name="remove-from-cart"),
    path('remove-single-item-from-cart/<slug>/',
         remove_single_item_from_cart, name="remove-single-item-from-cart"),
    path('create-checkout-session',
         create_checkout_session, name="create-checkout-session"),
    path('webhooks/stripe/', stripe_webhook, name='stripe-webhook')


]
