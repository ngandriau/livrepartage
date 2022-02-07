# Livre Partage
application django pour supporter le partage de livres communautaire

Ceci est ma première application django et devrit certainement être réécrite pour être plus élégante et respectueuse des bonnes pratiques.

## DatePickerBranch
essai d'intégration de selecteur de date 
ref:
- [doc django package: django-tempus-dominus 5.1.2.16 ](https://pypi.org/project/django-tempus-dominus/)
- [stackover: exemple](https://stackoverflow.com/questions/57490678/django-tempus-dominus-datetimepicker-time-and-date-conversion)

## Commandes type terminal
$ source ~/.virtualenvs/livrepartage/bin/activate
$ cd ~/PycharmProjects/livrepartage

$ python manage.py runserver

$ python manage.py shell

## DB MIGRATIONS
$ python manage.py makemigrations
$ python manage.py migrate


## Run tests
$ python manage.py test livres