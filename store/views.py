from django.shortcuts import render, get_object_or_404, redirect, reverse, HttpResponseRedirect
from django.http import HttpResponse, JsonResponse
from .models import Category, Company, Product, Cart, CartItem, ShippingDetails, Order, OrderItem, Review, Contact
from .forms import SignUpForm, LoginForm, CheckoutForm
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User, Group
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
import stripe
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
import urllib.parse as urlparse
from urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.db.models import Max, Min, Avg
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned


def home(request, category_slug=None):
    if category_slug != None:
        products = Product.objects.filter(
            category__slug=category_slug, available=True)
    else:
        products = Product.objects.all().filter(available=True)
    return render(request, 'home.html', {'products': products})


def productPage(request, category_slug, product_slug):
    can_review = False
    try:
        product = Product.objects.get(
            category__slug=category_slug, slug=product_slug)
        order_item = OrderItem.objects.all().filter(product=product,
                                                    order__email=request.user.email)
        if order_item.count() > 0:
            is_reviewed = Review.objects.all().filter(product=product, user=request.user)
            if not is_reviewed.count() > 0:
                can_review = True
    except Exception as e:
        raise e

    if request.method == 'POST' and request.user.is_authenticated and request.POST['content'].strip() != '':
        rating = int(request.POST['rating'])
        content = request.POST['content']
        Review.objects.create(product=product, user=request.user,
                              rating=rating, content=content)
        product_rating = Review.objects.all().filter(
            product=product).aggregate(Avg('rating'))['rating__avg']
        product.rating = product_rating
        product.save()
        can_review = False

    reviews = Review.objects.filter(product=product)
    reviews_num = reviews.count()

    return render(request, 'product_page.html', {'product': product, 'can_review': can_review, 'reviews': reviews, 'reviews_num': reviews_num})


def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()
    return cart


def change_cart(request, product_id):
    if request.method == "GET":
        add = request.GET.get('addQuantity', None)
        sub = request.GET.get('subQuantity', None)
        addQuantity = 0
        subQuantity = 0
        if add is not None:
            addQuantity = int(add)
        if sub is not None:
            subQuantity = int(sub)
        product = Product.objects.get(id=product_id)
        try:
            cart = Cart.objects.get(cart_id=_cart_id(request))
        except Cart.DoesNotExist:
            cart = Cart.objects.create(cart_id=_cart_id(request))
            cart.save()

        try:
            cart_item = CartItem.objects.get(product=product, cart=cart)
            if add is not None:
                if cart_item.quantity+addQuantity <= cart_item.product.stock:
                    cart_item.quantity += addQuantity
                    cart_item.save()
            else:
                if cart_item.quantity-subQuantity >= 1:
                    cart_item.quantity -= subQuantity
                    cart_item.save()
                else:
                    cart_item.delete()
        except CartItem.DoesNotExist:
            if addQuantity <= product.stock:
                cart_item = CartItem.objects.create(
                    product=product, cart=cart, quantity=addQuantity)
                cart_item.save()
        return redirect('cart_page')


def cartPage(request, total=0, counter=0, cart_items=None, shipping_address=None):
    try:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_items = CartItem.objects.filter(cart=cart, active=True)
        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity)
            counter += cart_item.quantity
        shipping_address = ShippingDetails.objects.filter(
            user=request.user).first()
    except Exception as e:
        print(e)
    return render(request, 'cart.html', dict(cart_items=cart_items, total=total, counter=counter, shipping_address=shipping_address))


def signupView(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            signup_user = User.objects.get(username=username)
            customer_group = Group.objects.get(name='Customer')
            customer_group.user_set.add(signup_user)
            login(request, signup_user)
    else:
        form = SignUpForm()
    return redirect('home')


def signinView(request):
    if request.method == 'POST':
        form = LoginForm(data=request.POST)
        if form.is_valid():
            username = request.POST['username']
            password = request.POST['password']
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
            else:
                return redirect('signup')
    else:
        form = AuthenticationForm()
    return redirect('home')


def signoutView(request):
    logout(request)
    return redirect('home')


@login_required
def checkoutPage(request):
    return render(request, 'checkout.html')


@csrf_exempt
def payment(request, total=0, counter=0, cart_items=None, payment_items=None):
    payment_items = []
    if request.method == 'GET':
        YOUR_DOMAIN = 'http://127.0.0.1:8000'
        stripe.api_key = settings.STRIPE_SECRET_KEY
        try:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, active=True)
            for cart_item in cart_items:
                total += (cart_item.product.price * cart_item.quantity)
                counter += cart_item.quantity
                payment_items.append({
                    'price_data': {
                        'currency': 'inr',
                        'unit_amount': int(cart_item.product.price*100),
                        'product_data': {
                            'name': cart_item.product.name
                        },
                    },
                    'quantity': cart_item.quantity,
                })
        except ObjectDoesNotExist:
            pass
        try:
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=payment_items,
                customer_email=request.user.email,
                client_reference_id=cart.id,
                mode='payment',
                success_url=YOUR_DOMAIN + '/order_history/',
                cancel_url=YOUR_DOMAIN + '/cart',
            )
            print("cardid"+str(cart.id))
            return JsonResponse({'id': checkout_session.id, 'key': settings.STRIPE_PUBLISHABLE_KEY})
        except Exception as e:
            return JsonResponse({'error': str(e)})


