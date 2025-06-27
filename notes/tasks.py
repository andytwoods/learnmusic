"""
Tasks for sending web push notifications.
"""
from datetime import datetime
from zoneinfo import ZoneInfo

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.mail import send_mail
from django.urls import reverse
from django.utils import timezone
from huey import crontab
from huey.contrib.djhuey import db_periodic_task
from pushover_complete import PushoverAPI

# Removed webpush import
from learnmusic.users.models import User
from notes.models import NoteRecord, LearningScenario


# Schedule the send_reminders task to run once a minute
@db_periodic_task(crontab(minute='*'))
def scheduled_send_reminders():
    send_reminders()


def send_reminders():
    """
    Send practice reminders to users based on their reminder settings.
    Only sends reminders if:
    1. The user hasn't already received a reminder today
    2. The user hasn't practiced today (no NoteRecord entries for today)

    Note: Reminder times are stored in UTC in the database, and the comparison
    is done directly with the current UTC time. The user's timezone is only used
    for display purposes in the UI.
    """

    # Get all learning scenarios with reminders enabled
    learning_scenarios_with_reminders = LearningScenario.objects.filter(
        reminder__isnull=False,
        reminder_type__in=['AL', 'EM', 'PN']  # All notifications, Email, Push notification
    ).prefetch_related('user',)

    # Get the current date (in UTC)
    today = timezone.now().date()
    reminders_sent = 0

    # Get the current time in UTC
    now_utc = timezone.now()
    current_hour = now_utc.hour

    p = PushoverAPI(settings.PUSHOVER_APP_TOKEN)

    # For each learning scenario, check if it's time to send a reminder
    for scenario in learning_scenarios_with_reminders:
        user = scenario.user

        # Get the reminder time (already in UTC)
        reminder_datetime = scenario.reminder

        # Check if current UTC time matches the reminder time (with a small buffer)
        # We're using huey to run this function once a minute, but we still want to
        # check if it's the right time based on the UTC reminder time
        if abs(current_hour - reminder_datetime.hour) > 1:
            # Not within an hour of the reminder time, skip this scenario
            continue

        # Check if a reminder has already been sent today
        if scenario.reminder_sent and scenario.reminder_sent.date() == today:
            print(f"Reminder already sent for scenario {scenario.id} to {user.email} today")
            continue

        # Check if the user has already practiced today
        # Get all NoteRecord entries for this user from today
        today_records = NoteRecord.objects.filter(
            learningscenario=scenario,
            created__date=today
        )

        if today_records.exists():
            print(f"User {user.email} has already practiced today, skipping reminder")
            continue

        # If we get here, the user hasn't received a reminder today and hasn't practiced today


        practice_url = f"https://{settings.DOMAIN}{reverse('practice', args=[scenario.id])}"

        if scenario.reminder_type in ['PN', 'Al']:
            p.send_message(user.pushover_key, message="This link will take you straight to your practice session", title="Reminder to practice", url=practice_url)
        if scenario.reminder_type in ['EM', 'Al']:
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

        scenario.reminder_sent = timezone.now()
        scenario.save()
        reminders_sent += 1



    print(f"Reminder task completed. Processed {learning_scenarios_with_reminders.count()} learning scenarios, sent {reminders_sent} reminders.")
