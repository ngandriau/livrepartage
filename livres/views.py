import distutils
import smtplib
import ssl
from email.mime.text import MIMEText

import dateparser
from decouple import config
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.utils import timezone
from django.views import generic

from .models import Livre, Transfert
from .queries import findTransfertsPourLivreTransfereNonConfirme


class LivreSearchCriteria:
    def __init__(self, searchinput='', jaicree=False, jepossede=False, dateEditionAfter='', dateEditionBefore='',
                 dateCreationAfter='', dateCreationBefore=''):
        self.searchinput = searchinput
        self.jaicree = jaicree
        self.jepossede = jepossede
        self.dateEditionAfter = dateEditionAfter
        self.dateEditionBefore = dateEditionBefore
        self.dateCreationAfter = dateCreationAfter
        self.dateCreationBefore = dateCreationBefore


def loadLivreSearchCriteriaFromSession(session):
    livreSearchCriteria = LivreSearchCriteria()

    livreSearchCriteria.searchinput = session.get('livreSearchInput', '')
    print(f"loadLivreSearchCriteriaFromSession() - searchinput=={livreSearchCriteria.searchinput}")
    livreSearchCriteria.jaicree = session.get('jaicree', False)
    livreSearchCriteria.jepossede = session.get('jepossede', False)
    livreSearchCriteria.dateEditionAfter = session.get('dateEditionAfter', '')
    livreSearchCriteria.dateEditionBefore = session.get('dateEditionBefore', '')
    livreSearchCriteria.dateCreationAfter = session.get('dateCreationAfter', '')
    livreSearchCriteria.dateCreationBefore = session.get('dateCreationBefore', '')

    return livreSearchCriteria


def writeLivreSearchCriteriaFromSession(session, criteria):
    session['livreSearchInput'] = criteria.searchinput
    session['jaicree'] = criteria.jaicree
    session['jepossede'] = criteria.jepossede
    session['dateEditionAfter'] = criteria.dateEditionAfter
    session['dateEditionBefore'] = criteria.dateEditionBefore
    session['dateCreationAfter'] = criteria.dateCreationAfter
    session['dateCreationBefore'] = criteria.dateCreationBefore


