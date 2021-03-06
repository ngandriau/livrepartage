# Generated by Django 4.0.2 on 2022-02-20 06:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('livres', '0021_livre_mode_partage_livre_mots_sujets_txt'),
    ]

    operations = [
        migrations.AddField(
            model_name='livre',
            name='possede_depuis_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='livre',
            name='creation_date',
            field=models.DateField(editable=False),
        ),
        migrations.AlterField(
            model_name='transfert',
            name='creation_date',
            field=models.DateField(editable=False),
        ),
    ]
