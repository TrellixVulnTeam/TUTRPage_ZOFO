# Generated by Django 2.2.2 on 2020-01-09 07:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('TUTRReg', '0003_auto_20190718_2329'),
    ]

    operations = [
        migrations.AddField(
            model_name='person',
            name='first_name',
            field=models.CharField(default='Null', max_length=100),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='person',
            name='last_name',
            field=models.CharField(default='Null', max_length=100),
            preserve_default=False,
        ),
    ]
