from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import SafeString

from sso.models import MemberOTPRequest


@admin.register(MemberOTPRequest)
class MemberOTPRequestAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'member_link',
        'created_at',
        'is_valid',
        'failed_attempts',
        'code_masked',
    )

    list_display_links = ('id',)
    list_filter = (
        'is_valid',
        ('created_at', admin.DateFieldListFilter),
    )
    search_fields = ('member__username', 'member__firstname', 'member__lastname', 'member__email')
    readonly_fields = ('code', 'created_at', 'member')
    date_hierarchy = 'created_at'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('member')

    fieldsets = (
        (None, {'fields': ('member', 'is_valid', 'failed_attempts')}),
        ('F-Kode', {'fields': ('code', 'created_at'), 'classes': ('collapse',)}),
    )

    def member_link(self, obj: MemberOTPRequest) -> SafeString:
        url = f"/admin/stregsystem/member/{obj.member_id}/change/"
        return format_html('<a href="{url}">{username}</a>', url=url, username=obj.member.username)

    member_link.short_description = 'Member'
    member_link.admin_order_field = 'member__username'

    def code_masked(self, obj: MemberOTPRequest) -> str:
        return "F-*****" if obj.code else ""

    code_masked.short_description = 'OTP Code'
