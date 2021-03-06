# Generated by Django 4.0.1 on 2022-01-31 10:01

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('livres', '0014_alter_transfert_ok_demandeur_date_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='livre',
            name='publication_date',
            field=models.DateField(blank=True, null=True, verbose_name='date publication'),
        ),
        migrations.AlterField(
            model_name='transfert',
            name='possesseur',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='possesseurtsf', to=settings.AUTH_USER_MODEL),
        ),
    ]
