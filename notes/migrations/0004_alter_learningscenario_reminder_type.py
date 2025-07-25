# Generated by Django 5.2.1 on 2025-06-27 08:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notes', '0003_learningscenario_reminder_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='learningscenario',
            name='reminder_type',
            field=models.CharField(blank=True, choices=[('AL', 'All notifications'), ('EM', 'Email'), ('PN', 'Push notification'), ('NO', 'No reminder')], default='NO', max_length=2, null=True, verbose_name='Daily reminder'),
        ),
    ]
