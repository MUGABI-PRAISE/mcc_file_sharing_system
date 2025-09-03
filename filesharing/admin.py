from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    User, Office, Document, DocumentRecipient,
    Chat, ChatParticipant, ChatMessage, ChatMessageHide
)

# =======================
# CUSTOM USER ADMIN
# =======================
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = [
        'username', 'email', 'first_name', 'last_name',
        'office', 'position', 'is_admin', 'is_staff'
    ]
    list_filter = ['is_admin', 'is_staff', 'is_superuser', 'office', 'date_of_appointment']
    search_fields = ['username', 'first_name', 'last_name', 'email', 'position']
    
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': (
                'office', 'is_admin', 'date_of_birth',
                'position', 'date_of_appointment', 'profile_picture'
            )
        }),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Additional Info', {
            'fields': (
                'office', 'is_admin', 'date_of_birth',
                'position', 'date_of_appointment', 'profile_picture'
            )
        }),
    )


# =======================
# OFFICE ADMIN
# =======================
@admin.register(Office)
class OfficeAdmin(admin.ModelAdmin):
    list_display = ['name', 'in_charge']
    search_fields = ['name']
    list_filter = ['in_charge']


# =======================
# DOCUMENT ADMIN
# =======================
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


# =======================
# DOCUMENT RECIPIENT ADMIN
# =======================
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


# =======================
# CHAT ADMIN
# =======================
class ChatParticipantInline(admin.TabularInline):
    model = ChatParticipant
    extra = 1


class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 1
    fields = ['sender', 'content', 'voice_note', 'created_at', 'updated_at', 'is_deleted']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    list_display = ['id', 'chat_type', 'name', 'created_by', 'created_at', 'participant_count']
    list_filter = ['chat_type', 'created_at']
    search_fields = ['name', 'created_by__username', 'created_by__first_name', 'created_by__last_name']
    date_hierarchy = 'created_at'
    inlines = [ChatParticipantInline, ChatMessageInline]

    def participant_count(self, obj):
        return obj.participants.count()
    participant_count.short_description = 'Participants'


# =======================
# CHAT PARTICIPANT ADMIN
# =======================
@admin.register(ChatParticipant)
class ChatParticipantAdmin(admin.ModelAdmin):
    list_display = ['chat', 'office', 'joined_at']
    list_filter = ['chat__chat_type', 'joined_at']
    search_fields = ['chat__name', 'office__name']
    date_hierarchy = 'joined_at'


# =======================
# CHAT MESSAGE ADMIN
# =======================
@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'chat', 'sender', 'short_content', 'created_at', 'updated_at', 'is_deleted']
    list_filter = ['is_deleted', 'created_at', 'chat__chat_type']
    search_fields = ['content', 'sender__username', 'sender__first_name', 'sender__last_name']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'

    def short_content(self, obj):
        return (obj.content[:50] + '...') if len(obj.content) > 50 else obj.content
    short_content.short_description = 'Content'


# =======================
# CHAT MESSAGE HIDE ADMIN
# =======================
@admin.register(ChatMessageHide)
class ChatMessageHideAdmin(admin.ModelAdmin):
    list_display = ['message', 'user', 'hidden_at']
    list_filter = ['hidden_at']
    search_fields = ['message__content', 'user__username']
    date_hierarchy = 'hidden_at'
    readonly_fields = ['hidden_at']
