from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate
from .models import Office, Document, DocumentRecipient, Chat, ChatParticipant, ChatMessage
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
        return obj.file if obj.file else None

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
        offices = validated_data.pop('offices')
        user = self.context['request'].user
        file = validated_data.pop('file')

        # Determine file extension
        ext = os.path.splitext(file.name)[1].lower().lstrip('.')
        if ext in ['mp4', 'mov', 'avi', 'mkv']:
            resource_type = 'video'
        elif ext in ['pdf', 'doc', 'docx', 'ppt', 'pptx', 'xls', 'xlsx']:
            resource_type = 'raw'
        else:
            resource_type = 'image'

        # Upload to Cloudinary
        upload_result = cloudinary_upload(file, resource_type=resource_type)

        # Store metadata BEFORE overwriting file
        file_size = file.size
        file_type = ext

        # Create document in DB
        document = Document.objects.create(
            sender=user,
            file=upload_result['secure_url'],  # Cloudinary URL
            file_type=file_type,
            file_size=file_size,
            **validated_data
        )

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


###################################################################33
#   SERIALIZERS FOR INAPP CHATTING
#######################################################################
User = get_user_model()


class OfficeTinySerializer(serializers.ModelSerializer):
    class Meta:
        model = Office
        fields = ['id', 'name']


class ChatSerializer(serializers.ModelSerializer):
    participants = OfficeTinySerializer(many=True, read_only=True)
    last_message = serializers.SerializerMethodField()
    is_group = serializers.SerializerMethodField()

    class Meta:
        model = Chat
        fields = ['id', 'chat_type', 'name', 'created_at', 'participants', 'last_message', 'is_group']

    def get_is_group(self, obj):
        return obj.chat_type == 'group'

    def get_last_message(self, obj):
        msg = obj.messages.order_by('-id').first()
        if not msg:
            return None
        return {
            'id': msg.id,
            'content': (msg.content[:60] + '...') if msg.content and len(msg.content) > 60 else msg.content,
            'voice_note': msg.voice_note,
            'is_deleted': msg.is_deleted,
            'created_at': msg.created_at,
            'ago': timesince(msg.created_at, now()) + " ago",
            'sender': {
                'id': msg.sender_id,
                'first_name': msg.sender.first_name,
                'last_name': msg.sender.last_name
            }
        }


class ChatCreateSerializer(serializers.Serializer):
    """
    POST /chats/ with either:
      { "type": "direct", "office_id": <int> }
      { "type": "group", "name": "Team X", "office_ids": [..] }
    """
    type = serializers.ChoiceField(choices=[('direct','direct'), ('group','group')])
    office_id = serializers.IntegerField(required=False)
    name = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    office_ids = serializers.ListField(child=serializers.IntegerField(), required=False)

    def validate(self, data):
        user = self.context['request'].user
        if not user.office_id:
            raise serializers.ValidationError("Your account is not attached to an office.")

        if data['type'] == 'direct':
            if 'office_id' not in data:
                raise serializers.ValidationError("office_id is required for direct chat.")
            if data['office_id'] == user.office_id:
                raise serializers.ValidationError("Cannot create a direct chat with your own office.")
        else:
            if not data.get('office_ids'):
                raise serializers.ValidationError("office_ids is required for group chat.")
            if user.office_id not in data['office_ids']:
                data['office_ids'].append(user.office_id)
            if len(set(data['office_ids'])) < 2:
                raise serializers.ValidationError("A group must contain at least 2 offices.")
        return data


class ChatMessageSerializer(serializers.ModelSerializer):
    sender = serializers.SerializerMethodField()
    delivered_office_ids = serializers.SerializerMethodField()
    read_office_ids = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()

    class Meta:
        model = ChatMessage
        fields = [
            'id', 'chat', 'sender', 'content', 'voice_note',
            'created_at', 'updated_at', 'is_deleted',
            'delivered_office_ids', 'read_office_ids', 'can_edit'
        ]

    def get_sender(self, obj):
        return {
            'id': obj.sender_id,
            'first_name': obj.sender.first_name,
            'last_name': obj.sender.last_name,
            'office_id': getattr(obj.sender, 'office_id', None)
        }

    def get_delivered_office_ids(self, obj):
        return list(obj.delivered_to.values_list('id', flat=True))

    def get_read_office_ids(self, obj):
        return list(obj.read_by.values_list('id', flat=True))

    def get_can_edit(self, obj):
        user = self.context['request'].user if 'request' in self.context else None
        return obj.can_edit(user) if user else False


class VoiceNoteUploadSerializer(serializers.Serializer):
    file = serializers.FileField()

    def create(self, validated_data):
        from cloudinary.uploader import upload as cloudinary_upload
        upload = validated_data['file']
        ext = (upload.name.split('.')[-1] or '').lower()
        # Cloudinary treats audio under resource_type='video'
        result = cloudinary_upload(upload, resource_type='video')
        return {'url': result['secure_url']}
