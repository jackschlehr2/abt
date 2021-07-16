from django import forms
from django_countries.fields import CountryField


class CheckoutForm(forms.Form):
    shipping_address = forms.CharField(required=False)
    shipping_address2 = forms.CharField(required=False)

    shipping_zip = forms.CharField(required=False)

    billing_address = forms.CharField(required=False)
    billing_address2 = forms.CharField(required=False)

    billing_zip = forms.CharField(required=False)

    same_billing_address = forms.BooleanField(required=False)
