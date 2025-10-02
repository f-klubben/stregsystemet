from django.contrib import admin
from django import forms
from django.conf import settings
from django.contrib.admin.views.autocomplete import AutocompleteJsonView
from django.contrib import messages
from django.contrib.admin.models import LogEntry
from django.core.exceptions import ValidationError
from django.utils.html import format_html
from datetime import datetime
import hashlib
import pytz
import os

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
    Achievement,
    AchievementComplete,
    AchievementTask,
    AchievementConstraint,
)
from stregsystem.templatetags.stregsystem_extras import money
from stregsystem.utils import make_active_productlist_query, make_inactive_productlist_query


def refund(modeladmin, request, queryset):
    for obj in queryset:
        transaction = PayTransaction(obj.price)
        obj.member.rollback(transaction)
        obj.member.save()
    queryset.delete()


refund.short_description = "Refund selected"


class SaleAdmin(admin.ModelAdmin):
    list_filter = ('room', 'timestamp')
    list_display = (
        'get_username',
        'get_fullname',
        'get_product_name',
        'get_room_name',
        'timestamp',
        'get_price_display',
    )
    actions = [refund]
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
        "alcohol_content_ml",
        "caffeine_content_mg",
    )
    readonly_fields = ("get_bought",)

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


class NamedProductAdmin(admin.ModelAdmin):
    search_fields = (
        'name',
        'product',
    )
    list_display = (
        'name',
        'product',
    )
    fields = (
        'name',
        'product',
    )
    autocomplete_fields = [
        'product',
    ]


class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'items_in_category')

    def items_in_category(self, obj):
        return obj.product_set.count()


class MemberForm(forms.ModelForm):
    class Meta:
        model = Member
        exclude = []

    def clean_username(self):
        username = self.cleaned_data['username']
        if self.instance is None or self.instance.pk is None:
            if Member.objects.filter(username__iexact=username).exists():
                raise forms.ValidationError("Brugernavnet er allerede taget")
        return username


class MemberAdmin(admin.ModelAdmin):
    form = MemberForm
    list_filter = ('want_spam',)
    search_fields = ('username', 'firstname', 'lastname', 'email')
    list_display = ('username', 'firstname', 'lastname', 'balance', 'email', 'notes')

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


class PaymentAdmin(admin.ModelAdmin):
    list_display = ('get_username', 'timestamp', 'get_amount_display', 'is_mobilepayment')
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


class MobilePaymentAdmin(admin.ModelAdmin):
    list_display = (
        'payment',
        'customer_name',
        'comment',
        'timestamp',
        'transaction_id',
        'get_amount_display',
        'status',
    )
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


class ThemeAdmin(admin.ModelAdmin):
    list_display = ["name", "override", "begin_month", "begin_day", "end_month", "end_day"]
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


class ProductNoteAdmin(admin.ModelAdmin):
    search_fields = ('active', 'text')
    list_display = (
        'active',
        'text',
    )

    actions = [toggle_active_selected_products]


class AchievementForm(forms.ModelForm):
    existing_icons = forms.ChoiceField(label="Or choose an existing image", required=False, choices=[])

    class Meta:
        model = Achievement
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        folder_path = os.path.join(settings.MEDIA_ROOT, 'stregsystem/achievement')
        choices = [('', '---')]
        if os.path.exists(folder_path):
            for filename in sorted(os.listdir(folder_path)):
                if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                    path = os.path.join('stregsystem/achievement', filename)
                    choices.append((path, filename))
        self.fields['existing_icons'].choices = choices

    def save(self, commit=True):
        instance = super().save(commit=False)

        new_upload = self.files.get('icon')
        selected_icon_path = self.cleaned_data.get('existing_icons')

        if new_upload:
            uploaded_bytes = new_upload.read()
            uploaded_hash = hashlib.md5(uploaded_bytes).hexdigest()

            folder_path = os.path.join(settings.MEDIA_ROOT, 'stregsystem/achievement')
            match_found = False

            for filename in os.listdir(folder_path):
                file_path = os.path.join(folder_path, filename)

                # Check for matching hash
                with open(file_path, 'rb') as f:
                    existing_hash = hashlib.md5(f.read()).hexdigest()
                    if uploaded_hash == existing_hash:
                        # Match found — use existing file
                        instance.icon.name = os.path.join('stregsystem/achievement', filename)
                        match_found = True
                        break

            if not match_found:
                # No match — reset file pointer and let Django upload it
                new_upload.seek(0)  # important!
                instance.icon = new_upload

        elif selected_icon_path:
            # No upload, but existing image selected
            instance.icon.name = selected_icon_path

        if commit:
            instance.save()
        return instance


