# Generated by Django 4.0.1 on 2022-01-30 10:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('livres', '0007_alter_livre_livre_code_alter_livre_publication_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='livre',
            name='livre_code',
            field=models.CharField(blank=True, default='', max_length=20),
        ),
        migrations.AlterField(
            model_name='livre',
            name='publication_date',
            field=models.DateField(null=True, verbose_name='date publication'),
        ),
    ]