def success(request):
    return render(request, 'success.html')


def fail(request):
    return render(request, 'fail.html')


@csrf_exempt
def stripe_webhook(request):
    stripe.api_key = settings.STRIPE_SECRET_KEY
    endpoint_secret = settings.STRIPE_ENDPOINT_SECRET
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        # Invalid payload
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return HttpResponse(status=400)
    # Handle the checkout.session.completed event
    if event['type'] == 'checkout.session.completed':
        email = event.data.object.customer_email
        cart_id = event.data.object.client_reference_id
        amount = int(event.data.object.amount_total/100)
        order_id = event.data.object.id
        try:
            cart = Cart.objects.get(id=cart_id)
            order = Order.objects.create(
                total=amount, email=email, cart_id=cart_id)
            order.save()
            cart_items = CartItem.objects.filter(cart=cart, active=True)
            for cart_item in cart_items:
                order_item = OrderItem.objects.create(
                    product=cart_item.product, quantity=cart_item.quantity, order=order)
                order_item.save()

                product = Product.objects.get(id=cart_item.product.id)
                product.stock = int(
                    cart_item.product.stock - cart_item.quantity)
                if product.stock <= 0:
                    product.available = False
                product.save()
                cart_item.delete()
                print('the order has been created')
        except ObjectDoesNotExist:
            pass
        print(cart_items)

    return HttpResponse(status=200)


def shippingDetails(request):
    if request.is_ajax and request.method == "POST":
        form = CheckoutForm(request.POST)
        if form.is_valid():
            full_name = form.cleaned_data.get('full_name')
            phone = form.cleaned_data.get('phone')
            shipping_country = form.cleaned_data.get('shipping_country')
            shipping_address1 = form.cleaned_data.get('shipping_address1')
            shipping_address2 = form.cleaned_data.get('shipping_address2')
            shipping_city = form.cleaned_data.get('shipping_city')
            shipping_state = form.cleaned_data.get('shipping_state')
            shipping_zip = form.cleaned_data.get('shipping_zip')
            additional_information = form.cleaned_data.get(
                'additional_information')
            try:
                shipping_details = ShippingDetails.objects.get(
                    user=request.user)
                shipping_details.full_name = full_name
                shipping_details.phone = phone
                shipping_details.shipping_country = shipping_country
                shipping_details.shipping_address1 = shipping_address1
                shipping_details.shipping_address2 = shipping_address2
                shipping_details.shipping_state = shipping_state
                shipping_details.shipping_city = shipping_city
                shipping_details.shipping_zip = shipping_zip
                shipping_details.additional_information = additional_information
                shipping_details.save()
                return JsonResponse({"success": "Edited SUccesfully"}, status=200)
            except ObjectDoesNotExist:
                shipping_details = ShippingDetails.objects.create(
                    user=request.user,
                    full_name=full_name,
                    phone=phone,
                    shipping_country=shipping_country,
                    shipping_address1=shipping_address1,
                    shipping_address2=shipping_address2,
                    shipping_state=shipping_state,
                    shipping_city=shipping_city,
                    shipping_zip=shipping_zip,
                    additional_information=additional_information
                )
                shipping_details.save()
                return JsonResponse({"success": "Created SUccesfully"}, status=200)
        else:
            return JsonResponse({"error": form.errors}, status=400)
    return JsonResponse({"error": "Some error Occured!"}, status=400)


@login_required(redirect_field_name='next', login_url='home')
def orderHistory(request):
    if request.user.is_authenticated:
        email = str(request.user.email)
        order_details = Order.objects.filter(email=email)
    return render(request, 'orders_list.html', {'order_details': order_details})


@login_required(redirect_field_name='next', login_url='home')
def viewOrder(request, order_id):
    if request.user.is_authenticated:
        email = str(request.user.email)
        order = Order.objects.get(id=order_id, email=email)
        order_items = OrderItem.objects.filter(order=order)
        shipping_details = ShippingDetails.objects.get(user=request.user)
    return render(request, 'order_detail.html', {'order': order, 'order_items': order_items, 'shipping_details': shipping_details})


