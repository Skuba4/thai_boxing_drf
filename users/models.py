import uuid
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUserManager(BaseUserManager):
    """Менеджер пользователя с авторизацией по email вместо username"""

    use_in_migrations = True

    def create_user(self, email, password=None, **extra_fields):
        """Создать обычного пользователя с email и паролем"""
        if not email:
            raise ValueError("Email обязателен.")
        if not password:
            raise ValueError("Пароль обязателен.")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Создать суперпользователя с правами staff и superuser"""
        if not password:
            raise ValueError("Superuser должен иметь пароль.")

        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser должен иметь is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser должен иметь is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """Переопределенная модель пользователей"""

    username = None

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    email = models.EmailField(unique=True)
    photo = models.ImageField(upload_to="users/%Y/%m/%d/", blank=True)

    city = models.CharField(max_length=50, blank=True)
    club = models.CharField(max_length=30, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []
    objects = CustomUserManager()

    def __str__(self):
        first = f"{self.first_name[0]}." if self.first_name else ""

        return f"{self.last_name} {first} ({self.email}, {self.club}-{self.city})"


class PremiumApplication(models.Model):
    """Заявка на премиум доступ"""

    class Status(models.TextChoices):
        WAIT = "0", "Ожидает"
        YES = "Y", "Одобрено"
        NO = "N", "Отказано"

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="premium_application",
        verbose_name="ФИО",
    )
    status = models.CharField(max_length=1, choices=Status, default=Status.WAIT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Заявка пользователя"
        verbose_name_plural = "Заявки пользователя"

    def __str__(self):
        return f"({self.created_at}): {self.user}, {self.status}"
