# Generated by Django 4.0.1 on 2022-01-29 12:39

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Livre',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titre_text', models.CharField(max_length=200)),
                ('publication_date', models.DateField(verbose_name='date publication')),
                ('creation_date', models.DateField(verbose_name='date creation')),
            ],
        ),
    ]
