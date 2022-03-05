from django.contrib.auth.models import User
from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    # la ville qui donnera une indication sur la localisation d'un livre
    ville = models.CharField(max_length=100)


class Livre(models.Model):
    # ceci n'est pas la primary key, mais le code a écrire sur le livre pour le retracer
    livre_code = models.CharField(max_length=20, blank=True, default='')

    # usage anticipé, permettre de saisir 3 mots pour décrire le livre en plus du titre qui seront dans la recherche
    mots_sujets_txt = models.CharField(max_length=200, blank=True, default='')
    titre_text = models.CharField(max_length=200)
    auteur_text = models.CharField(max_length=200, blank=True, default='')
    publication_date = models.DateField('date publication', null=True, blank=True)
    url_externe_livre_text=models.CharField(max_length=200, blank=True, default='')
    # date d'insertion dans le systeme
    creation_date = models.DateField(editable=False)
    createur = models.ForeignKey(User, on_delete=models.CASCADE, related_name='createur')
    possesseur = models.ForeignKey(User, on_delete=models.CASCADE, related_name='possesseur')
    possede_depuis_date = models.DateField(null=True, blank=True)
    categories = models.CharField(max_length=400, blank=True, default='')

    def getSortedCategoriesAsStr(self):
        if self.categories:
            dict = eval(self.categories)
            sortedList = sorted(dict.values())
            return ", ".join(sortedList)
        else:
            return ""


    def save(self, *args, **kwargs):
        ''' On save, update timestamps '''
        if not self.id:
            self.creation_date = timezone.now()
            self.possede_depuis_date = self.creation_date

        return super(Livre, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.titre_text} - code:[{self.livre_code}] - owner:[{self.possesseur}]- createur:[{self.createur}]"

    class ModeDePartage(models.TextChoices):
        DON = 'DON', _('Don')
        PRET = 'PRET', _('Pret')

    mode_partage = models.CharField(
        max_length=4,
        choices=ModeDePartage.choices,
        default=ModeDePartage.DON,
    )

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
    creation_date = models.DateField(editable=False)
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

    def save(self, *args, **kwargs):
        ''' On save, update timestamps '''
        if not self.id:
            self.creation_date = timezone.now()

        return super(Transfert, self).save(*args, **kwargs)

    class TransfertStatus(models.TextChoices):
        INITIALISE = 'INIT', _('INITIALISER')
        # le possesseur indique que le livre a ete transmis (echange)
        OKPOSSESSEUR = 'OKPO', _('OKPOSSESSEUR')
        # le demandeur indique qu'il a bien recu le livre, etat final
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


# lorsqu'un livre emprunte doit etre retourné
# initié par emprunteur qui indique avoir retourné le livre
# (dans le futur autre mode de creation comme propriétaire envoi message a emprunteur pour réclamer son livre, ou emprunteur qui envoi message au propriétaire pour initier retour)

class Retour(models.Model):
    livre = models.ForeignKey(Livre, on_delete=models.CASCADE)
    creation_date = models.DateField(editable=False)
    emprunteur = models.ForeignKey(User, on_delete=models.CASCADE, related_name='emprunteur')

    # devrait etre le createur du livre, mais celui-ci pourrait changer...
    proprietaire = models.ForeignKey(User, on_delete=models.CASCADE, related_name='proprietaire')

    # date à laquelle l'emprunteur a déclarer avoir retourné le livre
    emprunteur_retourne_livre_date = models.DateField(null=True, blank=True)

    # date à laquelle le propriétaire confirme avoir recupéré son livre
    proprietaire_a_recupere_son_livre_date = models.DateField(null=True, blank=True)

    # Date à laquelle l'emprunteur du livre envois un message au proprietaire pour planifier le retour du livre
    emprunteur_message_init_retour_date = models.DateField(null=True, blank=True)

    # Date à laquelle le proprietaire du livre envois un message a l'emprunteur pour réclamer le retour du livre
    proprietaire_message_reclame_retour_date = models.DateField(null=True, blank=True)

    class RetourStatus(models.TextChoices):
        ACTIF = 'ACTIF', _('ACTIF')
        ACHEVE = 'ACHEVE', _('ACHEVE')
        CANCEL = 'CANCEL', _('CANCEL')

    retour_status = models.CharField(
        max_length=10,
        choices=RetourStatus.choices,
        default=RetourStatus.ACTIF,
    )

    def save(self, *args, **kwargs):
        ''' On save, update timestamps '''
        if not self.id:
            self.creation_date = timezone.now()

        return super(Retour, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.livre.titre_text} - emprunteur: {self.emprunteur.first_name} {self.emprunteur.last_name} - crée le: {self.creation_date} "

