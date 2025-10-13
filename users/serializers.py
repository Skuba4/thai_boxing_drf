from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['email', 'password']

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("User with this email already exists")
        return value

    def create(self, validated_data):
        # Если username не передан — сгенерируем на основе email
        if 'username' not in validated_data:
            validated_data['username'] = validated_data['email'].split('@')[0]
        return User.objects.create_user(**validated_data)