@login_required()
def index_view(request):
    print(f"index_view(POST: {request.POST})")

    # recuperer les criteres de recherche dans la session si existe
    livreSearchCriteria = loadLivreSearchCriteriaFromSession(request.session)

    # si l'action est vraiment une recherche de livre avec un formulaire, mettre a jours nos criteres
    if (request.POST.get('cherchelivre')):
        if request.POST.get('searchinput'):
            livreSearchCriteria.searchinput = request.POST['searchinput']
        else:
            livreSearchCriteria.searchinput = ''

        if request.POST.get('jepossede_check'):
            livreSearchCriteria.jepossede = True
        else:
            livreSearchCriteria.jepossede = False

        if request.POST.get('jaicree_check'):
            livreSearchCriteria.jaicree = True
        else:
            livreSearchCriteria.jaicree = False

        if request.POST.get('dateEditionInputAfter'):
            livreSearchCriteria.dateEditionAfter = request.POST['dateEditionInputAfter']
        else:
            livreSearchCriteria.dateEditionAfter = ''

        if request.POST.get('dateEditionInputBefore'):
            livreSearchCriteria.dateEditionBefore = request.POST['dateEditionInputBefore']
        else:
            livreSearchCriteria.dateEditionBefore = ''

        if request.POST.get('dateCreationInputAfter'):
            livreSearchCriteria.dateCreationAfter = request.POST['dateCreationInputAfter']
        else:
            livreSearchCriteria.dateCreationAfter = ''

        if request.POST.get('dateCreationInputBefore'):
            livreSearchCriteria.dateCreationBefore = request.POST['dateCreationInputBefore']
        else:
            livreSearchCriteria.dateCreationBefore = ''

    # print(f"  livreSearchCriteria.searchinput: {livreSearchCriteria.searchinput}")
    queryset = Livre.objects.all()
    queryset = queryset.filter(Q(titre_text__contains=livreSearchCriteria.searchinput) | Q(
        auteur_text__contains=livreSearchCriteria.searchinput) | Q(
        mots_sujets_txt__contains=livreSearchCriteria.searchinput) | Q(
        livre_code__contains=livreSearchCriteria.searchinput))

    if livreSearchCriteria.jepossede:
        queryset = queryset.exclude(~Q(possesseur=request.user))
    else:
        queryset = queryset.exclude(Q(possesseur=request.user))

    if livreSearchCriteria.jaicree:
        queryset = queryset.exclude(~Q(createur=request.user))
    else:
        queryset = queryset.exclude(Q(createur=request.user))

    if (livreSearchCriteria.dateEditionAfter):
        try:
            d = dateparser.parse(livreSearchCriteria.dateEditionAfter, languages=['fr'])
            queryset = queryset.exclude(publication_date__lte=d)
        except:
            print(
                f"index_view() - ex while parsing dateEditionAfter with value:[{livreSearchCriteria.dateEditionAfter}]")
            livreSearchCriteria.dateEditionAfter = f"INVALIDE: {livreSearchCriteria.dateEditionAfter}"

    if (livreSearchCriteria.dateEditionBefore):
        try:
            d = dateparser.parse(livreSearchCriteria.dateEditionBefore, languages=['fr'])
            queryset = queryset.exclude(publication_date__gte=d)
        except:
            print(
                f"index_view() - ex while parsing dateEditionBefore with value:[{livreSearchCriteria.dateEditionBefore}]")
            livreSearchCriteria.dateEditionBefore = f"INVALIDE: {livreSearchCriteria.dateEditionBefore}"

    if livreSearchCriteria.dateCreationAfter:
        try:
            d = dateparser.parse(livreSearchCriteria.dateCreationAfter, languages=['fr'])
            queryset = queryset.exclude(creation_date__lte=d)
        except:
            print(
                f"index_view() - ex while parsing dateCreationAfter with value:[{livreSearchCriteria.dateCreationAfter}]")
            livreSearchCriteria.dateCreationAfter = f"INVALIDE: {livreSearchCriteria.dateCreationAfter}"

    if (livreSearchCriteria.dateCreationBefore):
        try:
            d = dateparser.parse(livreSearchCriteria.dateCreationBefore, languages=['fr'])
            queryset = queryset.exclude(creation_date__gte=d)
        except:
            print(
                f"index_view() - ex while parsing dateCreationBefore with value:[{livreSearchCriteria.dateCreationBefore}]")
            livreSearchCriteria.dateCreationBefore = f"INVALIDE: {livreSearchCriteria.dateCreationBefore}"

    latest_created_livre_list = queryset.order_by('-creation_date')[:25]

    writeLivreSearchCriteriaFromSession(request.session, livreSearchCriteria)

    # clef = livre, value= transfert
    livres_avec_transfert_actif_pour_user = {}
    for l in latest_created_livre_list:
        transfert = Transfert.objects.filter(livre=l, demandeur=request.user, transfert_status__in=[
            Transfert.TransfertStatus.INITIALISE,
            Transfert.TransfertStatus.OKPOSSESSEUR])
        if (transfert):
            livres_avec_transfert_actif_pour_user[l] = transfert

    context = {
        'livreSearchCriteria': livreSearchCriteria,
        'latest_created_livre_list': latest_created_livre_list,
        'livres_avec_transfert_actif_pour_user': livres_avec_transfert_actif_pour_user,

        'demandes_transfert_mes_livres_list': Transfert.objects.filter(livre__possesseur=request.user,
                                                                       transfert_status='INIT')
            .order_by('-creation_date'),

        'receptions_live_a_confirmer_list': Transfert.objects.filter(demandeur=request.user,
                                                                     transfert_status=Transfert.TransfertStatus.OKPOSSESSEUR)
            .order_by('-ok_demandeur_date'),

        'mes_demandes_transfert_list': Transfert.objects.filter(demandeur=request.user,
                                                                transfert_status__in=[
                                                                    Transfert.TransfertStatus.INITIALISE,
                                                                    Transfert.TransfertStatus.OKPOSSESSEUR])
            .order_by('-ok_demandeur_date')
    }
    if (request.session.__contains__('prevaction')):
        if (request.session['prevaction'] == 'newlivre'):
            context['showNewLivreCode'] = True
            context['newLivre'] = get_object_or_404(Livre, pk=request.session['livre_id'])
            request.session.__delitem__('livre_id')
        elif (request.session['prevaction'] == 'editlivre'):
            context[
                'showSuccessMessage'] = f"Le livre '{get_object_or_404(Livre, pk=request.session['livre_id']).titre_text}' a bien été modifié."
            request.session.__delitem__('livre_id')
        elif (request.session['prevaction'] == 'demandeTransfert'):
            context[
                'showSuccessMessage'] = f"Votre demande de transfert pour le livre '{get_object_or_404(Livre, pk=request.session['livre_id']).titre_text}' a bien été enregistrée."
            request.session.__delitem__('livre_id')
        elif (request.session['prevaction'] == 'sendMessageDemandeur'):
            transfert = get_object_or_404(Transfert, pk=request.session['transfert_id'])
            context[
                'showSuccessMessage'] = f"Message envoyé à '{transfert.demandeur.email}' pour le livre '{transfert.livre.titre_text}'."
            request.session.__delitem__('transfert_id')

        request.session.__delitem__('prevaction')

    return render(request, 'livres/index.html', context)


