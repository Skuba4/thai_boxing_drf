import uuid
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("Email обязателен.")
        if not password:
            raise ValueError("Пароль обязателен.")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        if not email:
            raise ValueError("Email обязателен.")
        if not password:
            raise ValueError("Пароль обязателен.")

        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser должен быть is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser должен быть is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    username = None

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    email = models.EmailField(unique=True, blank=False)
    photo = models.ImageField(upload_to="users/%Y/%m/%d/", blank=True)

    city = models.CharField(max_length=30, blank=True)
    club = models.CharField(max_length=30, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []
    objects = CustomUserManager()

    def __str__(self):
        return (
            f"{self.last_name} {self.first_name},\n"
            f"{self.city}-{self.club},\n"
            f"{self.email}"
        )


class PremiumApplication(models.Model):
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Создано",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Обновлено",
    )
    is_premium = models.BooleanField(
        default=False,
        verbose_name="Премиум",
    )
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="premium",
        verbose_name="Пользователь",
    )

    class Meta:
        verbose_name = "заявку"
        verbose_name_plural = "Заявки"
