from datetime import datetime
from django.core.mail import send_mail
from django.conf import settings
from .models import MailingAttempt


def send_mailing(mailing):
    if not (mailing.start_time <= datetime.now() <= mailing.end_time):
        raise ValueError('Рассылка не может быть отправлена сейчас')

    recipients = mailing.recipients.all()
    attempts = []
    for recipient in recipients:
        try:
            send_mail(
                subject=mailing.message.subject,
                message=mailing.message.body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient.email],
                fail_silently=False,
            )
            attempts.append(MailingAttempt(
                status='success',
                server_response='Письмо успешно отправлено',
                mailing=mailing,
            ))
        except Exception as e:
            attempts.append(MailingAttempt(
                status='failed',
                server_response=str(e),
                mailing=mailing,
            ))
    MailingAttempt.objects.bulk_create(attempts)
    mailing.status = 'completed'
    mailing.save()