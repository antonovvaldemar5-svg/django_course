from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone

User = get_user_model()


class Client(models.Model):
    email = models.EmailField(unique=True, verbose_name='Email')
    full_name = models.CharField(max_length=200, verbose_name='Ф. И. О.')
    comment = models.TextField(blank=True, verbose_name='Комментарий')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='clients', verbose_name='Владелец')

    class Meta:
        verbose_name = 'Клиент'
        verbose_name_plural = 'Клиенты'

    def __str__(self):
        return self.email


class Message(models.Model):
    subject = models.CharField(max_length=255, verbose_name='Тема письма')
    body = models.TextField(verbose_name='Тело письма')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='messages', verbose_name='Владелец')

    class Meta:
        verbose_name = 'Сообщение'
        verbose_name_plural = 'Сообщения'

    def __str__(self):
        return self.subject


class Mailing(models.Model):
    start_time = models.DateTimeField(verbose_name='Дата и время начала')
    end_time = models.DateTimeField(verbose_name='Дата и время окончания')
    status = models.CharField(
        max_length=20,
        choices=[
            ('created', 'Создана'),
            ('started', 'Запущена'),
            ('completed', 'Завершена'),
        ],
        default='created',
        verbose_name='Статус'
    )
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='mailings', verbose_name='Сообщение')
    recipients = models.ManyToManyField(Client, related_name='mailings', verbose_name='Получатели')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mailings', verbose_name='Владелец')

    class Meta:
        verbose_name = 'Рассылка'
        verbose_name_plural = 'Рассылки'

    def __str__(self):
        return f'{self.message.subject} ({self.start_time} - {self.end_time})'

    def clean(self):
        if self.start_time >= self.end_time:
            raise ValidationError('Дата начала должна быть раньше даты окончания')
        if self.start_time < timezone.now():
            raise ValidationError('Дата начала не может быть в прошлом')

    def save(self, *args, **kwargs):
        self.full_clean()
        self.update_status()
        super().save(*args, **kwargs)

    def update_status(self):
        now = timezone.now()
        if now < self.start_time:
            self.status = 'created'
        elif self.start_time <= now <= self.end_time:
            self.status = 'started'
        else:
            self.status = 'completed'

    @property
    def status_display(self):
        now = timezone.now()
        if now < self.start_time:
            return 'created'
        elif self.start_time <= now <= self.end_time:
            return 'started'
        else:
            return 'completed'

    @property
    def success_attempts(self):
        return self.attempts.filter(status='success').count()

    @property
    def failed_attempts(self):
        return self.attempts.filter(status='failed').count()


class MailingAttempt(models.Model):
    attempt_time = models.DateTimeField(auto_now_add=True, verbose_name='Дата и время попытки')
    status = models.CharField(
        max_length=20,
        choices=[
            ('success', 'Успешно'),
            ('failed', 'Не успешно'),
        ],
        verbose_name='Статус'
    )
    server_response = models.TextField(blank=True, verbose_name='Ответ почтового сервера')
    mailing = models.ForeignKey(Mailing, on_delete=models.CASCADE, related_name='attempts', verbose_name='Рассылка')

    class Meta:
        verbose_name = 'Попытка отправки'
        verbose_name_plural = 'Попытки отправки'

    def __str__(self):
        return f'{self.mailing} - {self.status} ({self.attempt_time})'