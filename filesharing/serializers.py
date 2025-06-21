from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate
from .models import Office

##########################################################################
#   SERIALIZERS FOR USER MODEL. HANDLES AUTHENTICATION AND REGISTRATION
##########################################################################
User = get_user_model() # substitute for importing the user model
# general pourpose.
class UserSerializer(serializers.ModelSerializer):
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
