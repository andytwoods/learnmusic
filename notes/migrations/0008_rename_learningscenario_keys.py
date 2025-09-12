from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("notes", "0007_alter_learningscenario_transpose_key"),
    ]

    operations = [
        migrations.RenameField(
            model_name="learningscenario",
            old_name="key",
            new_name="relative_key",
        ),
        migrations.RenameField(
            model_name="learningscenario",
            old_name="transpose_key",
            new_name="absolute_key",
        ),
    ]
