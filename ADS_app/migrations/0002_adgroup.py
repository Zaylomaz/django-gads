# Generated by Django 5.0.1 on 2024-02-02 18:06

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ADS_app', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AdGroup',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('ad_group_id', models.CharField(max_length=255, unique=True)),
                ('status', models.CharField(max_length=100)),
                ('campaign', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ad_groups', to='ADS_app.campaign')),
            ],
        ),
    ]
