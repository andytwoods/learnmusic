"""
Tasks for sending web push notifications and maintenance tasks.
"""
import logging
from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.db.models import Max
from django.urls import reverse
from django.utils import timezone
from huey import crontab
from huey.contrib.djhuey import db_periodic_task
from pushover_complete import PushoverAPI

from notes.models import LearningScenario

logger = logging.getLogger(__name__)




# Schedule the send_reminders task to run once a minute
@db_periodic_task(crontab(minute='*/2'))
def scheduled_send_reminders():
    send_reminders()


def send_reminders():
    """
    Send practice reminders to users based on their reminder settings.
    Only sends reminders if:
    1. The reminder is at least 24 hours old (ensuring reminders are only sent once a day)
    2. The user hasn't practiced today (no NoteRecord entries for today)

    After sending a reminder, the reminder time is updated to 24 hours later,
    which ensures that the next reminder won't be sent until at least 24 hours have passed.

    Note: Reminder times are stored in UTC in the database, and the comparison
    is done directly with the current UTC time. The user's timezone is only used
    for display purposes in the UI.
    """

    # Get all learning scenarios with reminders enabled
    # Only get scenarios where reminder is not null and is older than current now_utc
    now_utc = timezone.now()
    cutoff = now_utc - timedelta(hours=24)


    learning_scenarios_with_reminders = LearningScenario.objects.filter(
        reminder__isnull=False,
        # This ensures reminders are only sent once a day
        reminder__lte=now_utc,
        reminder_type__in=['AL', 'EM', 'PN']  # All notifications, Email, Push notification
    ).select_related('user').annotate(last_practice=Max("noterecord__created"))

    reminders_sent = 0

    p = PushoverAPI(settings.PUSHOVER_APP_TOKEN)

    # For each learning scenario, check if it's time to send a reminder
    for scenario in learning_scenarios_with_reminders:

        scenario.reminder += timedelta(hours=24)
        scenario.save()

        practised_recently = scenario.last_practice is not None and scenario.last_practice > cutoff

        if not practised_recently:
            user = scenario.user

            practice_url = f"https://{settings.DOMAIN}{reverse('practice', args=[scenario.id])}"

            if scenario.reminder_type in ['PN', 'AL']:
                p.send_message(user.pushover_key, message="This link will take you straight to your practice session", title="Reminder to practice", url=practice_url)
            if scenario.reminder_type in ['EM', 'AL']:
                # Send email instead of Pushover notification
                subject = f"{settings.EMAIL_SUBJECT_PREFIX}Reminder to practice"
                message = f"This link will take you straight to your practice session: {practice_url}"
                html_message = f"""
                <html>
                    <body>
                        <h2>Reminder to practice</h2>
                        <p>It's time for your daily practice session!</p>
                        <p><a href="{practice_url}">Click here to start practicing</a></p>
                    </body>
                </html>
                """
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    html_message=html_message,
                    fail_silently=False,
                )

            reminders_sent += 1


    logger.info(f"Reminder task completed. Processed {learning_scenarios_with_reminders.count()} learning scenarios, sent {reminders_sent} reminders.")


