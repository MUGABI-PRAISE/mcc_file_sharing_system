from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Office, Document, DocumentRecipient

# Custom User Admin
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'office', 'position', 'is_admin', 'is_staff']
    list_filter = ['is_admin', 'is_staff', 'is_superuser', 'office', 'date_of_appointment']
    search_fields = ['username', 'first_name', 'last_name', 'email', 'position']
    
    # Add custom fields to the user form
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('office', 'is_admin', 'date_of_birth', 'position', 'date_of_appointment', 'profile_picture')
        }),
    )
    
    # Fields to show when adding a new user
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Additional Info', {
            'fields': ('office', 'is_admin', 'date_of_birth', 'position', 'date_of_appointment', 'profile_picture')
        }),
    )

# Office Admin
@admin.register(Office)
class OfficeAdmin(admin.ModelAdmin):
    list_display = ['name', 'in_charge']
    search_fields = ['name']
    list_filter = ['in_charge']

# Document Admin
@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['id', 'document_title', 'sender', 'get_recipients', 'is_signed', 'timestamp', 'deleted_by_sender']
    list_filter = ['is_signed', 'deleted_by_sender', 'timestamp', 'sender__office']
    search_fields = ['document_title', 'message', 'sender__username', 'sender__first_name', 'sender__last_name']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'
    fieldsets = (
        ('Document Info', {
            'fields': ('document_title', 'message', 'file')
        }),
        ('Status', {
            'fields': ('is_signed', 'deleted_by_sender')
        }),
        ('Metadata', {
            'fields': ('sender', 'timestamp'),
            'classes': ('collapse',)
        }),
    )

    def get_recipients(self, obj):
        recipients = obj.documentrecipient_set.all()
        return ", ".join([r.recipient_office.name for r in recipients])
    get_recipients.short_description = 'Sent To'


# Document Recipient Admin
@admin.register(DocumentRecipient)
class DocumentRecipientAdmin(admin.ModelAdmin):
    list_display = ['document', 'recipient_office', 'received_at', 'is_read', 'is_deleted']
    list_filter = ['is_read', 'is_deleted', 'received_at', 'recipient_office']
    search_fields = ['document__document_title', 'recipient_office__name']
    readonly_fields = ['received_at']
    date_hierarchy = 'received_at'
    fieldsets = (
        ('Recipient Info', {
            'fields': ('document', 'recipient_office')
        }),
        ('Status', {
            'fields': ('is_read', 'is_deleted', 'received_at')
        }),
    )