from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Event, EventRegistration, BarcodeScan, AboutSection, Stat, QRCodeData

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('name', 'date', 'location', 'created_by', 'display_image', 'registrations_count', 'view_registered_users')
    list_filter = ('date', 'location', 'created_by')
    search_fields = ('name', 'location', 'created_by__username')
    date_hierarchy = 'date'
    readonly_fields = ('registrations_count',)
    fieldsets = (
        ('Event Details', {
            'fields': ('name', 'date', 'location', 'created_by')
        }),
        ('Timing', {
            'fields': ('start_time', 'stop_time')
        }),
        ('Media', {
            'fields': ('img',)
        }),
    )

    def display_image(self, obj):
        if obj.img:
            return format_html('<img src="{}" width="50" height="50" />', obj.img.url)
        return "No Image"
    display_image.short_description = 'Event Image'

    def registrations_count(self, obj):
        return obj.registrations.count()
    registrations_count.short_description = 'Registrations'

    def view_registered_users(self, obj):
        url = reverse('admin:Events_eventregistration_changelist') + f'?event__id={obj.id}'
        return format_html('<a class="button" href="{}">View Registered Users</a>', url)
    view_registered_users.short_description = 'Registered Users'

@admin.register(EventRegistration)
class EventRegistrationAdmin(admin.ModelAdmin):
    list_display = ('user', 'event', 'registration_date', 'user_email')
    list_filter = ('event', 'registration_date')
    search_fields = ('user__username', 'user__email', 'event__name')
    date_hierarchy = 'registration_date'
    raw_id_fields = ('user', 'event')

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email'

@admin.register(BarcodeScan)
class BarcodeScanAdmin(admin.ModelAdmin):
    list_display = ('user', 'event', 'scan_time', 'time_taken', 'user_email')
    list_filter = ('event', 'scan_time')
    search_fields = ('user__username', 'event__name', 'time_taken')
    date_hierarchy = 'scan_time'
    ordering = ('time_taken', 'scan_time')

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email'


class StatInline(admin.TabularInline):
    model = Stat
    extra = 1
    min_num = 1
    verbose_name = "Statistic"
    verbose_name_plural = "Statistics"

@admin.register(AboutSection)
class AboutSectionAdmin(admin.ModelAdmin):
    list_display = ('subtitle', 'display_image', 'stats_count')
    search_fields = ('subtitle', 'description')
    inlines = [StatInline]

    def display_image(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" />', obj.image.url)
        return "No Image"
    display_image.short_description = 'Image'

    def stats_count(self, obj):
        return obj.stats.count()
    stats_count.short_description = 'Number of Statistics'

@admin.register(QRCodeData)
class QRCodeDataAdmin(admin.ModelAdmin):
    list_display = ('data', 'created_at')
    search_fields = ('data',)
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at',)