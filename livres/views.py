from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils import timezone
from django.views import generic

from .models import Livre, Transfert


@login_required()
def index_view(request):
    context = {
        'latest_created_livre_list': Livre.objects.order_by('-creation_date')[:25],
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
    print("submit new livre")
    livre = Livre(livre_code="TODOFIX",
                  titre_text=request.POST['titre'],
                  auteur_text=request.POST['auteur'],
                  creation_date=timezone.now(),
                  createur=request.user,
                  possesseur=request.user)
    livre.save()
    print(livre)
    return HttpResponseRedirect(reverse('livres:index'))


@login_required()
def submit_edit_livre(request):
    print(f"submit_edit_livre({request.POST['livre_id']})")

    livre = get_object_or_404(Livre, pk=request.POST['livre_id'])
    livre.titre_text = request.POST['titre']
    livre.auteur_text = request.POST['auteur']
    livre.save()
    return HttpResponseRedirect(reverse('livres:index'))


@login_required()
def demande_transfert_livre(request, pk):
    print(f"requete edit livre {pk}")
    livre = get_object_or_404(Livre, pk=pk)
    transfert = Transfert(livre=livre, demandeur=request.user)
    transfert.save()
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
    if(transfert.demandeur != request.user):
        print(f"!!!WARNING annulation transfert demande par user[{request.user}] qui n'est pas le demandeur[{transfert.demandeur}]")
        return HttpResponseRedirect(reverse('livres:index'))

    transfert.transfert_status = Transfert.TransfertStatus.CANCEL
    transfert.demandeur_cancel_date = timezone.now()
    transfert.save()
    return HttpResponseRedirect(reverse('livres:index'))

