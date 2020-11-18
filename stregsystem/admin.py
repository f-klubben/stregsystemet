from django.contrib import admin
from django import forms
from django.contrib.admin.views.autocomplete import AutocompleteJsonView
from django.contrib import messages
from django.contrib.admin.models import LogEntry

from stregsystem.models import (
    Category,
    Member,
    News,
    Payment,
    PayTransaction,
    Product,
    Room,
    Sale,
    MobilePayment
)
from stregsystem.templatetags.stregsystem_extras import money
from stregsystem.utils import (
    make_active_productlist_query,
    make_inactive_productlist_query
)


class SaleAdmin(admin.ModelAdmin):
    list_filter = ('room', 'timestamp')
    list_display = ('get_username', 'get_fullname', 'get_product_name', 'get_room_name', 'timestamp', 'get_price_display')
    actions = ['refund']
    search_fields = ['^member__username', '=product__id', 'product__name']
    valid_lookups = ('member')
    autocomplete_fields = ['member', 'product']

    class Media:
        css = {'all': ('stregsystem/select2-stregsystem.css',)}

    def get_username(self, obj):
        return obj.member.username

    get_username.short_description = "Username"
    get_username.admin_order_field = "member__username"

    def get_fullname(self, obj):
        return f"{obj.member.firstname} {obj.member.lastname}"

    get_fullname.short_description = "Full name"
    get_fullname.admin_order_field = "member__firstname"

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
            return make_active_productlist_query(queryset)
        elif self.value() == 'No':
            return make_inactive_productlist_query(queryset)
        else:
            return queryset


class ProductAdmin(admin.ModelAdmin):
    search_fields = ('name', 'price', 'id')
    list_filter = (ProductActivatedListFilter, 'deactivate_date', 'price')
    list_display = (
        'activated',
        'id',
        'name',
        'get_price_display',
    )
    fields = (
        "name",
        "price",
        ("active", "deactivate_date"),
        ("start_date", "quantity", "get_bought"),
        "categories",
        "rooms",
        "alcohol_content_ml"
    )
    readonly_fields = (
        "get_bought",
    )

    actions = [toggle_active_selected_products]
    filter_horizontal = ('categories', 'rooms')

    def get_price_display(self, obj):
        if obj.price is None:
            obj.price = 0
        return "{0:.2f} kr.".format(obj.price / 100.0)
    get_price_display.short_description = "Price"
    get_price_display.admin_order_field = "price"

    def get_bought(self, obj):
        return obj.bought
    get_bought.short_description = "Bought"
    get_bought.admin_order_field = "bought"

    def activated(self, product):
        return product.is_active()
    activated.boolean = True


class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'items_in_category')

    def items_in_category(self, obj):
        return obj.product_set.count()


class MemberForm(forms.ModelForm):
    class Meta:
        model = Member
        exclude = []

    def clean_username(self):
        username = self.cleaned_data['username']
        if self.instance is None or self.instance.pk is None:
            if Member.objects.filter(username=username).exists():
                raise forms.ValidationError("Brugernavnet er allerede taget")
        return username


class MemberAdmin(admin.ModelAdmin):
    form = MemberForm
    list_filter = ('want_spam', )
    search_fields = ('username', 'firstname', 'lastname', 'email')
    list_display = ('username', 'firstname', 'lastname', 'balance', 'email', 'notes')

    # fieldsets is like fields, except that they are grouped and with descriptions
    fieldsets = (
        (None, {
            'fields': ('username', 'firstname', 'lastname', 'year', 'gender', 'email'),
            'description': "Basal information omkring fember"
        }),
        (None, {
            'fields': ('notes',),
            'description': "Studieretning + evt. andet i noter"
        }),
        (None, {
            'fields': ('active', 'want_spam', 'balance', 'undo_count'),
            'description': "Lad være med at rode med disse, med mindre du ved hvad du laver ..."
        })
    )

    def save_model(self, request, obj, form, change):
        if 'username' in form.changed_data and change:
            if Member.objects.filter(username=obj.username).exclude(pk=obj.pk).exists():
                messages.add_message(request, messages.WARNING, 'Det brugernavn var allerede optaget')
        super().save_model(request, obj, form, change)

    def autocomplete_view(self, request):
        """
        @HACK: Apply the class below.
        """
        return self.AutoCompleteJsonViewCorrector.as_view(model_admin=self)(request)

    class AutoCompleteJsonViewCorrector(AutocompleteJsonView):
        """
        @HACK: We need to apply a filter to our AutoComplete (select2),
        we do this by overwriting the default behaviour, and apply our filter.
        """
        def get_queryset(self):
            qs = super().get_queryset()
            return qs.filter(active=True).order_by('username')


class PaymentAdmin(admin.ModelAdmin):
    list_display = ('get_username', 'timestamp', 'get_amount_display', 'is_mobilepayment')
    valid_lookups = ('member')
    search_fields = ['member__username']
    autocomplete_fields = ['member']

    class Media:
        css = {'all': ('stregsystem/select2-stregsystem.css',)}

    def get_username(self, obj):
        return obj.member.username

    get_username.short_description = "Username"
    get_username.admin_order_field = "member__username"

    def get_amount_display(self, obj):
        return money(obj.amount)

    get_amount_display.short_description = "Amount"
    get_amount_display.admin_order_field = "amount"


    def is_mobilepayment(self, obj):
        return MobilePayment.objects.filter(payment=obj.pk).exists()

    is_mobilepayment.short_description = "From MobilePayment"
    is_mobilepayment.admin_order_field = "from_mobilepayment"
    is_mobilepayment.boolean = True


class MobilePaymentAdmin(admin.ModelAdmin):
    list_display = (
        'payment', 'customer_name', 'comment', 'timestamp', 'transaction_id', 'get_amount_display', 'status')
    valid_lookups = 'member'
    search_fields = ['member__username']
    autocomplete_fields = ['member', 'payment']

    class Media:
        css = {'all': ('stregsystem/select2-stregsystem.css',)}

    def get_amount_display(self, obj):
        return money(obj.amount)

    get_amount_display.short_description = "Amount"
    get_amount_display.admin_order_field = "amount"

    # django-bug, .delete() is not called https://stackoverflow.com/questions/1471909/django-model-delete-not-triggered
    actions = ['really_delete_selected']

    def get_actions(self, request):
        actions = super(MobilePaymentAdmin, self).get_actions(request)
        del actions['delete_selected']
        return actions

    def really_delete_selected(self, _, queryset):
        for obj in queryset:
            obj.delete()

    really_delete_selected.short_description = "Delete and refund selected entries"


class LogEntryAdmin(admin.ModelAdmin):
    date_hierarchy = 'action_time'
    list_filter = ['content_type', 'action_flag']
    search_fields = ['object_repr', 'change_message', 'user__username']
    list_display = ['action_time', 'user', 'content_type', 'object_id', 'action_flag', 'change_message', 'object_repr']


    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False

    

admin.site.register(LogEntry, LogEntryAdmin)
admin.site.register(Sale, SaleAdmin)
admin.site.register(Member, MemberAdmin)
admin.site.register(Payment, PaymentAdmin)
admin.site.register(News)
admin.site.register(Product, ProductAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Room)
admin.site.register(MobilePayment, MobilePaymentAdmin)
