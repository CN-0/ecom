from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('cart/', views.cartPage, name='cart_page'),
    path('payment/', views.payment, name='payment'),
    path('contact/', views.contact, name='contact'),
    path('change-password/', views.changePassword, name='changePassword'),
    path('search/', views.search, name='search'),
    path('wishlist/', views.wishlistPage, name='wishlist'),
    path('search-params/', views.searchParams, name='search-params'),
    path('shipping_details/', views.shippingDetails, name='shipping_details'),
    path('webhook/', views.stripe_webhook, name='webhook'),
    path('checkout/', views.checkoutPage, name='checkout_page'),
    path('order_history/', views.orderHistory, name='order_history'),
    path('order/<int:order_id>/', views.viewOrder, name='order_detail'),
    path('wishlist/<str:type>/<int:product_id>/',
         views.change_wishlist, name='change_wishlist'),
    path('cart/change/<int:product_id>/',
         views.change_cart, name='change_cart'),
    path('account/create/', views.signupView, name='signup'),
    path('account/signin/', views.signinView, name='signin'),
    path('account/signout/', views.signoutView, name='signout'),
    path('<slug:category_slug>/',
         views.home, name='products_by_category'),
    path('<slug:category_slug>/<slug:product_slug>/',
         views.productPage, name='product_page')
]