# TODO check if we need this view and if yes, don't use generic as we cannot @login_required()
class DetailView(generic.DetailView):
    model = Livre
    template_name = 'livres/detail_livre.html'


@login_required()
def requete_nouveau_livre(request):
    print("requete_nouveau_livre()")

    context = {
        'action': 'creation'
    }
    return render(request, 'livres/livre_edit.html', context)


@login_required()
def requete_edit_livre(request, pk):
    print(f"requete edit livre {pk}")
    livre = get_object_or_404(Livre, pk=pk)
    context = {
        'action': 'edition',
        'livre': livre,
    }
    return render(request, 'livres/livre_edit.html', context)


@login_required()
def submit_nouveau_livre(request):
    print(f"submit_nouveau_livre({request.POST}) ")

    livre = Livre(
        titre_text=request.POST['titre'],
        auteur_text=request.POST['auteur'],
        createur=request.user,
        possesseur=request.user,
        mode_partage=request.POST['mode_partage'],
        url_externe_livre_text=request.POST['pageweb'],
        publication_date=dateparser.parse(request.POST['dateEditionInput'], languages=['fr']),
        mots_sujets_txt=selectionnerTroisPremiersMots(request.POST['motssujets'])
    )
    livre.save()
    livre.livre_code = f"{config('LIVRE_CODE_PREFIX')}{livre.id}"
    livre.save()

    request.session['prevaction'] = 'newlivre'
    request.session['livre_id'] = livre.id

    # // change criteres de recherche pour s'assurer que le nouveau livre apparait dans la liste
    writeLivreSearchCriteriaFromSession(request.session, LivreSearchCriteria(jepossede=True, jaicree=True))
    return redirect(reverse('livres:index'))


@login_required()
def submit_edit_livre(request):
    print(f"submit_edit_livre({request.POST['livre_id']})")

    livre = get_object_or_404(Livre, pk=request.POST['livre_id'])

    if (livre.possesseur != request.user):
        print(
            f"submit_edit_livre({livre.titre_text} - {livre.livre_code}) - tentative de mise a jour par {request.user} qui n'est pas le possesseur du livre!!! - ignore changement.")
        return HttpResponseRedirect(reverse('livres:index'))

    livre.titre_text = request.POST['titre']
    livre.auteur_text = request.POST['auteur']
    if (livre.createur == request.user and 'mode_partage' in request.POST.keys()):
        print("UPDATE MODE PARTAGE")
        livre.mode_partage = request.POST['mode_partage']
    livre.publication_date = dateparser.parse(request.POST['dateEditionInput'], languages=['fr'])
    livre.url_externe_livre_text = request.POST['pageweb']
    livre.mots_sujets_txt = selectionnerTroisPremiersMots(request.POST['motssujets'])
    livre.save()

    request.session['prevaction'] = 'editlivre'
    request.session['livre_id'] = livre.id

    return HttpResponseRedirect(reverse('livres:index'))


def selectionnerTroisPremiersMots(mots_str):
    """

    :param mots_str:
    :return: une string qui contient au plus 3 mots
    """
    mots_list = mots_str.split()
    return " ".join(mots_list[0:3])


