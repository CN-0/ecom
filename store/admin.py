from django.contrib import admin
from .models import Category, Company, Product, ShippingDetails, Order, OrderItem, Cart, CartItem, Review, Contact


class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}


admin.site.register(Category, CategoryAdmin)


class CompanyAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'category']
    prepopulated_fields = {'slug': ('name', 'category')}


admin.site.register(Company, CompanyAdmin)


class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'price',
                    'stock', 'available', 'category', 'company', 'created', 'updated']
    list_editable = ['stock', 'available', 'price']
    prepopulated_fields = {'slug': ('name', 'company', 'category')}
    list_per_page = 20


admin.site.register(Product, ProductAdmin)

admin.site.register(ShippingDetails)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(Review)
admin.site.register(Contact)
