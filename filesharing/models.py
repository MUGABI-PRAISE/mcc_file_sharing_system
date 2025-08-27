from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings #
from django.core.exceptions import ValidationError
import os
from cloudinary.models import CloudinaryField

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
     