@login_required()
def demande_transfert_livre(request, pk):
    print(f"demande_transfert_livre {pk}")
    livre = get_object_or_404(Livre, pk=pk)
    transfert = Transfert(livre=livre, demandeur=request.user)
    transfert.save()

    sujet = "Quelqu'un est intéressé par un de vos livre :-)"

    message = f"""\
{request.user.first_name} {request.user.last_name}  est intéressé par votre livre: {livre.titre_text}. Vous pouvez le contacter par email à: {request.user.email}"""

    send_email(livre.possesseur.email, sujet, message)

    request.session['prevaction'] = 'demandeTransfert'
    request.session['livre_id'] = livre.id

    return HttpResponseRedirect(reverse('livres:index'))

def transfertListContainsLivre(transferts_list, livre):
    for tsf in transferts_list:
        if tsf.livre == livre:
            return True

    return False

@login_required()
def list_demandes_transfert_mes_livres(request):
    # les transferts pour le meme livre sont filtres. Si un des transferts a le livre dans les mains du demandeur
    # les autres transferts sont caches pour eviter de donner le livre 2 fois
    transfertsEchangeFait_list = Transfert.objects.filter(livre__possesseur=request.user,
                                                          transfert_status=Transfert.TransfertStatus.OKPOSSESSEUR).order_by(
        '-creation_date')
    transfertsJustInitialise_list = Transfert.objects.filter(livre__possesseur=request.user,
                                                             transfert_status=Transfert.TransfertStatus.INITIALISE)
    result_list = list(transfertsEchangeFait_list)
    for tsf in transfertsJustInitialise_list:
        if not transfertListContainsLivre(transfertsEchangeFait_list, tsf.livre):
            result_list.append(tsf)

    # on enleve aussi les livres qui sont en mode 'PRET' et que nous n'avons pas cree
    result2_list = []
    for tsf in result_list:
        if(tsf.livre.mode_partage == Livre.ModeDePartage.DON or tsf.livre.createur == request.user):
            result2_list.append(tsf)


    context = {
        'action': 'listTransfertMesLivres',
        'transferts_list': result2_list
    }

    if (request.session.__contains__('error')):
        context['showErrorMessage'] = request.session['error']
        request.session.__delitem__('error')

    if (request.session.__contains__('prevaction')):
        if (request.session['prevaction'] == 'sendMessageDemandeur'):
            transfert = get_object_or_404(Transfert, pk=request.session['transfert_id'])
            context[
                'showSuccessMessage'] = f"Message envoyé à '{transfert.demandeur.email}' pour le livre '{transfert.livre.titre_text}'."
            request.session.__delitem__('transfert_id')
        elif (request.session['prevaction'] == 'livreAEteTransfere'):
            transfert = get_object_or_404(Transfert, pk=request.session['transfert_id'])
            context[
                'showSuccessMessage'] = f"'{transfert.demandeur.email}' a été désigné comme le nouveau possesseur du livre '{transfert.livre.titre_text}'. Il doit encore confirmer la réception."
            request.session.__delitem__('transfert_id')

        request.session.__delitem__('prevaction')

    return render(request, 'livres/transferts_mes_livres_list.html', context)


@login_required()
def list_mes_demandes_transfert_de_livres(request):
    transferts_list = Transfert.objects.filter(demandeur=request.user,
                                               transfert_status__in=[
                                                   Transfert.TransfertStatus.INITIALISE,
                                                   Transfert.TransfertStatus.OKPOSSESSEUR]).order_by(
        '-ok_demandeur_date')
    context = {
        'transferts_list': transferts_list
    }

    if (request.session.__contains__('prevaction')):
        if (request.session['prevaction'] == 'annulationTransfert'):
            context[
                'showSuccessMessage'] = f"Votre annulation de transfert pour le livre '{get_object_or_404(Livre, pk=request.session['livre_id']).titre_text}' a bien été enregistrée."
            request.session.__delitem__('livre_id')
        elif (request.session['prevaction'] == 'livreAEteRecu'):
            context[
                'showSuccessMessage'] = f"Vous avez confirmé avoir reçule livre '{get_object_or_404(Livre, pk=request.session['livre_id']).titre_text}'."
            request.session.__delitem__('livre_id')

        request.session.__delitem__('prevaction')

    return render(request, 'livres/transferts_mes_demandes_list.html', context)


