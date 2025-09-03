from django.urls import path
from . import views


urlpatterns = [
    path('signup/', views.UserSignupView.as_view(), name='signup'),
    path('login/', views.UserLoginView.as_view(), name='login'),
    path('me/', views.UserMeView.as_view(), name='me'),
    path('offices/', views.OfficeListView.as_view(), name='office-list'),
    path('documents/send/', views.DocumentUploadView.as_view(), name='document-send'),
    path('documents/sent/', views.SentFilesView.as_view(), name='sent-files'),
    path('documents/received/', views.ReceivedFilesView.as_view(), name='received-files'),
    path('documents/recent/', views.RecentFilesView.as_view(), name='recent-files'),
    path('documents/<int:pk>/delete/', views.DocumentDeleteView.as_view(), name='document-delete'),
    path('documents/markasread/<int:pk>/', views.MarkDocumentAsReadView.as_view(), name='markasread'),
]
######################################################3
#       INAPP CHATTING ROUTES
######################################################
from .views import (
    ChatListCreateView, ChatDetailView, ChatMessagesView,
    ChatSendMessageView, ChatEditMessageView, ChatDeleteMessageForAllView,
    ChatDeleteMessageForMeView, VoiceNoteUploadView
)

urlpatterns += [
    path('chat/chats/', ChatListCreateView.as_view(), name='chat-list-create'),
    path('chat/chats/<int:pk>/', ChatDetailView.as_view(), name='chat-detail'),
    path('chat/chats/<int:chat_id>/messages/', ChatMessagesView.as_view(), name='chat-messages'),
    path('chat/messages/send/', ChatSendMessageView.as_view(), name='chat-send-message'),  # optional HTTP
    path('chat/messages/<int:pk>/edit/', ChatEditMessageView.as_view(), name='chat-edit-message'),
    path('chat/messages/<int:pk>/delete-all/', ChatDeleteMessageForAllView.as_view(), name='chat-delete-for-all'),
    path('chat/messages/delete-for-me/', ChatDeleteMessageForMeView.as_view(), name='chat-delete-for-me'),
    path('chat/voice/upload/', VoiceNoteUploadView.as_view(), name='chat-voice-upload'),
]
