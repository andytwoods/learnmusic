"""
Tasks for sending web push notifications.
"""
from datetime import datetime
from zoneinfo import ZoneInfo

from django.utils import timezone
from huey import crontab
from huey.contrib.djhuey import db_periodic_task
# Removed webpush import
from learnmusic.users.models import User
from notes.models import NoteRecord


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

    # Get all users who have reminders enabled
    users_with_reminders = User.objects.filter(
        user_profile__reminder_time__isnull=False
    ).exclude(
        user_profile__reminder_time="DISABLED"
    )

    # Get the current date (in UTC)
    today = timezone.now().date()
    reminders_sent = 0

    # Get the current time in UTC
    now_utc = timezone.now()
    current_utc_time = now_utc.strftime("%H:%M")

    # For each user, check if it's time to send a reminder
    for user in users_with_reminders:
        profile = user.profile

        # Get the user's reminder time (already in UTC)
        reminder_time = profile.reminder_time

        # Check if current UTC time matches the reminder time (with a small buffer)
        # We're using huey to run this function once a minute, but we still want to
        # check if it's the right time based on the UTC reminder time
        if abs(int(current_utc_time.split(":")[0]) - int(reminder_time.split(":")[0])) > 1:
            # Not within an hour of the reminder time, skip this user
            continue

        # Check if a reminder has already been sent today
        if profile.reminder_sent and profile.reminder_sent.date() == today:
            print(f"Reminder already sent to {user.email} today")
            continue

        # Check if the user has already practiced today
        # Get all NoteRecord entries for this user from today
        today_records = NoteRecord.objects.filter(
            learningscenario__user=user,
            created__date=today
        )

        if today_records.exists():
            print(f"User {user.email} has already practiced today, skipping reminder")
            continue

        # If we get here, the user hasn't received a reminder today and hasn't practiced today
        # Prepare the notification payload
        payload = {
            "head": "Time to Practice!",
            "body": "Don't forget to practice your musical skills today!",
            "icon": "/static/favicon/android-chrome-192x192.png",
            "url": "/practice/",
            "data": {
                "url": "/practice/"
            }
        }

        # Send the notification (webpush removed)
        # Update the reminder_sent field
        profile.reminder_sent = timezone.now()
        profile.save()
        reminders_sent += 1
        print(f"Would have sent reminder to {user.email} (webpush removed)")

    print(f"Reminder task completed. Processed {users_with_reminders.count()} users, sent {reminders_sent} reminders.")
