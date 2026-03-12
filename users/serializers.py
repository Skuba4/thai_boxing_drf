from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class RegistrationSerializer(serializers.ModelSerializer):
    password1 = serializers.CharField(write_only=True, min_length=4)
    password2 = serializers.CharField(write_only=True, min_length=4)

    class Meta:
        model = User
        fields = ("email", "password1", "password2")

    def validate(self, data):
        if data["password1"] != data["password2"]:
            raise serializers.ValidationError({"password2": "Пароли не совпадают"})
        return data

    def create(self, validated_data):
        return User.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password1"],
        )


class UserInfoSerializer(serializers.ModelSerializer):
    is_premium = serializers.SerializerMethodField()

    class Meta:
        model = User
        read_only_fields = ("email",)
        fields = (
            "first_name",
            "last_name",
            "middle_name",
            "email",
            "city",
            "club",
            "is_premium",
        )

    def get_is_premium(self, obj):
        application = getattr(obj, "premium_application", False)
        return application and application.status == "Y"