class AchievementAdmin(admin.ModelAdmin):
    form = AchievementForm

    search_fields = ['title', 'description']
    list_display = ['title', 'description', 'get_icon', 'get_active_from_or_active_duration']

    fieldsets = (
        (None, {'fields': ('title', 'description')}),
        (None, {'fields': (('icon', 'existing_icons'),)}),
        (None, {'fields': ('tasks', 'constraints')}),
        (None, {'fields': (('active_from', 'active_duration'),)}),
    )

    def get_icon(self, obj):
        if obj.icon:
            filename = obj.icon.name.rsplit('/', 1)[-1]
            filename = filename.rsplit('\\', 1)[-1]
            return format_html('<img src="{}" style="height: 20px;"/> {}', obj.icon.url, filename)
        return "-"

    get_icon.short_description = 'Icon'

    def get_active_from_or_active_duration(self, obj):
        if obj.active_from is not None:
            return f"Active From: {obj.active_from.strftime('%Y-%m-%d %H:%M:%S')}"
        elif obj.active_duration is not None:
            return f"Active Duration: {obj.active_duration}"

    get_active_from_or_active_duration.short_description = "Active-From / -Duration"

    @admin.action(description="Set Active From to now")
    def set_active_from_to_now(self, request, queryset):
        tz = pytz.timezone("Europe/Copenhagen")
        for obj in queryset:
            obj.active_from = datetime.now(tz=pytz.timezone("Europe/Copenhagen"))
            obj.full_clean()
            obj.save()

    @admin.action(description="Set Active From to None")
    def set_active_from_to_null(self, request, queryset):
        for obj in queryset:
            obj.active_from = None
            obj.full_clean()
            obj.save()

    actions = [set_active_from_to_now, set_active_from_to_null]


class AchievementTaskAdmin(admin.ModelAdmin):
    list_display = [
        'notes',
        'task_type',
        'goal_value',
        'get_product',
        'category',
    ]

    def get_product(self, obj):
        if obj.product:
            name = str(obj.product)
            return name[:20] + "..." if len(name) > 20 else name
        return ""

    get_product.short_description = "Product"


class AchievementCompleteAdmin(admin.ModelAdmin):

    valid_lookups = ['member', 'achievement']
    search_fields = ['member__username', 'achievement__title', 'achievement__description', 'completed_at']
    list_display = ['get_username', 'get_achievement_title', 'get_achievement_description', 'completed_at']

    def get_username(self, obj):
        return obj.member.username

    def get_achievement_title(self, obj):
        return obj.achievement.title

    get_achievement_title.short_description = 'Achievement Title'

    def get_achievement_description(self, obj):
        return obj.achievement.description

    get_achievement_description.short_description = 'Achievement Description'


class AchievementConstraintAdmin(admin.ModelAdmin):
    list_display = [
        'notes',
        'month_start',
        'month_end',
        'day_start',
        'day_end',
        'time_start',
        'time_end',
        'weekday',
    ]

    fieldsets = (
        (None, {'fields': ['notes']}),
        (
            None,
            {
                'fields': ['month_start', 'month_end'],
            },
        ),
        (
            None,
            {
                'fields': ['day_start', 'day_end'],
            },
        ),
        (
            None,
            {
                'fields': ['time_start', 'time_end'],
            },
        ),
        (
            None,
            {
                'fields': ['weekday'],
            },
        ),
    )


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
admin.site.register(Achievement, AchievementAdmin)
admin.site.register(AchievementTask, AchievementTaskAdmin)
admin.site.register(AchievementComplete, AchievementCompleteAdmin)
admin.site.register(AchievementConstraint, AchievementConstraintAdmin)
