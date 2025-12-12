from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    '''ПЕРЕОПРЕДЕЛЕННАЯ МОДЕЛЬ ПОЛЬЗОВАТЕЛЯ'''
    email = models.EmailField(unique=True, verbose_name='Email')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    first_name = models.CharField(blank=True, null=True, max_length=30, verbose_name='Имя')
    last_name = models.CharField(blank=True, null=True, max_length=30, verbose_name='Фамилия')
    club = models.CharField(blank=True, null=True, max_length=30, verbose_name='Клуб')
    city = models.CharField(blank=True, null=True, max_length=50, verbose_name='Город')
    photo = models.ImageField(upload_to='users/%Y/%m/%d/', blank=True, null=True, verbose_name='Фото')

    is_premium = models.BooleanField(default=True, verbose_name='Премиум-доступ')
    premium_until = models.DateField(blank=True, null=True, verbose_name='Подписка до')

    # вход по email
    USERNAME_FIELD = 'email'

    def __str__(self):
        return self.email
