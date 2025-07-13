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
]