# Generated by Django 5.0.13 on 2025-04-26 13:06

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('sleekweb', '0012_xy_count_alter_time_user_end_time'),
    ]

    operations = [
        migrations.RenameField(
            model_name='xy',
            old_name='Count',
            new_name='Order',
        ),
    ]
