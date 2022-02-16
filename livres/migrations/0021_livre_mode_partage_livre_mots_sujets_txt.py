# Generated by Django 4.0.2 on 2022-02-09 19:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('livres', '0020_alter_livre_creation_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='livre',
            name='mode_partage',
            field=models.CharField(choices=[('DON', 'Don'), ('PRET', 'Pret')], default='DON', max_length=4),
        ),
        migrations.AddField(
            model_name='livre',
            name='mots_sujets_txt',
            field=models.CharField(blank=True, default='', max_length=20),
        ),
    ]