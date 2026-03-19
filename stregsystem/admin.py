from typing import Any, Literal, Sequence
from typing_extensions import override
from django.contrib import admin
from django import forms
from django.contrib.admin.views.autocomplete import AutocompleteJsonView
from django.contrib import messages
from django.contrib.admin.models import LogEntry
from django.http import HttpRequest

from stregsystem.models import (
    Category,
    Member,
    News,
    Payment,
    PayTransaction,
    Product,
    Room,
    Sale,
    MobilePayment,
    NamedProduct,
    PendingSignup,
    Theme,
    ProductNote,
    Event,
    EventInstance,
    Ticket,
    TicketRecord,
)
from stregsystem.templatetags.stregsystem_extras import money
from stregsystem.utils import (
    make_active_productlist_query,
    make_inactive_productlist_query,
)


@admin.action(description="Refunder valgte sales")
def refund_sales(modeladmin, request, queryset):
    for sale in queryset:
        if not isinstance(sale, Sale):
            raise ValueError("queryset must be of Sale")
        sale.process_refund(request.user)


class BaseAdmin(admin.ModelAdmin):
    """
    Base admin class to add common attributes.
    Such as created_at and updated_at fields.
    """

    def _get_fields_to_display(self) -> list[str]:
        return self._get_fields_to_display_as_readonly()

    def _get_fields_to_display_as_readonly(self) -> list[str]:
        return [
            'created_at',
            'updated_at',
        ]

    def get_readonly_fields(self, request: HttpRequest, obj: Any | None = ...) -> list[str] | tuple[Any, ...]:
        return list(super().get_readonly_fields(request, obj)) + list(self._get_fields_to_display_as_readonly())

    def get_list_display(self, request) -> list[str]:
        return self._get_fields_to_display() + list(super().get_list_display(request))


class SaleAdmin(BaseAdmin):
    list_filter = ('room', 'timestamp')

    def _get_fields_to_display(self):
        return [
            'get_username',
            'get_fullname',
            'get_refunded',
            'get_product_name',
            'get_room_name',
            'timestamp',
            'get_price_display',
        ] + super()._get_fields_to_display()

    readonly_fields = ("refunded_at", "refunded_by")
    actions = [refund_sales]
    search_fields = ['^member__username', '=product__id', 'product__name']
    valid_lookups = 'member'
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

    def get_refunded(self, obj):
        if not isinstance(obj, Sale):
            raise ValueError("obj must be of Sale")
        return obj.is_refunded()

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


class ProductAdmin(BaseAdmin):
    search_fields = ('name', 'price', 'id')
    list_filter = (ProductActivatedListFilter, 'deactivate_date', 'price')

    def _get_fields_to_display(self):
        return [
            'activated',
            'id',
            'name',
            'get_price_display',
        ] + super()._get_fields_to_display()

    fields = (
        "name",
        "price",
        ("active", "deactivate_date"),
        ("start_date", "quantity", "get_bought"),
        "categories",
        "rooms",
        "alcohol_content_ml",
        "caffeine_content_mg",
    )

    def _get_fields_to_display_as_readonly(self) -> list[str]:
        return ["get_bought"] + super()._get_fields_to_display_as_readonly()

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


class NamedProductAdmin(BaseAdmin):
    search_fields = (
        'name',
        'product',
    )

    def _get_fields_to_display(self):
        return [
            'name',
            'product',
        ] + super()._get_fields_to_display()

    fields = (
        'name',
        'product',
    )
    autocomplete_fields = [
        'product',
    ]


class CategoryAdmin(BaseAdmin):
    def _get_fields_to_display(self):
        return [
            'name',
            'items_in_category',
        ] + super()._get_fields_to_display()

    def items_in_category(self, obj):
        return obj.product_set.count()


class MemberForm(forms.ModelForm):
    class Meta:
        model = Member
        exclude = []

    def clean_username(self):
        username = self.cleaned_data["username"]
        if self.instance is None or self.instance.pk is None:
            if Member.objects.filter(username__iexact=username).exists():
                raise forms.ValidationError("Brugernavnet er allerede taget")
        return username


class MemberAdmin(BaseAdmin):
    form = MemberForm
    list_filter = ('want_spam',)
    search_fields = ('username', 'firstname', 'lastname', 'email')

    def _get_fields_to_display(self):
        return [
            'username',
            'firstname',
            'lastname',
            'balance',
            'email',
            'notes',
        ] + super()._get_fields_to_display()

    # fieldsets is like fields, except that they are grouped and with descriptions
    fieldsets = (
        (
            None,
            {
                'fields': ('username', 'firstname', 'lastname', 'year', 'gender', 'email'),
                'description': "Basal information omkring fember",
            },
        ),
        (None, {'fields': ('notes',), 'description': "Studieretning + evt. andet i noter"}),
        (
            None,
            {
                'fields': ('active', 'want_spam', 'signup_due_paid', 'balance', 'undo_count'),
                'description': "Lad være med at rode med disse, med mindre du ved hvad du laver ...",
            },
        ),
    )

    def save_model(self, request, obj, form, change):
        if 'username' in form.changed_data and change:
            if Member.objects.filter(username__iexact=obj.username).exclude(pk=obj.pk).exists():
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