@login_required()
def livre_a_ete_transfere(request, pk):
    print(f"livre_a_ete_transfere {pk}")
    transfert = get_object_or_404(Transfert, pk=pk)

    autreTransferts = findTransfertsPourLivreTransfereNonConfirme(transfert)

    if len(autreTransferts) > 0:
        request.session[
            'error'] = f"Le livre '{transfert.livre.titre_text}' a déjà été transféré à un autre demandeur. L'opération a été annulée!"
    else:
        transfert.transfert_status = Transfert.TransfertStatus.OKPOSSESSEUR
        transfert.ok_possesseur_date = timezone.now()
        transfert.save()

        request.session['prevaction'] = 'livreAEteTransfere'
        request.session['transfert_id'] = transfert.id

    return HttpResponseRedirect(reverse('livres:listtransfertmeslivre'))


@login_required()
def livre_a_ete_recu(request, pk):
    print(f"livre_a_ete_recu {pk}")
    transfert = get_object_or_404(Transfert, pk=pk)
    transfert.transfert_status = Transfert.TransfertStatus.OKDEMANDEUR
    transfert.ok_demandeur_date = timezone.now()
    transfert.possesseur_final = transfert.livre.possesseur
    transfert.livre.possesseur = request.user
    # TODO: dans quel etat on met le livre a ce moment? Certainement bloque en mode lecture
    transfert.save()
    transfert.livre.save()

    request.session['prevaction'] = 'livreAEteRecu'
    request.session['livre_id'] = transfert.livre.id

    return HttpResponseRedirect(reverse('livres:listmesdemandestransfert'))


@login_required()
def annul_demande_transfert(request, pk):
    print(f"annul_demande_transfert {pk}")
    transfert = get_object_or_404(Transfert, pk=pk)
    if (transfert.demandeur != request.user):
        print(
            f"!!!WARNING annulation transfert demande par user[{request.user}] qui n'est pas le demandeur[{transfert.demandeur}]")
        return HttpResponseRedirect(reverse('livres:listmesdemandestransfert'))

    transfert.transfert_status = Transfert.TransfertStatus.CANCEL
    transfert.demandeur_cancel_date = timezone.now()
    transfert.save()

    request.session['prevaction'] = 'annulationTransfert'
    request.session['livre_id'] = transfert.livre.id

    return HttpResponseRedirect(reverse('livres:listmesdemandestransfert'))


@login_required()
def send_message_demandeur_to_prep_transfert(request, pk):
    print(f"send_message_demandeur_to_prep_transfert {pk}")
    transfert = get_object_or_404(Transfert, pk=pk)
    if (transfert.livre.possesseur != request.user):
        print(
            f"!!!WARNING send_message_demandeur_to_prep_transfert demande par user[{request.user}] qui n'est pas le possesseur du livre[{transfert.livre}]")
        return HttpResponseRedirect(reverse('livres:listtransfertmeslivre'))

    transfert.possesseur_envois_message_date = timezone.now()
    transfert.save()

    sujet = "Le possesseur d'un livre qui vous intéresse cherche à communiquer avec vous :-)"

    message = f"""\
Le possesseur du livre '{transfert.livre.titre_text}', pour lequel vous avez fait une demande de transfert le {transfert.creation_date} a communiqué avec vous. 
Il se nomme {transfert.livre.possesseur.first_name} {transfert.livre.possesseur.last_name} et vous pouvez le contacter par email à: {transfert.livre.possesseur.email}"""

    send_email(transfert.demandeur.email, sujet, message)

    request.session['prevaction'] = 'sendMessageDemandeur'
    request.session['transfert_id'] = transfert.id

    return HttpResponseRedirect(reverse('livres:listtransfertmeslivre'))


def send_email(destinataire, sujet, message):
    print(f"send email a: {destinataire} - {sujet} - {message}")
    if not distutils.util.strtobool(config('EMAIL_ACTIF')):
        print('  !!!Email pas actif. ')
        return

    port = 465  # For SSL
    # Create a secure SSL context
    context = ssl.create_default_context()

    with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
        server.login(config('GMAIL_USER'), config('GMAIL_PASS'))

        msg = MIMEText(message)
        msg.set_charset('utf-8')
        msg['Subject'] = sujet
        msg['From'] = config('GMAIL_USER')
        msg['To'] = destinataire

        server.send_message(msg)
