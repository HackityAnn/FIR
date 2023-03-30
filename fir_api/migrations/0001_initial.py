from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('incidents', '0012_profile_ms_home_account_id'),
    ]

    operations = [
        migrations.CreateModel(
        name='Oauth2API',
        fields=[
            ('app_id', models.CharField(max_length=512, primary_key=True)),
            ('jwks_uri', models.CharField(max_length=512)),
            ('aud', models.CharField(max_length=512)),
            ('iss', models.CharField(max_length=512)),
        ],
        options={
            'db_table': 'fir_api_oauth2_config',
        },
        )
    ]