class PaymentAdmin(BaseAdmin):
    def _get_fields_to_display(self):
        return [
            'get_username',
            'timestamp',
            'get_amount_display',
            'is_mobilepayment',
        ] + super()._get_fields_to_display()

    valid_lookups = 'member'
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


class MobilePaymentAdmin(BaseAdmin):
    def _get_fields_to_display(self):
        return [
            'payment',
            'customer_name',
            'comment',
            'timestamp',
            'transaction_id',
            'get_amount_display',
            'status',
        ] + super()._get_fields_to_display()

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


class LogEntryAdmin(BaseAdmin):
    date_hierarchy = 'action_time'
    list_filter = ['content_type', 'action_flag']
    search_fields = ['object_repr', 'change_message', 'user__username']

    def _get_fields_to_display(self):
        return [
            'action_time',
            'user',
            'content_type',
            'object_id',
            'action_flag',
            'change_message',
            'object_repr',
        ] + super()._get_fields_to_display()

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class ThemeAdmin(BaseAdmin):
    def _get_fields_to_display(self):
        return [
            'name',
            'override',
            'begin_month',
            'begin_day',
            'end_month',
            'end_day',
        ] + super()._get_fields_to_display()

    search_fields = ["name"]

    @admin.action(description="Do not force chosen themes")
    def force_unset(modeladmin, request, queryset):
        queryset.update(override=Theme.NONE)

    @admin.action(description="Force show chosen themes")
    def force_show(modeladmin, request, queryset):
        queryset.update(override=Theme.SHOW)

    @admin.action(description="Force hide chosen themes")
    def force_hide(modeladmin, request, queryset):
        queryset.update(override=Theme.HIDE)

    actions = [force_unset, force_show, force_hide]


class ProductNoteAdmin(BaseAdmin):
    search_fields = ('active', 'text')

    def _get_fields_to_display(self):
        return [
            'active',
            'text',
        ] + super()._get_fields_to_display()

    actions = [toggle_active_selected_products]


class EventAdmin(admin.ModelAdmin):
    pass


@admin.action(description="Refunder valgte event instances")
def refund_event_instances(modeladmin, request, queryset):
    for event_instance in queryset:
        if not isinstance(event_instance, EventInstance):
            raise ValueError("queryset must be of EventInstance")
        event_instance.refund_all_tickets(request.user)


@admin.action(description="Refunder KUN STAND-BY på valgte event instances")
def refund_stand_by_event_instances(modeladmin, request, queryset):
    for event_instance in queryset:
        if not isinstance(event_instance, EventInstance):
            raise ValueError("queryset must be of EventInstance")
        event_instance.refund_all_stand_by_tickets(request.user)


class EventInstanceAdmin(admin.ModelAdmin):
    list_display = (
        'get_name',
        'get_issue_count',
        'get_stand_by_count',
    )
    readonly_fields = (
        'get_issue_count',
        'get_stand_by_count',
    )

    actions = [refund_event_instances, refund_stand_by_event_instances]

    @admin.display(description="Event name")
    def get_name(self, obj):
        if not isinstance(obj, EventInstance):
            raise ValueError("obj must be an EventInstance")
        return obj.get_name()

    @admin.display(description="Issued tickets count")
    def get_issue_count(self, obj):
        if not isinstance(obj, EventInstance):
            raise ValueError("obj must be an EventInstance")
        return obj.get_issued_ticket_records().count()

    @admin.display(description="Stand-by tickets count")
    def get_stand_by_count(self, obj):
        if not isinstance(obj, EventInstance):
            raise ValueError("obj must be an EventInstance")
        return obj.get_stand_by_ticket_records().count()


class TicketAdmin(admin.ModelAdmin):
    pass


@admin.action(description="Refunder valgte ticket records")
def refund_tickets(modeladmin, request, queryset):
    for ticket_record in queryset:
        if not isinstance(ticket_record, TicketRecord):
            raise ValueError("queryset must be of TicketRecord")
        ticket_record.process_refund(request.user)


class TicketRecordAdmin(admin.ModelAdmin):
    readonly_fields = ("sale",)

    actions = [refund_tickets]


admin.site.register(LogEntry, LogEntryAdmin)
admin.site.register(Sale, SaleAdmin)
admin.site.register(Member, MemberAdmin)
admin.site.register(Payment, PaymentAdmin)
admin.site.register(News)
admin.site.register(Product, ProductAdmin)
admin.site.register(NamedProduct, NamedProductAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Room)
admin.site.register(MobilePayment, MobilePaymentAdmin)
admin.site.register(PendingSignup)
admin.site.register(Theme, ThemeAdmin)
admin.site.register(ProductNote, ProductNoteAdmin)
admin.site.register(Event, EventAdmin)
admin.site.register(EventInstance, EventInstanceAdmin)
admin.site.register(Ticket, TicketAdmin)
admin.site.register(TicketRecord, TicketRecordAdmin)
