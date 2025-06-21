from django.urls import path
from . import views


urlpatterns = [
    path('signup/', views.UserSignupView.as_view(), name='signup'),
    path('login/', views.UserLoginView.as_view(), name='login'),
    path('me/', views.UserMeView.as_view(), name='me'),
    path('offices/', views.OfficeListView.as_view(), name='office-list'),
]