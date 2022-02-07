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


@login_required()
def index_view(request):
    if 'searchinput' in request.POST.keys():
        search_input = request.POST['searchinput']
        latest_created_livre_list = Livre.objects.filter(
            Q(titre_text__contains=search_input) | Q(auteur_text__contains=search_input)).order_by('-creation_date')[
                                    :25]
    else:
        latest_created_livre_list = Livre.objects.order_by('-creation_date')[:25]

    # clef = livre, value= transfert
    livres_avec_transfert_actif_pour_user = {}
    for l in latest_created_livre_list:
        transfert = Transfert.objects.filter(livre=l, demandeur=request.user, transfert_status__in=[
            Transfert.TransfertStatus.INITIALISE,
            Transfert.TransfertStatus.OKPOSSESSEUR])
        if (transfert):
            livres_avec_transfert_actif_pour_user[l] = transfert

    context = {
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
    # request.session['prevaction'] = 'newlivre'
    # request.session['livre_id'] = 'livre.id'
    if (request.session.__contains__('prevaction')):
        if (request.session['prevaction'] == 'newlivre'):
            context['showNewLivreCode'] = True
            context['newLivre'] = get_object_or_404(Livre, pk=request.session['livre_id'])
            request.session.__delitem__('prevaction')
            request.session.__delitem__('livre_id')
    else:
        print("No entry 'prevaction' in session")
    return render(request, 'livres/index.html', context)


# TODO check if we need this view and if yes, don't use generic as we cannot @login_required()
class DetailView(generic.DetailView):
    model = Livre
    template_name = 'livres/detail_livre.html'


@login_required()
def requete_nouveau_livre(request):
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
    print(f"submit_nouveau_livre({request.POST['titre']}) - status: {request.POST['transferable_status']}")
    # livre.publication_date = dateparse.parse_date(request.POST['dateedition'])

    livre = Livre(
        titre_text=request.POST['titre'],
        auteur_text=request.POST['auteur'],
        createur=request.user,
        possesseur=request.user,
        transferable_status=request.POST['transferable_status'],
        url_externe_livre_text=request.POST['pageweb'],
        publication_date=dateparser.parse(request.POST['dateEditionInput'], languages=['fr'])
    )
    livre.save()
    livre.livre_code = f"{config('LIVRE_CODE_PREFIX')}{livre.id}"
    livre.save()
    print(livre.livre_code)
    # return redirect(reverse('livres:index'))
    request.session['prevaction'] = 'newlivre'
    request.session['livre_id'] = livre.id
    return redirect(reverse('livres:index'))


@login_required()
def submit_edit_livre(request):
    print(f"submit_edit_livre({request.POST['livre_id']}) - status: {request.POST['transferable_status']}")

    livre = get_object_or_404(Livre, pk=request.POST['livre_id'])

    if (livre.possesseur != request.user):
        print(
            f"submit_edit_livre({livre.titre_text} - {livre.livre_code}) - tentative de mise a jour par {request.user} qui n'est pas le possesseur du livre!!! - ignore changement.")
        return HttpResponseRedirect(reverse('livres:index'))

    livre.titre_text = request.POST['titre']
    livre.auteur_text = request.POST['auteur']
    livre.transferable_status = request.POST['transferable_status']
    livre.publication_date = dateparser.parse(request.POST['dateEditionInput'], languages=['fr'])
    livre.url_externe_livre_text = request.POST['pageweb']
    livre.save()
    return HttpResponseRedirect(reverse('livres:index'))


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

    return HttpResponseRedirect(reverse('livres:index'))


@login_required()
def list_demandes_transfert_mes_livres(request):
    transferts_list = Transfert.objects.filter(livre__possesseur=request.user, transfert_status='INIT').order_by(
        '-creation_date')
    context = {
        'action': 'listTransfertMesLivres',
        'transferts_list': transferts_list
    }
    return render(request, 'livres/transferts_list.html', context)


@login_required()
def list_reception_livre_a_confirmer(request):
    transferts_list = Transfert.objects.filter(demandeur=request.user,
                                               transfert_status=Transfert.TransfertStatus.OKPOSSESSEUR).order_by(
        '-ok_demandeur_date')
    context = {
        'action': 'listReceptionLivreAConfirmer',
        'transferts_list': transferts_list
    }
    return render(request, 'livres/transferts_list.html', context)


@login_required()
def list_mes_demandes_transfert_de_livres(request):
    transferts_list = Transfert.objects.filter(demandeur=request.user,
                                               transfert_status__in=[
                                                   Transfert.TransfertStatus.INITIALISE,
                                                   Transfert.TransfertStatus.OKPOSSESSEUR]).order_by(
        '-ok_demandeur_date')
    context = {
        'action': 'listMesDemandesTransfert',
        'transferts_list': transferts_list
    }
    return render(request, 'livres/transferts_list.html', context)


@login_required()
def livre_a_ete_transfere(request, pk):
    print(f"livre_a_ete_transfere {pk}")
    transfert = get_object_or_404(Transfert, pk=pk)
    transfert.transfert_status = Transfert.TransfertStatus.OKPOSSESSEUR
    transfert.ok_possesseur_date = timezone.now()
    transfert.save()
    return HttpResponseRedirect(reverse('livres:index'))


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
    return HttpResponseRedirect(reverse('livres:index'))


@login_required()
def annul_demande_transfert(request, pk):
    print(f"annul_demande_transfert {pk}")
    transfert = get_object_or_404(Transfert, pk=pk)
    if (transfert.demandeur != request.user):
        print(
            f"!!!WARNING annulation transfert demande par user[{request.user}] qui n'est pas le demandeur[{transfert.demandeur}]")
        return HttpResponseRedirect(reverse('livres:index'))

    transfert.transfert_status = Transfert.TransfertStatus.CANCEL
    transfert.demandeur_cancel_date = timezone.now()
    transfert.save()
    return HttpResponseRedirect(reverse('livres:index'))


@login_required()
def send_message_demandeur_to_prep_transfert(request, pk):
    print(f"send_message_demandeur_to_prep_transfert {pk}")
    transfert = get_object_or_404(Transfert, pk=pk)
    if (transfert.livre.possesseur != request.user):
        print(
            f"!!!WARNING send_message_demandeur_to_prep_transfert demande par user[{request.user}] qui n'est pas le possesseur du livre[{transfert.livre}]")
        return HttpResponseRedirect(reverse('livres:index'))

    transfert.possesseur_envois_message_date = timezone.now()
    transfert.save()
    return HttpResponseRedirect(reverse('livres:index'))


def send_email(destinataire, sujet, message):
    print(f"send email a: {destinataire} - {sujet} - {message}")
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
