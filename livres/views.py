import distutils
import json
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

from .models import Livre, Transfert, Retour
from .queries import findTransfertsPourLivreTransfereNonConfirme


class LivreSearchCriteria:
    def __init__(self, searchinput='', livrepossession="tous",  dateEditionAfter='', dateEditionBefore='',
                 dateCreationAfter='', dateCreationBefore=''):
        self.searchinput = searchinput
        self.livrepossession = livrepossession
        self.dateEditionAfter = dateEditionAfter
        self.dateEditionBefore = dateEditionBefore
        self.dateCreationAfter = dateCreationAfter
        self.dateCreationBefore = dateCreationBefore
        self.sortedselectedCategoriesList = [] # list of tupple ("category key", "category value")
        self.sortedRemainingCategoriesList = []  # list of tupple ("category key", "category value")


def loadLivreSearchCriteriaFromSession(session):
    livreSearchCriteria = LivreSearchCriteria()

    livreSearchCriteria.searchinput = session.get('livreSearchInput', '')
    print(f"loadLivreSearchCriteriaFromSession() - searchinput=={livreSearchCriteria.searchinput}")
    livreSearchCriteria.livrepossession = session.get('livrepossession', "tous")
    livreSearchCriteria.dateEditionAfter = session.get('dateEditionAfter', '')
    livreSearchCriteria.dateEditionBefore = session.get('dateEditionBefore', '')
    livreSearchCriteria.dateCreationAfter = session.get('dateCreationAfter', '')
    livreSearchCriteria.dateCreationBefore = session.get('dateCreationBefore', '')

    # Je ne suis pas certain de ce qui est sauvegardé dans la session, une string de list ou une liste
    sessionValue = session.get('sortedselectedCategoriesList', "")
    if not sessionValue:
        livreSearchCriteria.sortedselectedCategoriesList = []
    else:
        livreSearchCriteria.sortedselectedCategoriesList = sessionValue

    #  Oter les categories deja selectionnees
    categoriesDict = getAllCategories()
    for category in livreSearchCriteria.sortedselectedCategoriesList:
        categoriesDict.pop(category[0], None)
    livreSearchCriteria.sortedRemainingCategoriesList = sorted(categoriesDict.items(), key=lambda x: x[1])
    # sortedRemainingCategoriesList list of tupple ("category key", "category value")

    return livreSearchCriteria


def writeLivreSearchCriteriaFromSession(session, criteria):
    session['livreSearchInput'] = criteria.searchinput
    session['livrepossession'] = criteria.livrepossession
    session['dateEditionAfter'] = criteria.dateEditionAfter
    session['dateEditionBefore'] = criteria.dateEditionBefore
    session['dateCreationAfter'] = criteria.dateCreationAfter
    session['dateCreationBefore'] = criteria.dateCreationBefore
    session['sortedselectedCategoriesList'] = criteria.sortedselectedCategoriesList

def updateLivreSearchCriteriaFromPost(request, livreSearchCriteria):
    """
    update the search criteria passed as argument with the content of the request.POST
    :param request:
    :return: nothing, but update the value of the search criteria passed as argument
    """

    if request.POST.get('searchinput'):
        livreSearchCriteria.searchinput = request.POST['searchinput']
    else:
        livreSearchCriteria.searchinput = ''

    if request.POST.get('livrePossession'):
        livreSearchCriteria.livrepossession = request.POST['livrePossession']
    else:
        livreSearchCriteria.livrepossession = "tous"

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

    selectedCategoriesDict = getSelectedCategoriesFromPost(request=request, selectFieldName='categories')
    livreSearchCriteria.sortedselectedCategoriesList = sorted(selectedCategoriesDict.items(), key=lambda x: x[1])

    # prepare remaining categories
    categoriesDict = getAllCategories()
    for category in livreSearchCriteria.sortedselectedCategoriesList:
        categoriesDict.pop(category[0], None)
    livreSearchCriteria.sortedRemainingCategoriesList = sorted(categoriesDict.items(), key=lambda x: x[1])
    # livreSearchCriteria.sortedRemainingCategoriesList list of tupple ("category key", "category value")

