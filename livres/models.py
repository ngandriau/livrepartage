from django.contrib.auth.models import User
from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext_lazy as _


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    # la ville qui donnera une indication sur la localisation d'un livre
    ville = models.CharField(max_length=100)


class Livre(models.Model):
    # ceci n'est pas la primary key, mais le code a écrire sur le livre pour le retracer
    livre_code = models.CharField(max_length=20, blank=True, default='')
    titre_text = models.CharField(max_length=200)
    auteur_text = models.CharField(max_length=200, blank=True, default='')
    publication_date = models.DateField('date publication', null=True, blank=True)
    url_externe_livre_text=models.CharField(max_length=200, blank=True, default='')
    # date d'insertion dans le systeme
    creation_date = models.DateField('date creation')
    createur = models.ForeignKey(User, on_delete=models.CASCADE, related_name='createur')
    possesseur = models.ForeignKey(User, on_delete=models.CASCADE, related_name='possesseur')

    def __str__(self):
        return self.titre_text

    class TransferableStatus(models.TextChoices):
        DISPONIBLE = 'DISP', _('Disponible')
        LECTURE = 'LECT', _('Lecture')
        PERDU = 'PERD', _('Perdu')

    transferable_status = models.CharField(
        max_length=4,
        choices=TransferableStatus.choices,
        default=TransferableStatus.DISPONIBLE,
    )


class Transfert(models.Model):
    livre = models.ForeignKey(Livre, on_delete=models.CASCADE)
    creation_date = models.DateField(auto_now=True, null=False)
    demandeur = models.ForeignKey(User, on_delete=models.CASCADE, related_name='demandeurtsf')

    # Date à laquelle le possesseur du livre envois un message au demandeur pour planifier échange du livre
    possesseur_envois_message_date = models.DateField(null=True, blank=True)

    # possesseur when the transfert is actually done, not when requested, as the possesseur can change
    possesseur_final = models.ForeignKey(User, on_delete=models.CASCADE, related_name='possesseurfinaltsf', null=True, blank=True)
    # date ou le possesseur indique qu'il a transféré(physiquement) le livre au demandeur
    ok_possesseur_date = models.DateField(null=True, blank=True)
    # date ou le receveur confirme qu'il a bien recu le livre
    ok_demandeur_date = models.DateField(null=True, blank=True)
    demandeur_cancel_date = models.DateField(null=True, blank=True)

    class TransfertStatus(models.TextChoices):
        INITIALISE = 'INIT', _('INITIALISER')
        # le possesseur indique que le livre a ete transmis (echange)
        OKPOSSESSEUR = 'OKPO', _('OKPOSSESSEUR')
        OKDEMANDEUR = 'OKDE', _('OKDEMANDEUR')
        CANCEL = 'CANCEL', _('CANCEL')

    transfert_status = models.CharField(
        max_length=6,
        choices=TransfertStatus.choices,
        default=TransfertStatus.INITIALISE,
    )

    def __str__(self):
        possesseur = self.possesseur_final if self.possesseur_final else self.livre.possesseur
        return f"{self.livre.titre_text} - demandé le {self.creation_date} par {self.demandeur.first_name} {self.demandeur.last_name} a  {possesseur.first_name} {possesseur.last_name} - status: {self.transfert_status}"
