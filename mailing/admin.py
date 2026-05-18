from django.contrib import admin
from .models import Client, Message, Mailing, MailingAttempt

admin.site.register(Client)
admin.site.register(Message)
admin.site.register(Mailing)
admin.site.register(MailingAttempt)