def buildLivreQuerySet(livreSearchCriteria, currentUser):
    """
    :param livreSearchCriteria:
    :param currentUser: typically a request.user
    :return: a queryset basé sur Livre.objects.all() et configuré avec les critères de recherche
    """

    queryset = Livre.objects.all()
    queryset = queryset.filter(Q(titre_text__contains=livreSearchCriteria.searchinput) | Q(
        auteur_text__contains=livreSearchCriteria.searchinput) | Q(
        mots_sujets_txt__contains=livreSearchCriteria.searchinput) | Q(
        livre_code__contains=livreSearchCriteria.searchinput) | Q(
        possesseur__userprofile__ville__contains=livreSearchCriteria.searchinput)
                               )

    # Ajoute filtre par rapport aux categories selectionnées dans le formulaire
    # queryset = queryset.filter(Q(categories__contains="'jeunesse': 'jeunesse'"))
    for category in livreSearchCriteria.sortedselectedCategoriesList:
        queryset = queryset.filter(Q(categories__contains=f"'{category[0]}': '{category[1]}'"))

    if livreSearchCriteria.livrepossession == "meslivres":
        queryset = queryset.filter(Q(possesseur=currentUser) | Q(createur=currentUser))
    elif livreSearchCriteria.livrepossession == "lesautres":
        queryset = queryset.exclude(Q(possesseur=currentUser) | Q(createur=currentUser))

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

    return queryset

