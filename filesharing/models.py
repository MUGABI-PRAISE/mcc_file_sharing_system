from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings #
from django.core.exceptions import ValidationError
import os
from cloudinary.models import CloudinaryField
from django.utils import timezone
# USER MODEL
class User(AbstractUser):
    office = models.ForeignKey('Office', on_delete=models.SET_NULL, null=True, blank=True)
    is_admin = models.BooleanField(default=False)
    
    date_of_birth = models.DateField(null=True, blank=True)
    position = models.CharField(max_length=100, null=True, blank=True)
    date_of_appointment = models.DateField(null=True, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True)

    
    # return the full name of the user
    def __str__(self):
        return self.first_name + ' ' + self.last_name


#OFFICE MODEL
class Office(models.Model):
    name = models.CharField(max_length=100, unique=True)
    in_charge = models.OneToOneField(
        settings.AUTH_USER_MODEL, # better instead of importing the user model
        on_delete=models.SET_NULL, # if the user is deleted, the office will be in charge until we set one
        null=True,
        blank=True,
        related_name='office_in_charge' # allows reverse relationship
    )

    def __str__(self):
        return self.name
    
    
# DOCUMENT MODEL

class Document(models.Model):
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_documents'
    )
    document_title = models.CharField(max_length=255, blank=True)
    message = models.TextField(blank=True)
    file = models.URLField()  # ✅ store Cloudinary URL instead of CloudinaryField
    file_type = models.CharField(max_length=10, blank=True)
    file_size = models.PositiveIntegerField(null=True, blank=True)
    is_signed = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    deleted_by_sender = models.BooleanField(default=False)

    def __str__(self):
        return self.document_title or f"Document #{self.pk}"

    def clean(self):
        if not self.file:
            raise ValidationError("You must upload a file.")




# DOCUMENT RECIPIENT MODEL
# helps to track different operations that happen to a file when sent to other recipients
class DocumentRecipient(models.Model):
    recipient_office = models.ForeignKey(Office, on_delete=models.CASCADE)
    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    received_at = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)
    is_read = models.BooleanField(default=False)


# IN APP CHATTING
from .models import Office  # reuse your existing Office

class Chat(models.Model):
    """
    A chat between offices. Either 'direct' (exactly 2 offices) or 'group' (2+).
    Membership is by office; any user within a participant office participates implicitly.
    """
    CHAT_TYPE_CHOICES = (('direct', 'Direct'), ('group', 'Group'))
    chat_type = models.CharField(max_length=10, choices=CHAT_TYPE_CHOICES)
    name = models.CharField(max_length=255, blank=True, null=True)  # used for group
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_chats')
    created_at = models.DateTimeField(auto_now_add=True)
    participants = models.ManyToManyField(Office, through='ChatParticipant', related_name='chats')

    def __str__(self):
        if self.chat_type == 'group':
            return f"{self.name or 'Group'} (#{self.pk})"
        return f"Direct Chat #{self.pk}"

    def participant_office_ids(self):
        return list(self.participants.values_list('id', flat=True))


class ChatParticipant(models.Model):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='participant_links')
    office = models.ForeignKey(Office, on_delete=models.CASCADE, related_name='chat_participations')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('chat', 'office')

    def __str__(self):
        return f"Office {self.office_id} in Chat {self.chat_id}"


class ChatMessage(models.Model):
    """
    Messages in chats. Sender is a user; delivery & read statuses tracked by Office.
    """
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='chat_messages')
    content = models.TextField(blank=True)
    voice_note = models.URLField(blank=True, null=True)  # Cloudinary URL
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    is_deleted = models.BooleanField(default=False)

    # Statuses by Office (NOT by user) so it's truly "office-to-office"
    delivered_to = models.ManyToManyField(Office, related_name='delivered_chat_messages', blank=True)
    read_by = models.ManyToManyField(Office, related_name='read_chat_messages', blank=True)

    def can_edit(self, user):
        # Only sender can edit within 15 minutes
        if self.sender_id != getattr(user, 'id', None):
            return False
        return (timezone.now() - self.created_at).total_seconds() <= 15 * 60

    def __str__(self):
        return f"Msg#{self.pk} in Chat#{self.chat_id} by {self.sender_id}"


class ChatMessageHide(models.Model):
    """
    For DIRECT chats only:
    Allows a user to hide (delete for me) other people's messages locally.
    Not used for groups (not allowed).
    """
    message = models.ForeignKey(ChatMessage, on_delete=models.CASCADE, related_name='hidden_by_users')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='hidden_messages')
    hidden_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('message', 'user')


     
