from django.templatetags.static import static
from django.urls import reverse
from webpush import send_user_notification


def send_notification(user):
    payload = {"head": "Reminder to practice!",
               "body": "",
               "icon": static('images/favicons/android-chrome-192x192.png'),
               "url": reverse('notes-home')}

    send_user_notification(user=user, payload=payload, ttl=1000)
