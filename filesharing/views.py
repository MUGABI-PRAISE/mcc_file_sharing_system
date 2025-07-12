from django.shortcuts import render
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView # view for handling HTTP requests
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import login, logout
from .serializers import UserSignupSerializer, UserLoginSerializer, UserSerializer, OfficeSerializer, DocumentUploadSerializer, ReceivedDocumentSerializer# our serializers
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import permissions
from rest_framework import generics 
from .models import Office, Document, DocumentRecipient


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
    '''class based views. their inheritence of the CreateAPIView makes them require less inputs 
     to do great things.'''
    queryset = Document.objects.all()
    serializer_class = DocumentUploadSerializer
    permission_classes = [permissions.IsAuthenticated]


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
        user_office = self.request.user.office
        return DocumentRecipient.objects.filter(
            recipient_office=user_office,
            is_deleted=False
        ).order_by('-received_at')


#8. recent few(4) documents
class RecentFilesView(generics.ListAPIView):
    serializer_class = ReceivedDocumentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user_office = self.request.user.office
        return DocumentRecipient.objects.filter(
            recipient_office=user_office,
            is_deleted=False
        ).order_by('-received_at')[:4] # return the latest four

# Create your views here.
