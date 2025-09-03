from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView # view for handling HTTP requests
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.exceptions import PermissionDenied
from django.contrib.auth import login, logout
from .serializers import UserSignupSerializer, UserLoginSerializer, UserSerializer, OfficeSerializer, DocumentUploadSerializer, ReceivedDocumentSerializer, ChatSerializer, ChatCreateSerializer, ChatMessageSerializer, VoiceNoteUploadSerializer
from django.utils.timezone import now
from .models import Office, Document, DocumentRecipient, Chat, ChatParticipant, ChatMessage, ChatMessageHide
from rest_framework import generics, permissions, status
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework_simplejwt.tokens import RefreshToken


# realtime pourposes
from .realtime import send_to_office, send_to_user
from django.utils.timezone import localtime




# 1. User Signup View
class UserSignupView(APIView):
    permission_classes = [AllowAny] # anyone can access this view

    def post(self, request):
        print(request.data)
        serializer = UserSignupSerializer(data=request.data) # deserialization
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                "message": "User registered successfully",
                # "user": UserSerializer(user).data
            }, status=status.HTTP_201_CREATED)
        print("Serializer errors:", serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# 2. User Login View
class UserLoginView(APIView):
    permission_classes = [AllowAny] # anyone can access this view

    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']

            # Issue JWT token
            refresh = RefreshToken.for_user(user)

            return Response({
                "message": "Login successful",
                "user": UserSerializer(user).data,
                "access": str(refresh.access_token),
                "refresh": str(refresh)
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_401_UNAUTHORIZED)


# 3. Get current authenticated user
#handles editing of users
class UserMeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user) # serialization
        return Response(serializer.data) # returns json


    # patch allows partial edits
    def patch(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    # you must be editing the whole user object to use put.
    def put(self, request):
        serializer = UserSerializer(request.user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    

# 4.  handle offices
class OfficeListView(generics.ListAPIView):
    queryset = Office.objects.all()
    serializer_class = OfficeSerializer
    permission_classes = [permissions.AllowAny]


# 5. send a file.
class DocumentUploadView(generics.CreateAPIView):
    queryset = Document.objects.all()
    serializer_class = DocumentUploadSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        document = serializer.save()  # your serializer.create does Cloudinary upload + recipients

        # Build a minimal broadcast payload (you can shape this however you want)
        payload_base = {
            "document_id": document.id,
            "document_title": document.document_title,
            "message": document.message,
            "file_url": document.file,
            "file_type": document.file_type,
            "file_size": document.file_size,
            "sender": {
                "id": document.sender_id,
                "first_name": document.sender.first_name,
                "last_name": document.sender.last_name,
            },
            "timestamp": localtime(document.timestamp).isoformat(),
        }

        # Notify each recipient office
        recipients = DocumentRecipient.objects.filter(document=document).select_related("recipient_office")
        for dr in recipients:
            payload = {
                **payload_base,
                "recipient": {
                    "document_recipient_id": dr.id,
                    "office_id": dr.recipient_office_id,
                    "office_name": dr.recipient_office.name,
                    "received_at": localtime(dr.received_at).isoformat(),
                }
            }
            send_to_office(dr.recipient_office_id, "file.shared", payload)

        # Optionally, notify the sender’s personal channel (useful for “sent” list updates)
        send_to_user(document.sender_id, "file.shared", {**payload_base, "recipient_count": recipients.count()})



# 6. sent files.
class SentFilesView(generics.ListAPIView):
    serializer_class = DocumentUploadSerializer
    permission_classes = [permissions.IsAuthenticated]

    #return documents in reverse order
    def get_queryset(self):
        return Document.objects.filter(sender=self.request.user, deleted_by_sender=False).order_by('-timestamp')


# 7. received documents.
class ReceivedFilesView(generics.ListAPIView):
    serializer_class = ReceivedDocumentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # ✅ Get the office of the currently logged-in user
        user_office = self.request.user.office

        # ✅ Query the DocumentRecipient table
        # - Filter: Only files sent to this user's office, and not deleted
        # - Use select_related to optimize performance when accessing document fields
        # - Order:
        #     1. Unread files first (is_read = False)
        #     2. Within that, most recent files first by received_at
        return DocumentRecipient.objects.select_related('document').filter(
            recipient_office=user_office,
            is_deleted=False
        ).order_by('is_read', '-received_at')  # ✅ Unread first, because false < true then recent




#8. recent few(4) documents
class RecentFilesView(generics.ListAPIView):
    serializer_class = ReceivedDocumentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user_office = self.request.user.office
        return DocumentRecipient.objects.select_related('document').filter(
            recipient_office=user_office,
            is_deleted=False
        ).order_by('-received_at')[:4] # return the latest four


#9. delete a document.
class DocumentDeleteView(generics.DestroyAPIView):
    queryset = Document.objects.all()
    serializer_class = DocumentUploadSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        doc = super().get_object()
        # Enforce sender-only delete if you want:
        # if doc.sender_id != self.request.user.id:
        #     raise PermissionDenied("You do not have permission to delete this document.")
        return doc

    def perform_destroy(self, instance):
        # Collect recipients before deletion
        recipients = list(DocumentRecipient.objects.filter(document=instance).values_list("recipient_office_id", flat=True))
        sender_id = instance.sender_id
        doc_id = instance.id
        super().perform_destroy(instance)

        payload = {"document_id": doc_id}
        for office_id in recipients:
            send_to_office(office_id, "file.deleted", payload)
        send_to_user(sender_id, "file.deleted", payload)



# 10. mark a file as read
'''
    note that we are not using a serializer here. DRF only recommends using a serializer when
    Creating a new object	
    Validating input data	
    Updating many fields	
    Returning complex nested responses

    however if you want, you can use it.
'''

class MarkDocumentAsReadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, pk):
        try:
            recipient = DocumentRecipient.objects.select_related("document", "recipient_office").get(
                pk=pk,
                recipient_office=request.user.office,
                is_deleted=False
            )
        except DocumentRecipient.DoesNotExist:
            return Response({'detail': 'File not found or access denied.'}, status=404)

        if not recipient.is_read:
            recipient.is_read = True
            recipient.save()

            payload = {
                "document_id": recipient.document_id,
                "document_recipient_id": recipient.id,
                "reader_office_id": recipient.recipient_office_id,
                "reader_office_name": recipient.recipient_office.name,
            }
            # Notify the sender that someone read their file
            send_to_user(recipient.document.sender_id, "file.read", payload)

        return Response({'message': 'Marked as read successfully.'}, status=200)

########################################################################3
#             IN APP CHATTING VIEWS
#########################################################################
# --- CHAT VIEWS (new) ---
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.db.models import Q
from django.shortcuts import get_object_or_404
from .models import Chat, ChatParticipant, ChatMessage, Office, ChatMessageHide
from .serializers import ChatSerializer, ChatCreateSerializer, ChatMessageSerializer, VoiceNoteUploadSerializer
from .realtime import send_to_user
from django.utils.timezone import now

class ChatListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ChatSerializer

    def get_queryset(self):
        user = self.request.user
        if not user.office_id:
            return Chat.objects.none()
        return Chat.objects.filter(participants=user.office).prefetch_related('participants').order_by('-created_at')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ChatCreateSerializer
        return ChatSerializer

    def create(self, request, *args, **kwargs):
        user = request.user
        data = request.data.copy()
        ser = ChatCreateSerializer(data=data, context={'request': request})
        ser.is_valid(raise_exception=True)
        payload = ser.validated_data

        if payload['type'] == 'direct':
            my_office = user.office
            other_office = get_object_or_404(Office, pk=payload['office_id'])

            # Try to find existing direct chat with exactly these two offices
            existing = Chat.objects.filter(
                chat_type='direct',
                participants=my_office
            ).filter(participants=other_office).distinct().first()

            if existing:
                return Response(ChatSerializer(existing).data, status=200)

            chat = Chat.objects.create(
                chat_type='direct',
                name=None,
                created_by=user
            )
            ChatParticipant.objects.bulk_create([
                ChatParticipant(chat=chat, office=my_office),
                ChatParticipant(chat=chat, office=other_office),
            ])
            return Response(ChatSerializer(chat).data, status=201)

        # group
        office_ids = list(set(payload['office_ids']))
        offices = list(Office.objects.filter(id__in=office_ids))
        if len(offices) != len(office_ids):
            return Response({'detail': 'Some offices not found.'}, status=400)

        chat = Chat.objects.create(
            chat_type='group',
            name=payload.get('name') or 'New Group',
            created_by=user
        )
        ChatParticipant.objects.bulk_create([ChatParticipant(chat=chat, office=o) for o in offices])
        return Response(ChatSerializer(chat).data, status=201)


class ChatDetailView(generics.RetrieveAPIView):
    queryset = Chat.objects.all().prefetch_related('participants')
    serializer_class = ChatSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        chat = super().get_object()
        user = self.request.user
        if not user.office_id or user.office not in chat.participants.all():
            self.permission_denied(self.request, message="Not a participant.")
        return chat


class ChatMessagesView(generics.ListAPIView):
    """
    GET chat history. Also marks messages as delivered for the caller's office.
    """
    serializer_class = ChatMessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        chat_id = self.kwargs['chat_id']
        user = self.request.user
        chat = get_object_or_404(Chat, id=chat_id)

        if not user.office_id or user.office not in chat.participants.all():
            self.permission_denied(self.request, message="Not a participant.")

        # Hide messages user chose to hide (direct chat other people's messages only)
        hidden_ids = ChatMessageHide.objects.filter(user=user).values_list('message_id', flat=True)
        qs = ChatMessage.objects.filter(chat=chat).exclude(id__in=hidden_ids).select_related('sender').order_by('id')

        # Mark as delivered for this office (for messages from other offices)
        other_msgs = qs.exclude(sender__office=user.office)
        undelivered = other_msgs.exclude(delivered_to=user.office)
        for msg in undelivered:
            msg.delivered_to.add(user.office)

        return qs


class ChatSendMessageView(generics.CreateAPIView):
    """
    Optional HTTP send (WebSocket also supported).
    """
    serializer_class = ChatMessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        user = request.user
        chat_id = request.data.get('chat')
        content = request.data.get('content', '')
        voice_note = request.data.get('voice_note', None)

        chat = get_object_or_404(Chat, id=chat_id)
        if not user.office_id or user.office not in chat.participants.all():
            self.permission_denied(request, message="Not a participant.")

        if not content and not voice_note:
            return Response({'detail': 'Content or voice_note required.'}, status=400)

        msg = ChatMessage.objects.create(chat=chat, sender=user, content=content, voice_note=voice_note)

        # Delivery: mark delivered for all recipient offices (everyone except sender office)
        recipient_offices = chat.participants.exclude(id=user.office_id)
        for off in recipient_offices:
            msg.delivered_to.add(off)

        ser = ChatMessageSerializer(msg, context={'request': request})
        return Response(ser.data, status=201)


class ChatEditMessageView(generics.UpdateAPIView):
    queryset = ChatMessage.objects.all()
    serializer_class = ChatMessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def update(self, request, *args, **kwargs):
        msg = self.get_object()
        if msg.sender_id != request.user.id:
            return Response({'detail': 'Cannot edit others messages.'}, status=403)
        if not msg.can_edit(request.user):
            return Response({'detail': 'Edit window expired (15 min).'}, status=400)
        new_content = request.data.get('content', '')
        msg.content = new_content
        msg.updated_at = now()
        msg.save()
        return Response(ChatMessageSerializer(msg, context={'request': request}).data, status=200)


class ChatDeleteMessageForAllView(generics.DestroyAPIView):
    queryset = ChatMessage.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def destroy(self, request, *args, **kwargs):
        msg = self.get_object()
        chat = msg.chat
        if msg.sender_id != request.user.id:
            return Response({'detail': 'Only sender can delete for all.'}, status=403)
        msg.is_deleted = True
        msg.save()
        return Response({'message': 'Deleted for everyone.'}, status=200)


class ChatDeleteMessageForMeView(generics.CreateAPIView):
    """
    Direct chats only: a user can hide other people's messages locally.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        msg_id = request.data.get('message_id')
        msg = get_object_or_404(ChatMessage, id=msg_id)
        if msg.chat.chat_type != 'direct':
            return Response({'detail': 'Delete for me is only allowed in direct chats.'}, status=400)
        if msg.sender_id == request.user.id:
            return Response({'detail': 'Use delete-for-all for your own message.'}, status=400)
        ChatMessageHide.objects.get_or_create(message=msg, user=request.user)
        return Response({'message': 'Hidden for you.'}, status=200)


class VoiceNoteUploadView(generics.CreateAPIView):
    """
    Upload an audio blob and get back a Cloudinary URL.
    """
    serializer_class = VoiceNoteUploadSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        ser = VoiceNoteUploadSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        result = ser.create(ser.validated_data)
        return Response(result, status=201)
