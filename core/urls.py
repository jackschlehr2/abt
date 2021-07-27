from django.urls import path, include
from .views import (
    ItemDetailView,
    HomeView,
    OrderSummaryView,
    add_to_cart,
    remove_from_cart,
    remove_single_item_from_cart,
    stripe_webhook,
    create_checkout_session,
    ProductsView,
    AboutView,
    get_inventory
)

app_name = 'core'

urlpatterns = [
    path('', HomeView.as_view(), name="home"),
    path('products-page/', ProductsView.as_view(), name='products-page'),
    path('about/', AboutView.as_view(), name='about'),
    path('order-summary/', OrderSummaryView.as_view(), name='order-summary'),
    path('product/<slug>/', ItemDetailView.as_view(), name="product"),
    path('add-to-cart/<slug>/<size>', add_to_cart, name="add-to-cart"),
    path('remove-from-cart/<slug>/', remove_from_cart, name="remove-from-cart"),
    path('remove-single-item-from-cart/<slug>/',
         remove_single_item_from_cart, name="remove-single-item-from-cart"),
    path('create-checkout-session',
         create_checkout_session, name="create-checkout-session"),
    path('webhooks/stripe/', stripe_webhook, name='stripe-webhook'),
    path('get-inventory/<slug>', get_inventory, name='get-inventory')

]
