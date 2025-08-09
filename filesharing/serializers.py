from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate
from .models import Office, Document, DocumentRecipient
from django.utils.timesince import timesince # helps in enforcing the 'set at' feature.
from django.utils.timezone import now
import os

#uploader for cloudinary
from cloudinary.uploader import upload as cloudinary_upload

#get the user model
User = get_user_model()

#################################################################
#       SERIALIZER FOR OFFICE MODEL
#################################################################
class OfficeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Office
        fields = ['id', 'name']


##########################################################################
#   SERIALIZERS FOR USER MODEL. HANDLES AUTHENTICATION AND REGISTRATION
##########################################################################
class UserSerializer(serializers.ModelSerializer):
    office = OfficeSerializer(read_only=True) # will be used to track the office name

    class Meta:
        model = User
        fields = [
            'id', 'username', 'first_name', 'last_name', 'email',
            'date_of_birth', 'position', 'date_of_appointment',
            'profile_picture', 'office', 'is_admin'
        ]
        read_only_fields = ['id', 'is_admin']


# signup serializer
class UserSignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6) # hide the password in responses

    class Meta:
        model = User
        fields = [
            'username', 'first_name', 'last_name', 'email',
            'password', 'date_of_birth', 'position',
            'date_of_appointment', 'profile_picture', 'office'
        ]
    # hash password
    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


# login serializer
class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        username = data.get('username')
        password = data.get('password')
        user = authenticate(username=username, password=password)

        if not user:
            raise serializers.ValidationError("Invalid username or password")

        data['user'] = user
        return data



#################################################################
#       SERIALIZER FOR OFFICE MODEL
#################################################################
class OfficeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Office
        fields = ['id', 'name']
        

#####################################################################
# HANDLING FILE SUBMISSION SERIALIZER.
#####################################################################
# currently handles submission of one file
class DocumentUploadSerializer(serializers.ModelSerializer):
    offices = serializers.PrimaryKeyRelatedField(
        queryset=Office.objects.all(),
        many=True,
        write_only=True
    )
    file = serializers.FileField(write_only=True)
    file_size = serializers.SerializerMethodField(read_only=True)
    sent_at = serializers.SerializerMethodField(read_only=True)
    file_type = serializers.CharField(read_only=True)
    sender = UserSerializer(read_only=True)
    file_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Document
        fields = [
            'id',
            'document_title',
            'file',
            'file_url',
            'message',
            'offices',
            'file_size',
            'sent_at',
            'file_type',
            'sender'
        ]

    def get_file_url(self, obj):
        return obj.file.url if obj.file else None

    def get_file_size(self, obj):
        size = obj.file_size
        if size is None:
            return None
        elif size < 1024:
            return f"{size} B"
        elif size < 1024 ** 2:
            return f"{size / 1024:.1f} KB"
        else:
            return f"{size / (1024 ** 2):.1f} MB"

    def get_sent_at(self, obj):
        delta = timesince(obj.timestamp, now())
        return f"{delta.split(',')[0]} ago"

    # do some custom logic before saving the file to the database.
    def create(self, validated_data):
        # get some fields from validated data, that we shall use to create the instance
        offices = validated_data.pop('offices')
        user = self.context['request'].user
        file = validated_data.pop('file')

        # Determine file type & resource_type for Cloudinary
        ext = os.path.splitext(file.name)[1].lower().lstrip('.')
        if ext in ['mp4', 'mov', 'avi', 'mkv']:
            resource_type = 'video'
        elif ext in ['pdf', 'doc', 'docx', 'ppt', 'pptx', 'xls', 'xlsx']:
            resource_type = 'raw' # important for cloudinary to know this ain't a video or image
        else:
            resource_type = 'image'

        # Upload to Cloudinary with correct resource_type
        # we are doing all this before saving
        upload_result = cloudinary_upload(file, resource_type=resource_type)
        print(upload_result)

        # Create Document entry (this is where we save)
        document = Document.objects.create(
            sender=user,
            file=upload_result['secure_url'],  # storing the file URL directly
            file_type=ext,
            file_size=file.size,
            **validated_data
        )
        print(validated_data)

        # Link document to offices
        for office in offices:
            DocumentRecipient.objects.create(document=document, recipient_office=office)

        return document



##################################################################
#    RECEIVED FILES. 
##################################################################
# create a serializer that includes document data through DocumentRecipient.
class ReceivedDocumentSerializer(serializers.ModelSerializer):
    document = DocumentUploadSerializer(read_only=True)

    class Meta:
        model = DocumentRecipient
        fields = ['id', 'document', 'received_at', 'is_read']
