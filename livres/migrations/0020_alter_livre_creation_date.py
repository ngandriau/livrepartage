# Generated by Django 4.0.2 on 2022-02-06 06:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('livres', '0019_alter_transfert_possesseur_envois_message_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='livre',
            name='creation_date',
            field=models.DateField(auto_now=True),
        ),
    ]
