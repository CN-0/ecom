from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, UsernameField
from django_countries.widgets import CountrySelectWidget
from django_countries.fields import CountryField
from .models import ShippingDetails


class SignUpForm(UserCreationForm):
    email = forms.EmailField(widget=forms.EmailInput(
        attrs={'class': 'form-control', 'id': 'formLoginRegister-email-example', 'type': 'email', 'required': True}))
    username = UsernameField(
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'id': 'formLoginRegister-username-example', 'type': 'text', 'required': True})
    )
    password1 = forms.CharField(widget=forms.PasswordInput(
        attrs={'class': 'form-control', 'id': 'formLoginRegister-password-example', 'type': 'password', 'required': True}))
    password2 = forms.CharField(widget=forms.PasswordInput(
        attrs={'class': 'form-control', 'id': 'formLoginRegister-password-repeat', 'type': 'password', 'required': True}))

    class Meta:
        model = User
        fields = ('email', 'username', 'password1', 'password2')


class LoginForm(AuthenticationForm):
    username = UsernameField(
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'id': 'formLoginRegister-username', 'type': 'text', 'required': True})
    )
    password = forms.CharField(widget=forms.PasswordInput(
        attrs={'class': 'form-control', 'id': 'formLoginRegister-password', 'type': 'password', 'required': True}))


class CheckoutForm(forms.Form):
    full_name = forms.CharField(max_length=100, label="Full Name", widget=forms.TextInput(
        attrs={'class': 'form-control', 'type': 'text', 'required': True}))
    phone = forms.IntegerField(label="Phone", widget=forms.TextInput(
        attrs={'class': 'form-control', 'required': True}))
    shipping_country = CountryField(
        blank_label='Choose your option').formfield(label="Country",
                                                    required=True, widget=CountrySelectWidget(layout='{widget}', attrs={
                                                        'class': 'mdb-select md-form md-outline'
                                                    }))
    shipping_address1 = forms.CharField(max_length=150, label="Address", widget=forms.TextInput(
        attrs={'class': 'form-control', 'type': 'text', 'required': True, 'placeholder': 'House number and street name'}))
    shipping_address2 = forms.CharField(max_length=150, label="Address", widget=forms.TextInput(
        attrs={'class': 'form-control', 'type': 'text', 'required': True, 'placeholder': 'Apartment, suite, unit etc'}))
    shipping_city = forms.CharField(max_length=100, label="Town / City", widget=forms.TextInput(
        attrs={'class': 'form-control', 'type': 'text', 'required': True}))
    shipping_state = forms.CharField(max_length=50, label="State", widget=forms.TextInput(
        attrs={'class': 'form-control', 'type': 'text', 'required': True}))
    shipping_zip = forms.CharField(max_length=20, label="Postcode / ZIP", widget=forms.TextInput(
        attrs={'class': 'form-control', 'type': 'text', 'required': True}))
    additional_information = forms.CharField(label="Additional Information(optional)", widget=forms.Textarea(attrs={
        'rows': 4, 'class': 'md-textarea form-control'
    }))


# class CheckoutForm(forms.ModelForm):
#     shipping_country = CountryField(
#         blank_label='Choose your option').formfield(label="Country",
#                                                     required=True, widget=CountrySelectWidget(layout='{widget}', attrs={
#                                                         'class': 'mdb-select md-form md-outline'
#                                                     }))

#     def __init__(self, *args, **kwargs):
#         super(ShippingDetails, self).__init__(*args, **kwargs)
#         for name in self.fields.keys():
#             self.fields[name].widget.attrs.update({
#                 'class': 'form-control',
#             })

#     class Meta:
#         model = ShippingDetails
#         fields = ("__all__")
