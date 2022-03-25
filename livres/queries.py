from .models import Livre, Transfert
from django.db.models import Q
def findTransfertsPourLivreTransfereNonConfirme(transfertDeReference):
    """
    recherche des transferts pour le meme livres que celui de @transfertDeReference
    qui sont dans l'etat indiquant que le livre a change de main, mais que ceci n'a pas ete confirme
    :param transfertDeReference: transfert de reference
    :return: List de transferts selectionnes
    """
    transferts_list = Transfert.objects.filter(
        livre=transfertDeReference.livre,
        transfert_status__in=[Transfert.TransfertStatus.OKPOSSESSEUR]
    ).exclude(id=transfertDeReference.id)

    return transferts_list


from django.utils import timezone