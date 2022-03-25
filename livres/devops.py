from livres.views import send_email
from django.contrib.auth.models import User
newUser = User.objects.filter(email="stef.chloe86@protonmail.com").first()
msg=f"""Bonjour {newUser.first_name} {newUser.last_name}, ceci est un message de bienvenu de votre application de partage de livres.
Nous vous recommandons d'ajouter l'adresse de l'expéditeur de cet email dans la liste 'blanche' de votre compte email.
Si vous avez trouvé cet email dans vos 'pourriels' ou 'spams', le fait de le sortir de cette liste est suffisant.
Pour toute question, n'hésitez pas à contacter un des administrateurs de cette application.
Merci et bonne journée
"""
send_email(newUser.email, "Bienvenu à l'application de partage de livres", msg)