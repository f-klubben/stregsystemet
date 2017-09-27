from django.contrib import admin
from django.db.models import Q
from django.utils import timezone
from stregsystem.utils import make_active_productlist_query
from stregsystem.models import (
    Category,
    Member,
    News,
    Payment,
    PayTransaction,
    Product,
    Room,
    Sale,
)


class SaleAdmin(admin.ModelAdmin):
    list_filter = ('room', 'timestamp')
    list_display = ('get_username', 'get_product_name', 'get_room_name', 'timestamp', 'get_price_display')
    actions = ['refund']
    search_fields = ['^member__username', '=product__id', 'product__name']
    valid_lookups = ('member')

    def get_username(self, obj):
        return obj.member.username

    get_username.short_description = "Username"
    get_username.admin_order_field = "member__username"

    def get_product_name(self, obj):
        return obj.product.name

    get_product_name.short_description = "Product"
    get_product_name.admin_order_field = "product__name"

    def get_room_name(self, obj):
        return obj.room.name

    get_room_name.short_description = "Room"
    get_room_name.admin_order_field = "room__name"

    def delete_model(self, request, obj):
        transaction = PayTransaction(obj.price)
        obj.member.rollback(transaction)
        obj.member.save()
        super(SaleAdmin, self).delete_model(request, obj)

    def save_model(self, request, obj, form, change):
        if change:
            return
        transaction = PayTransaction(obj.price)
        obj.member.fulfill(transaction)
        obj.member.save()
        super(SaleAdmin, self).save_model(request, obj, form, change)

    def get_price_display(self, obj):
        if obj.price is None:
            obj.price = 0
        return "{0:.2f} kr.".format(obj.price / 100.0)

    get_price_display.short_description = "Price"
    get_price_display.admin_order_field = "price"

    def refund(modeladmin, request, queryset):
        for obj in queryset:
            transaction = PayTransaction(obj.price)
            obj.member.rollback(transaction)
            obj.member.save()
        queryset.delete()
    refund.short_description = "Refund selected"


def toggle_active_selected_products(modeladmin, request, queryset):
    "toggles active on products, also removes deactivation date."
    # This is horrible since it does not use update, but update will
    # not do not F('active') so we are doing this. I am sorry.
    for obj in queryset:
        obj.deactivate_date = None
        obj.active = not obj.active
        obj.save()


class ProductActivatedListFilter(admin.SimpleListFilter):
    title = 'activated'
    parameter_name = 'activated'

    def lookups(self, request, model_admin):
        return (
            ('Yes', 'Yes'),
            ('No', 'No'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'Yes':
            return queryset.filter(make_active_productlist_query())
        elif self.value() == 'No':
            return queryset.exclude(make_active_productlist_query())
        else:
            return queryset


class ProductAdmin(admin.ModelAdmin):
    search_fields = ('name', 'price', 'id')
    list_filter = (ProductActivatedListFilter, 'deactivate_date', 'price')
    list_display = ('activated', 'id', 'name', 'get_price_display', 'categories_display', 'rooms_display')
    actions = [toggle_active_selected_products]
    filter_horizontal = ('categories', )


    def get_price_display(self, obj):
        if obj.price is None:
            obj.price = 0
        return "{0:.2f} kr.".format(obj.price / 100.0)

    get_price_display.short_description = "Price"
    get_price_display.admin_order_field = "price"

    def activated(self, product):
        return product.is_active()
    activated.boolean = True


    def categories_display(self, obj):
        # TODO Add a link to the category.
        return ', '.join((cat.name for cat in obj.categories.all()))
    categories_display.short_description = "Categories"

    def rooms_display(self, obj):
        if len(obj.rooms.all()) == 0:
            return 'All'
        else:
            return ', '.join(room.name for room in obj.rooms.all())
    rooms_display.short_description = "Rooms"


class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'items_in_category')

    def items_in_category(self, obj):
        return obj.product_set.count()


class MemberAdmin(admin.ModelAdmin):
    list_filter = ('want_spam', )
    search_fields = ('username', 'firstname', 'lastname', 'email')
    list_display = ('username', 'firstname', 'lastname', 'balance', 'email', 'notes')


class PaymentAdmin(admin.ModelAdmin):
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "member":
            kwargs["queryset"] = Member.objects.filter(active=True).order_by('username')
            return db_field.formfield(**kwargs)
        return super(PaymentAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)

    list_display = ('get_username', 'timestamp', 'get_amount_display')
    valid_lookups = ('member')
    search_fields = ['member__username']

    def get_username(self, obj):
        return obj.member.username

    get_username.short_description = "Username"
    get_username.admin_order_field = "member__username"

    def get_amount_display(self, obj):
        if obj.amount is None:
            obj.amount = 0
        return "{0:.2f} kr.".format(obj.amount / 100.0)

    get_amount_display.short_description = "Amount"
    get_amount_display.admin_order_field = "amount"


admin.site.register(Sale, SaleAdmin)
admin.site.register(Member, MemberAdmin)
admin.site.register(Payment, PaymentAdmin)
admin.site.register(News)
admin.site.register(Product, ProductAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Room)
