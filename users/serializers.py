from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.utils import timezone

from users.models import User


# ? Profile Image Serializer
class ProfileImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['profile_image']


# ? General User Serializer (used for listing basic info)
class UserSerializer(serializers.ModelSerializer):
    profile_image = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'user_type', 'profile_image']

    def get_profile_image(self, obj):
        request = self.context.get('request')
        if obj.profile_image and request:
            return request.build_absolute_uri(obj.profile_image.url)
        return None


# ? Custom Token Serializer for Login Response
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['user_type'] = user.user_type
        token['email'] = user.email
        token['gender'] = user.gender
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        self.user.is_online = True
        self.user.last_seen = timezone.now()
        self.user.save(update_fields=['is_online', 'last_seen'])

        data.update({
            'user': {
                'id': self.user.id,
                'full_name': getattr(self.user, 'full_name', self.user.username),
                'email': self.user.email,
                'role': self.user.user_type,
                'profile_image': self.user.profile_image.url if self.user.profile_image else None,
                'is_online': self.user.is_online,
                'last_seen': self.user.last_seen,
            }
        })
        return data


# ? Register Serializer
class RegisterSerializer(serializers.ModelSerializer):
    confirm_password = serializers.CharField(write_only=True)
    email = serializers.EmailField(required=True)

    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'password',
            'confirm_password',
            'user_type',
            'gender',
            'profile_image',
        ]
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({
                'confirm_password': "Passwords do not match."
            })
        validate_password(data['password'])  # Django's built-in validation
        return data

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            user_type=validated_data.get('user_type', 'student'),
            gender=validated_data.get('gender', ''),
            profile_image=validated_data.get('profile_image')
        )
        return user


# ? Login Serializer
class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')

        if email and password:
            user = authenticate(email=email, password=password)
            if not user:
                raise serializers.ValidationError("Invalid email or password.")
        else:
            raise serializers.ValidationError("Both email and password are required.")
        data['user'] = user
        return data
