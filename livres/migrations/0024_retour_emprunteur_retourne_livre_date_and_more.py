# Generated by Django 4.0.2 on 2022-02-20 08:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('livres', '0023_alter_livre_mots_sujets_txt_retour'),
    ]

    operations = [
        migrations.AddField(
            model_name='retour',
            name='emprunteur_retourne_livre_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='retour',
            name='proprietaire_a_recupere_son_livre_date',
            field=models.DateField(blank=True, null=True),
        ),
    ]