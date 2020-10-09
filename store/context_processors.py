from .models import Category
from .forms import SignUpForm, LoginForm, CheckoutForm


def menu_links(request):
    links = Category.objects.all()
    return dict(links=links)


def login_form(request):
    form = LoginForm()
    return dict(loginForm=form)


def register_form(request):
    form = SignUpForm()
    return dict(signupForm=form)


def checkout_form(request):
    form = CheckoutForm()
    return dict(checkoutForm=form)
