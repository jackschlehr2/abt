from django.urls import path, include
from .views import (
    ItemDetailView,
    HomeView,
    OrderSummaryView,
    add_to_cart,
    remove_single_item_from_cart,
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
    path('remove-single-item-from-cart/<slug>/<size>',
         remove_single_item_from_cart, name="remove-single-item-from-cart"),
    path('create-checkout-session',
         create_checkout_session, name="create-checkout-session"),
    path('get-inventory/<slug>', get_inventory, name='get-inventory')

]
