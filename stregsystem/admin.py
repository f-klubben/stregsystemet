from django.contrib import admin
from stregsystem.models import Sale, Member, Payment, News, Product, Room

class SaleAdmin(admin.ModelAdmin):
    list_filter = ('room', 'timestamp')
    list_display = ('get_username', 'get_product_name', 'price')

    def get_username(self, obj):
        return obj.member.username
    get_username.short_description = "Username"
    get_username.admin_order_field = "member__username"

    def get_product_name(self, obj):
        return obj.product.name
    get_product_name.short_description = "Product"
    get_product_name.admin_order_field = "product__name"

def toggle_active_selected_products(modeladmin, request, queryset):
    "toggles active on products, also removes deactivation date."
    # This is horrible since it does not use update, but update will
    # not do not F('active') so we are doing this. I am sorry.
    for obj in queryset:
        obj.deactivate_date = None
        obj.active = not obj.active
        obj.save()

class ProductAdmin(admin.ModelAdmin):
    search_fields = ('name', 'price', 'id')
    list_filter = ('deactivate_date', 'price')
    list_display = ('name', 'price')
    actions = [toggle_active_selected_products]

class MemberAdmin(admin.ModelAdmin):
    list_filter = ('want_spam', )
    search_fields = ('username', 'firstname', 'lastname', 'email')
    list_display = ('username', 'firstname', 'lastname', 'balance', 'email', 'notes')

class PaymentAdmin(admin.ModelAdmin):
    list_display = ('get_username', 'amount', 'timestamp')

    def get_username(self, obj):
        return obj.member.username
    get_username.short_description = "Username"
    get_username.admin_order_field = "member__username"

admin.site.register(Sale, SaleAdmin)
admin.site.register(Member, MemberAdmin)
admin.site.register(Payment, PaymentAdmin)
admin.site.register(News)
admin.site.register(Product, ProductAdmin)
admin.site.register(Room)