def search(request):
    term = request.GET.get('searchterm', None)
    select = request.GET.get('select', None)
    orderby = request.GET.get('orderby', None)
    view = request.GET.get('view', None)
    price = request.GET.get('price', None)
    min = request.GET.get('min', None)
    max = request.GET.get('max', None)
    rating = request.GET.get('rating', None)
    focus = '0'
    products_list = None
    min_price = 0
    max_price = 1000000
    active_radio = '0'

    if select == 'all':
        category = Category.objects.all().filter(name__contains=term)
        if(category):
            products_cat = Product.objects.all().filter(
                category__name__contains=category[0].name, available=True)
            products_name = Product.objects.all().filter(
                name__contains=term, available=True)
            products_list = (products_cat | products_name).distinct()
        else:
            products_list = Product.objects.all().filter(
                name__contains=term, available=True)

    else:
        products_list = Product.objects.all().filter(category__name__contains=select,
                                                     name__contains=term, available=True)
    if orderby is not None:
        if orderby == 'pricelh':
            focus = '1'
            products_list = products_list.order_by('price')
        elif orderby == 'pricehl':
            focus = '2'
            products_list = products_list.order_by('-price')
        elif orderby == 'newest':
            focus = '3'
            products_list = products_list.order_by('-created')
        elif orderby == 'oldest':
            focus = '4'
            products_list = products_list.order_by('created')

    max_price = products_list.aggregate(Max('price'))['price__max']
    min_price = products_list.aggregate(Min('price'))['price__min']
    diff = max_price - min_price

    price1 = min_price + diff/5
    price2 = min_price + (2*diff)/5
    price3 = min_price + (3*diff)/5
    price4 = min_price + (4*diff)/5

    if price == '1':
        products_list = products_list.filter(
            price__gte=min_price, price__lte=price1)
        active_radio = '1'
    elif price == '2':
        products_list = products_list.filter(
            price__gte=price1, price__lte=price2)
        active_radio = '2'
    elif price == '3':
        products_list = products_list.filter(
            price__gte=price2, price__lte=price3)
        active_radio = '3'
    elif price == '4':
        products_list = products_list.filter(
            price__gte=price3, price__lte=price4)
        active_radio = '4'
    elif price == '5':
        products_list = products_list.filter(
            price__gte=price4, price__lte=max_price)
        active_radio = '5'

    if min is not None and max is not None and min <= max:
        products_list = products_list.filter(
            price__gte=min, price__lte=max)

    if rating is not None:
        products_list = products_list.filter(rating__gte=int(rating))

    paginator = Paginator(products_list, 6)

    try:
        page = int(request.GET.get('page', '1'))
    except:
        page = 1

    try:
        products = paginator.page(page)
    except(EmptyPage, InvalidPage):
        products = paginator.page(paginator.num_pages)

    context = {'products': products, 'focus': focus, 'active_radio': active_radio,
               'max_price': max_price, 'min_price': min_price, 'price1': price1, 'price2': price2, 'price3': price3, 'price4': price4}

    if view == 'list':
        return render(request, 'searchlist.html', context)
    else:
        return render(request, 'searchbox.html', context)


def searchParams(request):
    url = request.META.get('HTTP_REFERER')
    orderby = request.GET.get('orderby', None)
    view = request.GET.get('view', None)
    page = request.GET.get('page', None)
    price = request.GET.get('price', None)
    min = request.GET.get('min', None)
    max = request.GET.get('max', None)
    rating = request.GET.get('rating', None)

    if orderby is not None:
        url = set_query_parameter(url, 'orderby', orderby)
    elif view is not None:
        url = set_query_parameter(url, 'view', view)
    elif page is not None:
        url = set_query_parameter(url, 'page', page)
    elif price is not None:
        url = set_query_parameter(url, 'price', price)
    elif min is not None and max is not None:
        url = set_query_parameter(url, 'min', min)
        url = set_query_parameter(url, 'max', max)
    elif rating is not None:
        url = set_query_parameter(url, 'rating', rating)

    return HttpResponseRedirect(url)


def set_query_parameter(url, param_name, param_value):
    scheme, netloc, path, query_string, fragment = urlsplit(url)
    query_params = parse_qs(query_string)

    query_params[param_name] = [param_value]
    new_query_string = urlencode(query_params, doseq=True)

    return urlunsplit((scheme, netloc, path, new_query_string, fragment))


def contact(request):
    if request.method == 'POST':
        name = request.POST.get('name', None)
        email = request.POST.get('email', None)
        message = request.POST.get('message', None)
        contact = Contact.objects.create(
            name=name, email=email, message=message)
        contact.save()
    return render(request, 'contact.html')
