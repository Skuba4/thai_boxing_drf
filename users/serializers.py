from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from users.models import PremiumApplication

User = get_user_model()


class RegistrationSerializer(serializers.ModelSerializer):
    password1 = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ("email", "password1", "password2")

    def validate(self, data):
        if data["password1"] != data["password2"]:
            raise serializers.ValidationError({"password2": "Пароли не совпадают"})
        validate_password(data["password1"])

        return data

    def create(self, validated_data):
        return User.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password1"],
        )


class BaseInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        read_only_fields = ("email",)
        fields = (
            "first_name",
            "last_name",
            "email",
            "city",
            "club",
        )


class PremiumApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = PremiumApplication
        read_only_fields = ("is_premium",)
        fields = ("is_premium",)


class ExtendedInfoSerializer(BaseInfoSerializer):
    premium = PremiumApplicationSerializer(read_only=True, )

    class Meta(BaseInfoSerializer.Meta):
        fields = BaseInfoSerializer.Meta.fields + ("premium",)


class EmptySerializer(serializers.Serializer):
    pass
