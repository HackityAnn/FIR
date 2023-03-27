from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('incidents', '0011_auto_20210208_2156'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='ms_home_account_id',
            field=models.CharField(max_length=73, null=True, unique=True),
        ),
    ]