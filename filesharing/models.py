from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings #
from django.core.exceptions import ValidationError
import os

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
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError

class Document(models.Model):
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_documents'
    )
    document_title = models.CharField(max_length=255, blank=True)
    message = models.TextField(blank=True)
    file = models.FileField(upload_to='documents/')
    file_type = models.CharField(max_length=10, blank=True)  # e.g., 'doc', 'ppt', 'xls', 'pdf'
    file_size = models.PositiveIntegerField(null=True, blank=True)  # file size in bytes
    is_signed = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    deleted_by_sender = models.BooleanField(default=False)

    def __str__(self):
        return self.document_title or f"Document #{self.pk}"

    def clean(self):
        if not self.file:
            raise ValidationError("You must upload a file.")

    def save(self, *args, **kwargs):
        self.full_clean()

        if self.file:
            name = self.file.name
            ext = os.path.splitext(name)[1].lower().lstrip('.')  # get extension without dot

            # Normalize extension groups
            if ext in ['doc', 'docx']:
                self.file_type = 'doc'
            elif ext in ['ppt', 'pptx']:
                self.file_type = 'ppt'
            elif ext in ['xls', 'xlsx']:
                self.file_type = 'xls'
            else:
                self.file_type = ext  # keep original for pdf, zip, etc.

            # Get file size
            self.file_size = self.file.size

        super().save(*args, **kwargs)


# DOCUMENT RECIPIENT MODEL
class DocumentRecipient(models.Model):
    recipient_office = models.ForeignKey(Office, on_delete=models.CASCADE)
    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    received_at = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)
    is_read = models.BooleanField(default=False)
    
    
#models i might need later
# class Signature(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     document = models.OneToOneField(Document, on_delete=models.CASCADE)
#     signed_at = models.DateTimeField(auto_now_add=True)
#     signature_file = models.FileField(upload_to='signatures/')

# class Reply(models.Model):
#     original_document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='replies')
#     reply_document = models.OneToOneField(Document, on_delete=models.CASCADE, related_name='reply_to')
#     replied_by = models.ForeignKey(User, on_delete=models.CASCADE)
#     replied_at = models.DateTimeField(auto_now_add=True)

# class Notification(models.Model):
#     recipient = models.ForeignKey(User, on_delete=models.CASCADE)
#     message = models.CharField(max_length=255)
#     is_read = models.BooleanField(default=False)
#     created_at = models.DateTimeField(auto_now_add=True)

# class AuditTrail(models.Model):
#     action = models.CharField(max_length=100)
#     user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
#     document = models.ForeignKey(Document, on_delete=models.SET_NULL, null=True, blank=True)
#     timestamp = models.DateTimeField(auto_now_add=True)
#     details = models.TextField()
