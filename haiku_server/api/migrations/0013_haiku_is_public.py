from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0012_profile_nickname_optional'),
    ]

    operations = [
        migrations.AddField(
            model_name='haiku',
            name='is_public',
            field=models.BooleanField(default=True),
        ),
    ]
