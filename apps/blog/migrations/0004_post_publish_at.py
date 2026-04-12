# Generated manually — model had publish_at without migration

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("blog", "0003_alter_post_status"),
    ]

    operations = [
        migrations.AddField(
            model_name="post",
            name="publish_at",
            field=models.DateTimeField(
                blank=True,
                help_text="Set with status=scheduled to auto-publish at this time.",
                null=True,
                verbose_name="publish at",
            ),
        ),
    ]