@login_required()
def index_view(request):
    print(f"index_view(POST: {request.POST})")

    # recuperer les criteres de recherche dans la session si existe
    livreSearchCriteria = loadLivreSearchCriteriaFromSession(request.session)

    # si l'action est vraiment une recherche de livre avec un formulaire, mettre a jours nos criteres
    if (request.POST.get('cherchelivre')):
        updateLivreSearchCriteriaFromPost(request, livreSearchCriteria)

    queryset = buildLivreQuerySet(livreSearchCriteria, request.user)

    latest_created_livre_list = queryset.order_by('-creation_date')[:200]
    livreEtAutreList=[]
    for livre in latest_created_livre_list:
        livreEtAutreList.append(LivreEtAutreEltOpt(livre=livre))

    writeLivreSearchCriteriaFromSession(request.session, livreSearchCriteria)

    for lEtAutre in livreEtAutreList:
        transfert = Transfert.objects.filter(livre=lEtAutre.livre, demandeur=request.user, transfert_status__in=[
            Transfert.TransfertStatus.INITIALISE,
            Transfert.TransfertStatus.OKPOSSESSEUR]).first()
        if transfert:
            lEtAutre.transfert = transfert

    context = {
        'livreSearchCriteria': livreSearchCriteria,
        'latest_created_livre_et_autres_list': livreEtAutreList,
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

    categories = getAllCategories()
    sortedCategories = sorted(categories.items(), key=lambda x: x[1])

    context = {
        'action': 'creation',
        'categories': sortedCategories
    }
    return render(request, 'livres/livre_edit.html', context)


@login_required()
def requete_edit_livre(request, pk):
    print(f"requete edit livre {pk}")
    livre = get_object_or_404(Livre, pk=pk)

    selectedCategoriesDict = {}
    if (livre.categories):
        selectedCategoriesDict = eval(livre.categories)
    sortedselectedCategoriesList = sorted(selectedCategoriesDict.items(), key=lambda x: x[1])
    # sortedselectedCategoriesList list of tupple ("category key", "category value")

    # prepare remaining categories
    categoriesDict = getAllCategories()
    for category in sortedselectedCategoriesList:
        categoriesDict.pop(category[0], None)
    sortedRemainingCategoriesList = sorted(categoriesDict.items(), key=lambda x: x[1])
    # sortedRemainingCategoriesList list of tupple ("category key", "category value")

    context = {
        'action': 'edition',
        'livre': livre,
        'sortedselectedCategories': sortedselectedCategoriesList,
        'sortedRemainingCategories': sortedRemainingCategoriesList
    }
    return render(request, 'livres/livre_edit.html', context)

def getAllCategories():
    """
    :return: un Dict<key: categorie code, Value: categorie label> des categories de livres configurée. Vide si pas de config trouvées
    """
    categoriesDict = json.loads(config('LIVRE_CATEGORIES', "{}"))
    if len(categoriesDict)==0:
        print("WARNING: pas de categories de livre trouvée. Vérifier si la propriété 'LIVRE_CATEGORIES' est bien configurée")

    return categoriesDict


def getSelectedCategoriesFromPost(request, selectFieldName):
    """
       identifie les 'categories' de livre selectionnees dans un formulaire passe à la request
       :param selectFieldName: le nom de l'input type:select dans le formulaire
       :return: un dictionnaire <key:cle de categorie, value: text de la categorie>
       """

    allCategoriesDict= getAllCategories()
    selectedCategoriesDict= dict((k, allCategoriesDict[k]) for k in request.POST.getlist(selectFieldName) if k in allCategoriesDict)
    return selectedCategoriesDict

@login_required()
def submit_nouveau_livre(request):
    print(f"submit_nouveau_livre({request.POST}) ")

    selectedCategoriesDict = getSelectedCategoriesFromPost(request=request, selectFieldName='categories')


    livre = Livre(
        titre_text=request.POST['titre'],
        auteur_text=request.POST['auteur'],
        createur=request.user,
        possesseur=request.user,
        mode_partage=request.POST['mode_partage'],
        url_externe_livre_text=request.POST['pageweb'],
        publication_date=dateparser.parse(request.POST['dateEditionInput'], languages=['fr']),
        mots_sujets_txt=selectionnerTroisPremiersMots(request.POST['motssujets']),
        categories=selectedCategoriesDict
    )
    livre.save()
    livre.livre_code = f"{config('LIVRE_CODE_PREFIX')}{livre.id}"
    livre.save()

    request.session['prevaction'] = 'newlivre'
    request.session['livre_id'] = livre.id

    # change criteres de recherche pour s'assurer que le nouveau livre apparait dans la liste
    writeLivreSearchCriteriaFromSession(request.session, LivreSearchCriteria( livrepossession="meslivres"))
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

    livre.categories = getSelectedCategoriesFromPost(request=request, selectFieldName='categories')

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
        if (tsf.livre.mode_partage == Livre.ModeDePartage.DON or tsf.livre.createur == request.user):
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
def list_livres_que_je_dois_retourner(request):
    livres_list = Livre.objects.filter(possesseur=request.user, mode_partage=Livre.ModeDePartage.PRET).exclude(
        createur=request.user).order_by('-possede_depuis_date')

    liste_data_view = []
    for livre in livres_list:
        liste_data_view.append(LivreEtAutreEltOpt(
            livre=livre,
            retour=Retour.objects.filter(livre=livre, emprunteur=request.user,
                                         retour_status=Retour.RetourStatus.ACTIF).first())
        )

    context = {
        'livre_et_retour_list': liste_data_view
    }

    return render(request, 'livres/livres_que_je_dois_retourner_list.html', context)


@login_required()
def list_livres_que_je_veux_recuperer(request):
    livres_list = Livre.objects.filter(createur=request.user, mode_partage=Livre.ModeDePartage.PRET).exclude(
        possesseur=request.user).order_by('-possede_depuis_date')

    liste_data_view = []
    for livre in livres_list:
        liste_data_view.append(LivreEtAutreEltOpt(
            livre=livre,
            retour=Retour.objects.filter(livre=livre, proprietaire=request.user,
                                         retour_status=Retour.RetourStatus.ACTIF).first())
        )

    context = {
        'livre_et_retour_list': liste_data_view
    }

    return render(request, 'livres/livres_que_je_veux_recuperer_list.html', context)


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
def livre_a_ete_retourne_par_emprunteur(request, pk):
    print(f"livre_a_ete_retourne_par_emprunteur(livreid:{pk})")
    livre = get_object_or_404(Livre, pk=pk)

    #     check si un retour existe deja sur ce livre
    retour = None
    try:
        retour = Retour.objects.get(livre=livre, retour_status=Retour.RetourStatus.ACTIF)
    except Retour.DoesNotExist:
        retour = Retour(livre=livre, emprunteur=request.user, proprietaire=livre.createur,
                        retour_status=Retour.RetourStatus.ACTIF, emprunteur_retourne_livre_date=timezone.now())

    retour.emprunteur_retourne_livre_date = timezone.now()
    retour.save()

    request.session['prevaction'] = 'retourparemprunteur'
    request.session['retour_id'] = retour.id

    send_email(retour.proprietaire.email, "L'emprunteur d'un de vos livre cherche à communiquer avec vous.",
               f"{retour.emprunteur.first_name} {retour.emprunteur.last_name} indique qu'il vous a restitué le livre '{livre.titre_text}'. <br/> Veuillez confirmer le retour dans le système ou le contacter pour clarifier la situation à l'adresse: {retour.emprunteur.email}. Merci.")

    return HttpResponseRedirect(reverse('livres:listlivrequejedoisretourner'))


@login_required()
def livre_retour_confirme_par_proprietaire(request, pk):
    print(f"livre_retour_confirme_par_proprietaire(livreid:{pk})")
    livre = get_object_or_404(Livre, pk=pk)

    #     check si un retour existe deja sur ce livre
    retour = Retour.objects.filter(livre=livre, retour_status=Retour.RetourStatus.ACTIF,
                                   proprietaire=request.user).first()
    if not retour:
        print(
            f"livre_retour_confirme_par_proprietaire(livre_id:{pk}) - le retour devrait deja exister, mais pas trouver. Creer pour historique seulement")
        retour = Retour(livre=livre, proprietaire=request.user, emprunteur=livre.possesseur,
                        emprunteur_retourne_livre_date=timezone.now()
                        )

    retour.retour_status = Retour.RetourStatus.ACHEVE
    retour.proprietaire_a_recupere_son_livre_date = timezone.now()
    retour.save()

    livre.possesseur = request.user
    livre.possede_depuis_date = timezone.now()
    livre.save()

    request.session['prevaction'] = 'retourconfirmeparproprietaire'
    request.session['retour_id'] = retour.id

    return HttpResponseRedirect(reverse('livres:listlivrequejeveuxrecuperer'))


@login_required()
def livre_retour_emprunteur_envoi_msg_preparer_retour(request, pk):
    print(f"livre_retour_emprunteur_envoi_msg_preparer_retour(livreid:{pk})")
    livre = get_object_or_404(Livre, pk=pk)

    #     check si un retour existe deja sur ce livre
    retour = Retour.objects.filter(livre=livre, retour_status=Retour.RetourStatus.ACTIF,
                                   emprunteur=request.user).first()
    if not retour:
        print("   PAS  DE RETOUR, on en créé un")
        retour = Retour(livre=livre, emprunteur=request.user, proprietaire=livre.createur,
                        retour_status=Retour.RetourStatus.ACTIF)

    retour.emprunteur_message_init_retour_date = timezone.now()
    retour.save()

    send_email(retour.proprietaire.email, "L'emprunteur d'un de vos livre cherche à communiquer avec vous.",
               f"{retour.emprunteur.first_name} {retour.emprunteur.last_name} vous informe qu'il est prêt à vous retourner votre livre '{livre.titre_text}'. <br/> Merci de prendre contact avec lui a l'adresse suivante: {retour.emprunteur.email}")

    return HttpResponseRedirect(reverse('livres:listlivrequejedoisretourner'))


@login_required()
def livre_retour_proprietaire_envoi_msg_rappel(request, pk):
    print(f"livre_retour_proprietaire_envoi_msg_rappel(livreid:{pk})")
    livre = get_object_or_404(Livre, pk=pk)

    #     check si un retour existe deja sur ce livre
    retour = Retour.objects.filter(livre=livre, retour_status=Retour.RetourStatus.ACTIF,
                                   proprietaire=request.user).first()
    if not retour:
        retour = Retour(livre=livre, proprietaire=request.user, emprunteur=livre.possesseur,
                        retour_status=Retour.RetourStatus.ACTIF)

    retour.proprietaire_message_reclame_retour_date = timezone.now()
    retour.save()

    send_email(retour.emprunteur.email, "Le possesseur d'un livre qui vous intéresse cherche à communiquer avec vous.",
               f"{livre.createur.first_name} {livre.createur.last_name} vous informe qu'il aimerait récupérer son livre '{livre.titre_text}' que vous avez depuis le {livre.possede_depuis_date}. <br/> Merci de prendre contact a l'adresse suivante: {livre.createur.email}")

    request.session['prevaction'] = 'retourproprietaireenvoiemessage'
    request.session['retour_id'] = retour.id

    return HttpResponseRedirect(reverse('livres:listlivrequejeveuxrecuperer'))


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

    send_email(transfert.demandeur.email, "Le possesseur d'un livre qui vous intéresse indique qu'il vous l'a transféré.",
               f"{transfert.livre.possesseur.first_name} {transfert.livre.possesseur.last_name} indique vous avoir transféré le livre '{transfert.livre.titre_text}'. <br/> Veuillez confirmer le transfert dans le système ou communiquer pour clarifier la situation à l'adresse en utilisant l'adresse suivante: {transfert.livre.possesseur.email}. Merci.")

    return HttpResponseRedirect(reverse('livres:listtransfertmeslivre'))


@login_required()
def livre_a_ete_recu(request, pk):
    """
    Le demandeur d'un livre confirme qu'il a bien recu un livre et qu'il en est le possesseur
    :param request:
    :param pk:
    :return:
    """

    print(f"livre_a_ete_recu {pk}")
    transfert = get_object_or_404(Transfert, pk=pk)
    transfert.transfert_status = Transfert.TransfertStatus.OKDEMANDEUR
    transfert.ok_demandeur_date = timezone.now()
    transfert.possesseur_final = transfert.livre.possesseur
    transfert.livre.possesseur = request.user
    transfert.livre.possede_depuis_date = timezone.now()
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

    sujet = "Le possesseur d'un livre qui vous intéresse cherche à communiquer avec vous."

    message = f"""\
{transfert.livre.possesseur.first_name} {transfert.livre.possesseur.last_name} qui possède le livre '{transfert.livre.titre_text}', pour lequel vous avez fait une demande de transfert le {transfert.creation_date} a communiqué avec vous. 
 vous pouvez communiquer par email à: {transfert.livre.possesseur.email} pour organiser l'échange."""

    send_email(transfert.demandeur.email, sujet, message)

    request.session['prevaction'] = 'sendMessageDemandeur'
    request.session['transfert_id'] = transfert.id

    return HttpResponseRedirect(reverse('livres:listtransfertmeslivre'))


def send_email(destinataire, sujet, message):
    print(f"send email a: {destinataire} - {sujet} - {message}")
    if not distutils.util.strtobool(config('EMAIL_ACTIF', "False")):
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



class LivreEtAutreEltOpt:
    def __init__(self, livre, retour=None, transfert=None):
        self.livre = livre
        self.retour = retour
        self.transfert = transfert
