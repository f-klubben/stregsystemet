from django.contrib import admin

from events.models import EventInstance, TicketRecord, Event, Ticket


class EventAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'description',
    )


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
        'capacity',
        'start_time',
        'end_time',
        'final_refund_time',
        'location',
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

    @admin.display(description="Tickets issued")
    def get_issue_count(self, obj):
        if not isinstance(obj, EventInstance):
            raise ValueError("obj must be an EventInstance")
        return obj.get_issued_ticket_records().count()

    @admin.display(description="Tickets on Stand-by")
    def get_stand_by_count(self, obj):
        if not isinstance(obj, EventInstance):
            raise ValueError("obj must be an EventInstance")
        return obj.get_stand_by_ticket_records().count()


class TicketAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        "quantity",
        'event_instance',
        'product',
    )


@admin.action(description="Refunder valgte ticket records")
def refund_tickets(modeladmin, request, queryset):
    for ticket_record in queryset:
        if not isinstance(ticket_record, TicketRecord):
            raise ValueError("queryset must be of TicketRecord")
        ticket_record.process_refund(request.user)


class TicketRecordAdmin(admin.ModelAdmin):
    readonly_fields = ("sale",)
    list_display = (
        'ticket',
        'sale',
        'has_attended',
        'is_stand_by',
        'admin_issued_to',
        'admin_issued_by',
        'get_ticket_owner',
    )

    actions = [refund_tickets]


admin.site.register(Event, EventAdmin)
admin.site.register(EventInstance, EventInstanceAdmin)
admin.site.register(Ticket, TicketAdmin)
admin.site.register(TicketRecord, TicketRecordAdmin)
