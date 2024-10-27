from rest_framework import serializers
from .models import User
from .services import AuthService

class UserRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ( 'email','username', 'password', )
        # fields = ('email', 'username', 'password', 'first_name', 'last_name', 'last_ip','last_location')
        extra_kwargs = {'password': {'write_only': True}}
        
    def validate(self, attrs):
        if User.objects.filter(username=attrs['username']).exists() or User.objects.filter(email=attrs['email']).exists():
                return False
        return attrs
    
class UserLoginSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ( 'email','username', 'password', )

        
    username = serializers.CharField(required=False) # you need more validatoin and stuff
    email = serializers.EmailField(required=False)
    password = serializers.CharField(style={'input_type': 'password'}, write_only=True)

    def validate(self, attrs):
        username = attrs.get('username')
        email = attrs.get('email')
        password = attrs.get('password')

        if not (username and email):
            raise serializers.ValidationError("Both 'username' and 'email' are required.")

        if not password:
            raise serializers.ValidationError("Password is required.")

        try:
            user = User.objects.get(username=username, email = email)
        except User.DoesNotExist:
            raise serializers.ValidationError("No user found with the given credentials.")

        if not user.check_password(password):
            raise serializers.ValidationError("Incorrect password.")

        attrs['user'] = user
        return attrs

class APITokenObtainSerializer(serializers.Serializer):
    client_id = serializers.CharField(required=False)

    def validate(self, attrs):
        client_id = attrs.get('client_id')
        return AuthService.generate_api_tokens(client_id)

class TokenRefreshSerializer(serializers.Serializer): # NOT GONNA USE FOR NOW
    refresh = serializers.CharField()
    access = serializers.CharField(read_only=True)

    def validate(self, attrs):
        refresh = attrs.get('refresh')
        if not refresh:
            raise serializers.ValidationError('Refresh token not provided')
        try:
            return AuthService.refresh_token(refresh)
        except ValueError as e:
            raise serializers.ValidationError(str(e))