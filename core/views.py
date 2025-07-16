# Fichier : core/views.py - Version complète avec workflow Manager/Technicien

# ==============================================================================
# IMPORTATIONS
# ==============================================================================

import json
import os
from decimal import Decimal
from datetime import datetime, timedelta
from io import BytesIO
from django.utils.html import escape
from django.http import Http404
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import models
from django.db.models import (Count, Sum, Avg, F, Q, Case, When, IntegerField, 
                             Exists, OuterRef, BooleanField, CharField, Max)
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import get_template
from django.urls import reverse
from django.utils import timezone
from django.conf import settings
# core/views_suppression.py
# Vues pour la suppression des opérations et points de contrôle
# À ajouter dans core/views.py

from django.db import transaction
from .models import Operation, PointDeControle, Intervention, Reponse

# Importations des modèles
from .models import *

# Importations des formulaires
from .forms import *
# ==============================================================================
# NOUVELLES VUES POUR L'EXÉCUTION D'INTERVENTION AMÉLIORÉE
# À ajouter dans core/views.py
# ==============================================================================
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from PIL import Image
import uuid
# ==============================================================================
# FONCTIONS DE CONTRÔLE D'ACCÈS
# ==============================================================================

def is_manager_or_admin(user):
    """Vérifie si l'utilisateur est Manager ou Admin"""
    if not user.is_authenticated:
        return False
    try:
        return user.profil.role in ['MANAGER', 'ADMIN']
    except:
        return False

def is_technicien(user):
    """Vérifie si l'utilisateur est Technicien"""
    if not user.is_authenticated:
        return False
    try:
        return user.profil.role == 'TECHNICIEN'
    except:
        return False

def get_user_role(user):
    """Récupère le rôle de l'utilisateur"""
    try:
        return user.profil.role if hasattr(user, 'profil') else 'OPERATEUR'
    except:
        return 'OPERATEUR'

# ==============================================================================
# VUES POUR L'AUTHENTIFICATION
# ==============================================================================
from .views import is_manager_or_admin
def inscription_view(request):
    """Gère l'inscription de nouveaux utilisateurs."""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Créer automatiquement un profil utilisateur
            ProfilUtilisateur.objects.create(user=user, role='OPERATEUR')
            username = form.cleaned_data.get('username')
            messages.success(request, f'Compte créé pour {username}!')
            return redirect('connexion')
    else:
        form = UserCreationForm()
    return render(request, 'core/auth/inscription.html', {'form': form})

def connexion_view(request):
    """Gère la connexion des utilisateurs."""
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.info(request, f'Vous êtes maintenant connecté en tant que {username}.')
                return redirect('dashboard')
            else:
                messages.error(request, 'Nom d\'utilisateur ou mot de passe invalide.')
        else:
            messages.error(request, 'Nom d\'utilisateur ou mot de passe invalide.')
    else:
        form = AuthenticationForm()
    return render(request, 'core/auth/connexion.html', {'form': form})

def deconnexion_view(request):
    """Gère la déconnexion des utilisateurs."""
    logout(request)
    messages.info(request, 'Vous avez été déconnecté avec succès.')
    return redirect('connexion')

# ==============================================================================
# TABLEAU DE BORD ADAPTÉ PAR RÔLE
# ==============================================================================

@login_required
def dashboard(request):
    """Tableau de bord adapté selon le rôle utilisateur"""
    user_role = get_user_role(request.user)
    
    # Statistiques de base
    stats = {
        'ordres_actifs': OrdreDeTravail.objects.exclude(statut__est_statut_final=True).count(),
        'interventions_validees': Intervention.objects.filter(statut='VALIDATED').count(),
        'assets_total': Asset.objects.count(),
        'assets_en_panne': Asset.objects.filter(statut='EN_PANNE').count(),
    }
    
    # Ordres spécifiques selon le rôle
    if user_role == 'TECHNICIEN':
        # Pour les techniciens : leurs ordres assignés uniquement
        mes_ordres = OrdreDeTravail.objects.filter(
            Q(assigne_a_technicien=request.user) | 
            Q(assigne_a_equipe__membres=request.user)
        ).exclude(statut__est_statut_final=True).select_related(
            'intervention', 'asset', 'statut'
        )[:5]
        
        ordres_recents = mes_ordres
        
    elif user_role in ['MANAGER', 'ADMIN']:
        # Pour les managers : vue globale
        mes_ordres = OrdreDeTravail.objects.filter(
            Q(assigne_a_technicien=request.user) | 
            Q(assigne_a_equipe__membres=request.user) |
            Q(cree_par=request.user)
        ).exclude(statut__est_statut_final=True).select_related(
            'intervention', 'asset', 'statut'
        )[:5]
        
        ordres_recents = OrdreDeTravail.objects.select_related(
            'intervention', 'asset', 'statut', 'cree_par'
        ).order_by('-date_creation')[:10]
        
    else:
        # Pour les autres rôles
        mes_ordres = OrdreDeTravail.objects.filter(
            Q(cree_par=request.user) |
            Q(assigne_a_technicien=request.user) | 
            Q(assigne_a_equipe__membres=request.user)
        ).exclude(statut__est_statut_final=True).select_related(
            'intervention', 'asset', 'statut'
        )[:5]
        
        ordres_recents = mes_ordres
    
    # Assets critiques en panne
    assets_critiques = Asset.objects.filter(
        statut='EN_PANNE',
        criticite__gte=3
    ).order_by('-criticite')[:5]
    
    context = {
        'stats': stats,
        'ordres_recents': ordres_recents,
        'assets_critiques': assets_critiques,
        'mes_ordres': mes_ordres,
        'user_role': user_role,
    }
    
    return render(request, 'core/dashboard.html', context)

# ==============================================================================
# GESTION DES INTERVENTIONS (Manager/Admin uniquement)
# ==============================================================================

@login_required
@user_passes_test(is_manager_or_admin)
def liste_interventions(request):
    """Liste les interventions - Accès Manager/Admin uniquement"""
    query = request.GET.get('search', '')
    user_role = get_user_role(request.user)

    interventions_list = Intervention.objects.all()
    
    if query:
        interventions_list = interventions_list.filter(
            Q(nom__icontains=query) | 
            Q(description__icontains=query)
        )
    
    interventions_list = interventions_list.order_by('-id')
    
    # Pagination
    paginator = Paginator(interventions_list, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'interventions_page': page_obj,
        'search_query': query,
        'user_role': user_role,

    }
    return render(request, 'core/intervention/liste_interventions.html', context)

@login_required
@user_passes_test(is_manager_or_admin)
def creer_intervention(request):
    """Crée une nouvelle intervention - Accès Manager/Admin uniquement"""
    if request.method == 'POST':
        form = InterventionForm(request.POST)
        if form.is_valid():
            intervention = form.save()
            messages.success(request, f'Intervention "{intervention.nom}" créée avec succès!')
            return redirect('intervention_builder', pk=intervention.pk)
    else:
        form = InterventionForm()
    
    return render(request, 'core/intervention/creer_intervention.html', {'form': form})

@login_required
@user_passes_test(is_manager_or_admin)
def intervention_builder(request, pk):
    """Constructeur d'intervention complet - Accès Manager/Admin uniquement"""
    intervention = get_object_or_404(Intervention, pk=pk)
    total_points = PointDeControle.objects.filter(operation__intervention=intervention).count()
    points_obligatoires = PointDeControle.objects.filter(operation__intervention=intervention,
    est_obligatoire=True).count()
    # Traitement des actions POST
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'update_intervention':
            form = InterventionForm(request.POST, instance=intervention)
            if form.is_valid():
                form.save()
                messages.success(request, 'Intervention mise à jour avec succès!')
        
        elif action == 'add_operation':
            nom_operation = request.POST.get('nom')
            if nom_operation:
                # Calculer l'ordre automatiquement
                max_ordre = intervention.operations.aggregate(
                    max_ordre=models.Max('ordre')
                )['max_ordre'] or 0
                
                operation = Operation.objects.create(
                    intervention=intervention,
                    nom=nom_operation,
                    ordre=max_ordre + 1
                )
                messages.success(request, f'Opération "{operation.nom}" ajoutée!')
        
        elif action == 'add_point':
            operation_id = request.POST.get('operation_id')
            operation = get_object_or_404(Operation, pk=operation_id, intervention=intervention)
            
            # Calculer l'ordre automatiquement
            max_ordre = operation.points_de_controle.aggregate(
                max_ordre=models.Max('ordre')
            )['max_ordre'] or 0
            permettre_fichiers = request.POST.get('permettre_fichiers') == 'on'
            file_types = request.POST.getlist('file_types')
            types_fichiers_autorises = ','.join(file_types) if permettre_fichiers else ''

            point = PointDeControle.objects.create(
                operation=operation,
                label=request.POST.get('label'),
                type_champ=request.POST.get('type_champ'),
                aide=request.POST.get('aide', ''),
                options=request.POST.get('options', ''),
                est_obligatoire=request.POST.get('est_obligatoire') == 'on',
                permettre_photo=request.POST.get('permettre_photo') == 'on',
                permettre_audio=request.POST.get('permettre_audio') == 'on',
                permettre_video=request.POST.get('permettre_video') == 'on',
                ordre=max_ordre + 1 ,
                permettre_fichiers=permettre_fichiers,
                types_fichiers_autorises=types_fichiers_autorises
            )
            messages.success(request, f'Point de contrôle "{point.label}" ajouté!')
        
        elif action == 'delete_operation':
            operation_id = request.POST.get('operation_id')
            operation = get_object_or_404(Operation, pk=operation_id, intervention=intervention)
            operation_name = operation.nom
            operation.delete()
            messages.success(request, f'Opération "{operation_name}" supprimée!')
        
        elif action == 'delete_point':
            point_id = request.POST.get('point_id')
            point = get_object_or_404(PointDeControle, pk=point_id)
            point_name = point.label
            point.delete()
            messages.success(request, f'Point de contrôle "{point_name}" supprimé!')
        
        elif action == 'validate_intervention':
            intervention.statut = 'VALIDATED'
            intervention.save()
            messages.success(request, 'Intervention validée avec succès!')
        
        return redirect('intervention_builder', pk=pk)
    
    # Préparer le contexte
    operations = intervention.operations.all().order_by('ordre')
    intervention_form = InterventionForm(instance=intervention)
    
    context = {
        'intervention': intervention,
        'operations': operations,
        'intervention_form': intervention_form,
        'total_points': total_points,
        'points_obligatoires': points_obligatoires,


    }
    return render(request, 'core/intervention/intervention_builder.html', context)

@login_required
@user_passes_test(is_manager_or_admin)
def valider_intervention(request, pk):
    if request.method == 'POST':
        intervention = get_object_or_404(Intervention, pk=pk)
        intervention.statut = 'VALIDATED'
        intervention.save()
        messages.success(request, 'Intervention validée avec succès.')
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})
@login_required
@user_passes_test(is_manager_or_admin)
def supprimer_intervention(request, pk):
    """Supprime une intervention - Accès Manager/Admin uniquement"""
    intervention = get_object_or_404(Intervention, pk=pk)
    
    # Vérifier qu'aucun OT n'utilise cette intervention
    ordres_utilisant = OrdreDeTravail.objects.filter(intervention=intervention).count()
    if ordres_utilisant > 0:
        messages.error(request, f'Impossible de supprimer cette intervention car {ordres_utilisant} ordre(s) de travail l\'utilise(nt).')
        return redirect('intervention_builder', pk=pk)
    
    if request.method == 'POST':
        intervention_name = intervention.nom
        intervention.delete()
        messages.success(request, f'Intervention "{intervention_name}" supprimée!')
        return redirect('liste_interventions')
    
    return render(request, 'core/intervention/supprimer_intervention.html', {
        'intervention': intervention,
        'ordres_utilisant': ordres_utilisant
    })

# Alias pour la compatibilité
intervention_detail = intervention_builder


@login_required
@user_passes_test(is_manager_or_admin)
def preview_intervention(request, pk):
    """Aperçu de l'intervention comme la verrait un technicien"""
    intervention = get_object_or_404(Intervention, pk=pk)
    operations = intervention.operations.all().order_by('ordre')
    
    # Simuler des réponses d'exemple pour la démonstration
    reponses_demo = {}
    for operation in operations:
        for point in operation.points_de_controle.all():
            if point.type_champ == 'BOOLEAN':
                reponses_demo[point.id] = 'OUI' if point.id % 2 == 0 else 'NON'
            elif point.type_champ == 'SELECT' and point.options:
                options = point.options.split(';')
                reponses_demo[point.id] = options[0] if options else ''
            elif point.type_champ == 'NUMBER':
                reponses_demo[point.id] = '25.5'
            elif point.type_champ in ['TEXT', 'TEXTAREA']:
                reponses_demo[point.id] = 'Exemple de réponse de démonstration'
            elif point.type_champ == 'DATE':
                reponses_demo[point.id] = '2024-12-31'
            elif point.type_champ == 'TIME':
                reponses_demo[point.id] = '14:30'
            elif point.type_champ == 'DATETIME':
                reponses_demo[point.id] = '2024-12-31T14:30'
    
    context = {
        'intervention': intervention,
        'operations': operations,
        'reponses_demo': reponses_demo,
        'is_preview': True,
    }
    
    return render(request, 'core/intervention/preview_intervention.html', context)

# ==============================================================================
# GESTION DES ORDRES DE TRAVAIL
# ==============================================================================

@login_required
def liste_ordres_travail(request):
    """Liste tous les ordres de travail avec filtres selon le rôle"""
    ordres = OrdreDeTravail.objects.select_related(
        'intervention', 'asset', 'statut', 'cree_par', 'assigne_a_technicien'
    ).annotate(
        cout_total=F('cout_main_oeuvre_reel') + F('cout_pieces_reel')
    )
    print(ordres)
    # Filtrer selon le rôle
    user_role = get_user_role(request.user)
    
    if user_role == 'TECHNICIEN':
        # Les techniciens ne voient que leurs ordres assignés
        ordres = ordres.filter(
            Q(assigne_a_technicien=request.user) | 
            Q(assigne_a_equipe__membres=request.user)
        )
    elif user_role in ['MANAGER', 'ADMIN']:
        # Managers et admins voient tout
        pass
    else:
        # Autres rôles voient leurs ordres créés/assignés
        ordres = ordres.filter(
            Q(cree_par=request.user) |
            Q(assigne_a_technicien=request.user) | 
            Q(assigne_a_equipe__membres=request.user)
        )
    
    ordres = ordres.order_by('-date_creation')
    
    # Filtres
    statut_filter = request.GET.get('statut')
    priorite_filter = request.GET.get('priorite')
    type_filter = request.GET.get('type_OT')
    search = request.GET.get('search')
    
    if statut_filter:
        ordres = ordres.filter(statut__nom=statut_filter)
    
    if priorite_filter:
        ordres = ordres.filter(priorite=priorite_filter)
    
    if type_filter:
        ordres = ordres.filter(type_OT=type_filter)
    
    if search:
        ordres = ordres.filter(
            Q(titre__icontains=search) |
            Q(asset__nom__icontains=search) |
            Q(intervention__nom__icontains=search)
        )
    
    # Pagination
    paginator = Paginator(ordres, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Données pour les filtres
    statuts = StatutWorkflow.objects.all()
    priorites = [(1, 'Basse'), (2, 'Normale'), (3, 'Haute'), (4, 'Urgente')]
    types_ot = OrdreDeTravail.TYPE_OT_CHOIX
    
    context = {
        'ordres_page': page_obj,
        'statuts': statuts,
        'priorites': priorites,
        'types_ot': types_ot,
        'current_filters': {
            'statut': statut_filter,
            'priorite': priorite_filter,
            'type_OT': type_filter,
            'search': search,
        },
        'user_role': user_role
    }
    
    return render(request, 'core/ot/liste_ordres_travail.html', context)

@login_required
@user_passes_test(is_manager_or_admin)
def creer_ordre_travail(request):
    """Crée un nouvel ordre de travail - Accès Manager/Admin uniquement"""
    if request.method == 'POST':
        form = OrdreDeTravailForm(request.POST)
        if form.is_valid():
            ordre = form.save(commit=False)
            ordre.cree_par = request.user
            ordre.save()
            
            # Créer automatiquement un rapport d'exécution
            RapportExecution.objects.create(
                ordre_de_travail=ordre,
                cree_par=request.user
            )
            
            messages.success(request, f'Ordre de travail "{ordre.titre}" créé avec succès!')
            return redirect('detail_ordre_travail', pk=ordre.pk)
    else:
        form = OrdreDeTravailForm()
    
    return render(request, 'core/ot/creer_ordre_travail.html', {'form': form})


@login_required
def detail_ordre_travail(request, pk):
    """Affiche les détails d'un ordre de travail"""
    ordre = get_object_or_404(OrdreDeTravail, pk=pk)
    
    # Vérifier les permissions d'accès
    user_role = get_user_role(request.user)
    
    can_view = (
        user_role in ['MANAGER', 'ADMIN'] or
        ordre.cree_par == request.user or
        ordre.assigne_a_technicien == request.user or
        (ordre.assigne_a_equipe and request.user in ordre.assigne_a_equipe.membres.all())
    )
    
    if not can_view:
        messages.error(request, "Vous n'avez pas accès à cet ordre de travail.")
        return redirect('liste_ordres_travail')
    
    # Récupérer ou créer le rapport d'exécution
    rapport, created = RapportExecution.objects.get_or_create(
        ordre_de_travail=ordre,
        defaults={'cree_par': request.user}
    )

    # 🔧 Extraire les IDs des points de contrôle déjà remplis
    reponses_ids = set()
    if rapport:
        reponses_ids = set(
            rapport.reponses.values_list('point_de_controle_id', flat=True)
        )
    
    # Traitement des commentaires
    if request.method == 'POST' and request.POST.get('action') == 'add_comment':
        contenu = request.POST.get('contenu')
        if contenu:
            CommentaireOT.objects.create(
                ordre_de_travail=ordre,
                auteur=request.user,
                contenu=contenu
            )
            messages.success(request, 'Commentaire ajouté!')
            return redirect('detail_ordre_travail', pk=pk)
    
    # Commentaires
    commentaires = ordre.commentaires.all().order_by('-date_creation')
    
    # Actions correctives
    actions_correctives = rapport.actions_correctives.all().order_by('-date_creation')
    
    # Vérifier si l'utilisateur peut commencer l'intervention
    peut_executer = (
        ordre.assigne_a_technicien == request.user or
        (ordre.assigne_a_equipe and request.user in ordre.assigne_a_equipe.membres.all()) or
        user_role in ['MANAGER', 'ADMIN']
    )
    
    context = {
        'ordre_de_travail': ordre,
        'rapport': rapport,
        'commentaires': commentaires,
        'actions_correctives': actions_correctives,
        'peut_executer': peut_executer,
        'user_role': user_role,
        'reponses_ids': reponses_ids,  # 👈 Ajout clé
    }
    return render(request, 'core/ot/detail_ordre_travail.html', context)

@login_required
@user_passes_test(is_manager_or_admin)
def modifier_ordre_travail(request, pk):
    """Modifie un ordre de travail existant - Accès Manager/Admin uniquement"""
    ordre = get_object_or_404(OrdreDeTravail, pk=pk)
    
    if request.method == 'POST':
        form = OrdreDeTravailEditForm(request.POST, instance=ordre)
        if form.is_valid():
            ordre_modifie = form.save()
            messages.success(request, f'Ordre de travail "{ordre.titre}" mis à jour avec succès!')
            return redirect('detail_ordre_travail', pk=ordre.pk)
    else:
        form = OrdreDeTravailEditForm(instance=ordre)
    
    context = {
        'form': form,
        'ordre_de_travail': ordre,
    }
    return render(request, 'core/ot/modifier_ordre_travail.html', context)

@login_required
@user_passes_test(is_manager_or_admin)
def supprimer_ordre_travail(request, pk):
    """Supprime un ordre de travail - Accès Manager/Admin uniquement"""
    ordre = get_object_or_404(OrdreDeTravail, pk=pk)
    
    if request.method == 'POST':
        ordre_titre = ordre.titre
        ordre.delete()
        messages.success(request, f'Ordre de travail "{ordre_titre}" supprimé!')
        return redirect('liste_ordres_travail')
    
    return render(request, 'core/ot/supprimer_ordre_travail.html', {
        'ordre_de_travail': ordre
    })

# ==============================================================================
# EXÉCUTION DES INTERVENTIONS
# ==============================================================================

@login_required
def commencer_intervention(request, pk):
    """Démarre l'exécution d'un ordre de travail"""
    ordre = get_object_or_404(OrdreDeTravail, pk=pk)
    
    # Vérifier que l'utilisateur peut commencer cette intervention
    user_role = get_user_role(request.user)
    
    peut_commencer = (
        ordre.assigne_a_technicien == request.user or
        (ordre.assigne_a_equipe and request.user in ordre.assigne_a_equipe.membres.all()) or
        user_role in ['MANAGER', 'ADMIN']
    )
    
    if not peut_commencer:
        messages.error(request, "Vous n'êtes pas autorisé à commencer cette intervention.")
        return redirect('detail_ordre_travail', pk=pk)
    
    # Récupérer ou créer le rapport
    rapport, created = RapportExecution.objects.get_or_create(
        ordre_de_travail=ordre,
        defaults={'cree_par': request.user}
    )
    
    # Marquer le début de l'intervention
    if not rapport.date_execution_debut:
        rapport.date_execution_debut = timezone.now()
        rapport.statut_rapport = 'EN_COURS'
        rapport.save()
        
        # Mettre à jour l'ordre de travail
        ordre.date_debut_reel = timezone.now()
        # Changer le statut vers "En cours"
        statut_en_cours = StatutWorkflow.objects.filter(nom='EN_COURS').first()
        if statut_en_cours:
            ordre.statut = statut_en_cours
        ordre.save()
        
        messages.success(request, "Intervention démarrée!")
    
    return redirect('executer_intervention', pk=pk)


# ==============================================================================
# VUES POUR L'AMÉLIORATION DE L'EXÉCUTION DES OT
# ==============================================================================

@login_required
def executer_intervention(request, pk):
    """
    Version enrichie de l'exécution d'intervention avec fonctionnalités avancées
    """
    ordre = get_object_or_404(OrdreDeTravail, pk=pk)
    
    # Vérifications de permissions existantes...
    user_role = get_user_role(request.user)
    peut_executer = (
        ordre.assigne_a_technicien == request.user or
        (ordre.assigne_a_equipe and request.user in ordre.assigne_a_equipe.membres.all()) or
        user_role in ['MANAGER', 'ADMIN']
    )
    
    if not peut_executer:
        messages.error(request, "Vous n'êtes pas autorisé à exécuter cette intervention.")
        return redirect('detail_ordre_travail', pk=pk)
    
    rapport = get_object_or_404(RapportExecution, ordre_de_travail=ordre)
    operations = ordre.intervention.operations.all().order_by('ordre')
    
    # Vérifier s'il y a des demandes de réparation bloquantes
    demandes_bloquantes = DemandeReparation.objects.filter(
        ordre_de_travail=ordre,
        bloque_cloture_ot=True,
        statut__in=['EN_ATTENTE', 'VALIDEE', 'EN_COURS']
    )
    
    # Traitement des actions
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'sauvegarder_reponses':
            # Sauvegarde automatique améliorée
            reponses_sauvees = 0
            
            for key, value in request.POST.items():
                if key.startswith('point_'):
                    point_id = key.replace('point_', '')
                    try:
                        point = PointDeControle.objects.get(id=point_id)
                        reponse, created = Reponse.objects.get_or_create(
                            rapport_execution=rapport,
                            point_de_controle=point,
                            defaults={'saisi_par': request.user}
                        )
                        
                        if reponse.valeur != value:  # Seulement si changement
                            reponse.valeur = value
                            reponse.saisi_par = request.user
                            reponse.date_reponse = timezone.now()
                            reponse.save()
                            reponses_sauvees += 1
                            
                    except PointDeControle.DoesNotExist:
                        continue
            
            # Réponse JSON pour AJAX
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': f'{reponses_sauvees} réponse(s) sauvegardée(s)',
                    'auto_save': True
                })
            
            messages.success(request, f"Réponses sauvegardées! ({reponses_sauvees} modifications)")
        
        elif action == 'finaliser_intervention':
            # Vérification avancée avant finalisation
            if demandes_bloquantes.exists():
                messages.error(request, f"Impossible de finaliser: {demandes_bloquantes.count()} demande(s) de réparation en attente.")
                return redirect('executer_intervention', pk=pk)
            
            # Vérifier les points obligatoires
            points_obligatoires_manquants = []
            for operation in operations:
                for point in operation.points_de_controle.filter(est_obligatoire=True):
                    if not rapport.reponses.filter(point_de_controle=point).exists():
                        points_obligatoires_manquants.append(f"{operation.nom} > {point.label}")
            
            if points_obligatoires_manquants:
                messages.error(request, f"Points obligatoires manquants: {', '.join(points_obligatoires_manquants)}")
            else:
                # Finaliser avec historique
                rapport.statut_rapport = 'FINALISE'
                rapport.date_execution_fin = timezone.now()
                rapport.save()
                
                ordre.date_fin_reelle = timezone.now()
                statut_termine = StatutWorkflow.objects.filter(nom='TERMINE').first()
                if statut_termine:
                    ordre.statut = statut_termine
                ordre.save()
                
                # Créer historique
                HistoriqueModification.objects.create(
                    type_objet='ORDRE_TRAVAIL',
                    objet_id=ordre.id,
                    type_action='CHANGEMENT_STATUT',
                    description=f"Intervention finalisée par {request.user.get_full_name()}",
                    utilisateur=request.user
                )
                
                messages.success(request, "Intervention finalisée avec succès!")
                return redirect('detail_ordre_travail', pk=pk)
    
    # Récupérer les réponses existantes avec médias
    reponses_existantes = {}
    medias_par_reponse = {}
    
    for reponse in rapport.reponses.all():
        reponses_existantes[reponse.point_de_controle.id] = reponse.valeur
        medias_par_reponse[reponse.point_de_controle.id] = reponse.fichiers_media.all()
    
    context = {
        'ordre_de_travail': ordre,
        'rapport': rapport,
        'operations': operations,
        'reponses_existantes': reponses_existantes,
        'medias_par_reponse': medias_par_reponse,
        'demandes_bloquantes': demandes_bloquantes,
        'user_role': user_role,
        'peut_finaliser': not demandes_bloquantes.exists(),
    }
    
    return render(request, 'core/execution/executer_intervention.html', context)

# ==============================================================================
# GESTION DES PROFILS UTILISATEURS
# ==============================================================================

@login_required
def profil_utilisateur(request):
    """Affiche et permet de modifier le profil de l'utilisateur connecté."""
    profil, created = ProfilUtilisateur.objects.get_or_create(
        user=request.user,
        defaults={'role': 'OPERATEUR'}
    )
    
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profil_form = ProfilUtilisateurUpdateForm(request.POST, instance=profil)
        
        if user_form.is_valid() and profil_form.is_valid():
            user_form.save()
            profil_form.save()
            messages.success(request, 'Votre profil a été mis à jour avec succès!')
            return redirect('profil_utilisateur')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profil_form = ProfilUtilisateurUpdateForm(instance=profil)
    
    context = {
        'user_form': user_form,
        'profil_form': profil_form,
        'profil': profil,
    }
    
    return render(request, 'core/profil/profil_utilisateur.html', context)

@login_required
def changer_mot_de_passe(request):
    """Permet à l'utilisateur de changer son mot de passe."""
    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Votre mot de passe a été changé avec succès!')
            return redirect('profil_utilisateur')
        else:
            messages.error(request, 'Veuillez corriger les erreurs ci-dessous.')
    else:
        form = CustomPasswordChangeForm(request.user)
    
    return render(request, 'core/profil/changer_mot_de_passe.html', {'form': form})

# ==============================================================================
# APIs AJAX POUR LE CONSTRUCTEUR D'INTERVENTION
# ==============================================================================

@login_required
@user_passes_test(is_manager_or_admin)
def ajax_edit_operation(request, operation_id):
    """Édite une opération via AJAX"""
    if request.method == 'POST':
        operation = get_object_or_404(Operation, pk=operation_id)
        operation.nom = request.POST.get('nom', operation.nom)
        operation.save()
        return JsonResponse({'success': True, 'message': 'Opération mise à jour'})
    return JsonResponse({'success': False})

@login_required
def get_point_data(request, pk):
    """Récupère les données d'un point de contrôle pour l'édition"""
    try:
        point = get_object_or_404(PointDeControle, pk=pk)
        
        if not is_manager_or_admin(request.user):
            return JsonResponse({'success': False, 'error': 'Permission refusée'}, status=403)
        
        return JsonResponse({
            'success': True,
            'point': {
                'label': point.label,
                'type_champ': point.type_champ,
                'options': point.options,
                'aide': point.aide,
                'est_obligatoire': point.est_obligatoire,
                'permettre_photo': point.permettre_photo,
                'permettre_audio': point.permettre_audio,
                'permettre_video': point.permettre_video,
                'permettre_fichiers': point.permettre_fichiers,
                'types_fichiers_autorises': point.types_fichiers_autorises,
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@user_passes_test(is_manager_or_admin)
def ajax_edit_point(request, point_id):
    """Édite un point de contrôle via AJAX"""
    if request.method == 'POST':
        point = get_object_or_404(PointDeControle, pk=point_id)
        
        point.label = request.POST.get('label', point.label)
        point.type_champ = request.POST.get('type_champ', point.type_champ)
        point.aide = request.POST.get('aide', point.aide)
        point.options = request.POST.get('options', point.options)
        point.est_obligatoire = request.POST.get('est_obligatoire') == 'on'
        point.permettre_photo = request.POST.get('permettre_photo') == 'on'
        point.permettre_audio = request.POST.get('permettre_audio') == 'on'
        point.permettre_video = request.POST.get('permettre_video') == 'on'
        point.permettre_fichiers = request.POST.get('permettre_fichiers') == 'on'
        file_types = request.POST.getlist('file_types')
        point.types_fichiers_autorises = ','.join(file_types) if point.permettre_fichiers else ''
        
        point.save()
        return JsonResponse({'success': True, 'message': 'Point de contrôle mis à jour'})
    return JsonResponse({'success': False})
@login_required
@user_passes_test(is_manager_or_admin)
def ajax_reorder_operations(request):
    """Réordonne les opérations via AJAX"""
    if request.method == 'POST':
        try:
            # Récupérer les IDs
            operation_ids_str = request.POST.get('operation_ids', '')
            operation_ids = [id.strip() for id in operation_ids_str.split(',') if id.strip()]
            
            if not operation_ids:
                return JsonResponse({
                    'success': False,
                    'error': 'Aucun ID d\'opération fourni'
                }, status=400)
            
            # Récupérer toutes les opérations concernées
            operations = list(Operation.objects.filter(pk__in=operation_ids))
            
            if not operations:
                return JsonResponse({
                    'success': False,
                    'error': 'Aucune opération trouvée'
                }, status=404)
            
            # Obtenir l'intervention_id (toutes les opérations doivent avoir la même)
            intervention_id = operations[0].intervention_id
            
            with transaction.atomic():
                # Méthode 1: Utiliser un offset temporaire élevé
                max_ordre = Operation.objects.filter(
                    intervention_id=intervention_id
                ).aggregate(max_ordre=models.Max('ordre'))['max_ordre'] or 0
                
                offset = max_ordre + 100  # Un offset suffisamment grand
                
                # D'abord, déplacer toutes les opérations à réordonner vers des positions temporaires
                for i, operation_id in enumerate(operation_ids):
                    Operation.objects.filter(pk=int(operation_id)).update(
                        ordre=offset + i
                    )
                
                # Ensuite, les remettre dans le bon ordre
                for index, operation_id in enumerate(operation_ids, 1):
                    Operation.objects.filter(pk=int(operation_id)).update(
                        ordre=index
                    )
            
            return JsonResponse({
                'success': True,
                'message': 'Ordre mis à jour avec succès'
            })
            
        except Exception as e:
            import traceback
            print(f"Erreur dans ajax_reorder_operations: {str(e)}")
            traceback.print_exc()
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'error': 'Méthode non autorisée'
    }, status=405)



# ==============================================================================
# APIs AJAX ET UTILITAIRES
# ==============================================================================

@login_required
def ajax_assets_par_categorie(request):
    """API AJAX pour récupérer les assets par catégorie."""
    categorie_id = request.GET.get('categorie_id')
    
    if categorie_id:
        assets = Asset.objects.filter(
            categorie_id=categorie_id,
            statut__in=['EN_SERVICE', 'EN_MAINTENANCE']
        ).values('id', 'nom', 'reference')
    else:
        assets = Asset.objects.filter(
            statut__in=['EN_SERVICE', 'EN_MAINTENANCE']
        ).values('id', 'nom', 'reference')
    
    return JsonResponse({'assets': list(assets)})

@login_required
def ajax_interventions_validees(request):
    """API AJAX pour récupérer les interventions validées."""
    interventions = Intervention.objects.filter(
        statut='VALIDATED'
    ).values('id', 'nom', 'duree_estimee_heures', 'techniciens_requis')
    
    return JsonResponse({'interventions': list(interventions)})

# ==============================================================================
# RAPPORTS ET EXPORTS
# ==============================================================================

@login_required
def export_rapport_pdf(request, pk):
    """Exporte un rapport d'exécution en PDF."""
    rapport = get_object_or_404(RapportExecution, pk=pk)
    
    # Vérifier les permissions
    user_role = get_user_role(request.user)
    ordre = rapport.ordre_de_travail
    
    can_export = (
        user_role in ['MANAGER', 'ADMIN'] or
        ordre.cree_par == request.user or
        ordre.assigne_a_technicien == request.user or
        (ordre.assigne_a_equipe and request.user in ordre.assigne_a_equipe.membres.all())
    )
    
    if not can_export:
        messages.error(request, "Vous n'avez pas accès à ce rapport.")
        return redirect('liste_ordres_travail')
    
    template_path = 'core/export/rapport_pdf.html'
    context = {
        'rapport': rapport,
        'ordre': rapport.ordre_de_travail,
        'reponses': rapport.reponses.all().order_by(
            'point_de_controle__operation__ordre', 
            'point_de_controle__ordre'
        ),
    }
    
    # Créer un objet HttpResponse avec le bon content-type pour PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="rapport_OT_{rapport.ordre_de_travail.id}.pdf"'
    
    # Générer le PDF
    template = get_template(template_path)
    html = template.render(context)
    
    try:
        from xhtml2pdf import pisa
        result = BytesIO()
        pdf = pisa.pisaDocument(BytesIO(html.encode("ISO-8859-1")), result)
        
        if not pdf.err:
            response.write(result.getvalue())
            return response
    except ImportError:
        messages.error(request, "La génération de PDF n'est pas disponible. Installez xhtml2pdf.")
        return redirect('detail_ordre_travail', pk=rapport.ordre_de_travail.pk)
    
    messages.error(request, "Erreur lors de la génération du PDF.")
    return redirect('detail_ordre_travail', pk=rapport.ordre_de_travail.pk)

# ==============================================================================
# PAGES D'ERREUR ET UTILITAIRES
# ==============================================================================

def handler404(request, exception):
    """Page d'erreur 404 personnalisée."""
    return render(request, 'core/errors/404.html', status=404)

def handler500(request):
    """Page d'erreur 500 personnalisée."""
    return render(request, 'core/errors/500.html', status=500)

# ==============================================================================
# VUES SUPPLÉMENTAIRES POUR LA COMPATIBILITÉ
# ==============================================================================

# Ces vues sont des alias pour assurer la compatibilité avec les URLs existantes
intervention_detail = intervention_builder

# Vue pour preview d'intervention (optionnelle)
@login_required
@user_passes_test(is_manager_or_admin)
def preview_intervention(request, pk):
    """Aperçu de l'intervention comme la verrait un technicien"""
    intervention = get_object_or_404(Intervention, pk=pk)
    operations = intervention.operations.all().order_by('ordre')
    
    context = {
        'intervention': intervention,
        'operations': operations,
        'is_preview': True,
    }
    
    return render(request, 'core/intervention/preview_intervention.html', context)


# ==============================================================================
# VUES POUR LES DEMANDES DE RÉPARATION
# ==============================================================================

@login_required
def liste_demandes_reparation(request):
    """
    Liste toutes les demandes de réparation avec filtres
    """
    user_role = get_user_role(request.user)
    
    # Récupérer les demandes selon le rôle
    demandes = DemandeReparation.objects.select_related(
        'ordre_de_travail', 'point_de_controle', 'cree_par', 'assignee_a'
    )
    
    if user_role == 'TECHNICIEN':
        # Techniciens voient leurs demandes créées et assignées
        demandes = demandes.filter(
            Q(cree_par=request.user) | Q(assignee_a=request.user)
        )
    elif user_role in ['MANAGER', 'ADMIN']:
        # Managers voient tout
        pass
    else:
        # Autres rôles voient leurs demandes
        demandes = demandes.filter(cree_par=request.user)
    
    # Filtres
    statut_filter = request.GET.get('statut')
    priorite_filter = request.GET.get('priorite')
    search = request.GET.get('search')
    
    if statut_filter:
        demandes = demandes.filter(statut=statut_filter)
    
    if priorite_filter:
        demandes = demandes.filter(priorite=priorite_filter)
    
    if search:
        demandes = demandes.filter(
            Q(numero_demande__icontains=search) |
            Q(titre__icontains=search) |
            Q(description__icontains=search)
        )
    
    demandes = demandes.order_by('-date_creation')
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(demandes, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'demandes_page': page_obj,
        'statuts_choix': DemandeReparation.STATUT_CHOIX,
        'priorites_choix': DemandeReparation.PRIORITE_CHOIX,
        'current_filters': {
            'statut': statut_filter,
            'priorite': priorite_filter,
            'search': search,
        },
        'user_role': user_role
    }
    
    return render(request, 'core/reparation/liste_demandes.html', context)

@login_required
def creer_demande_reparation(request, ordre_id, point_id, reponse_id=None):
    """
    Crée une nouvelle demande de réparation depuis un point de contrôle
    """
    ordre = get_object_or_404(OrdreDeTravail, pk=ordre_id)
    point = get_object_or_404(PointDeControle, pk=point_id)
    reponse = None
    
    if reponse_id:
        reponse = get_object_or_404(Reponse, pk=reponse_id)
    
    # Vérifier que le point autorise les demandes de réparation
    if not point.peut_demander_reparation:
        messages.error(request, "Ce point de contrôle n'autorise pas les demandes de réparation.")
        return redirect('executer_intervention', pk=ordre_id)
    
    # Vérifier les permissions
    peut_creer = (
        ordre.assigne_a_technicien == request.user or
        (ordre.assigne_a_equipe and request.user in ordre.assigne_a_equipe.membres.all()) or
        get_user_role(request.user) in ['MANAGER', 'ADMIN']
    )
    
    if not peut_creer:
        messages.error(request, "Vous n'êtes pas autorisé à créer une demande de réparation pour cet ordre.")
        return redirect('executer_intervention', pk=ordre_id)
    
    if request.method == 'POST':
        form = DemandeReparationForm(request.POST)
        if form.is_valid():
            demande = form.save(commit=False)
            demande.ordre_de_travail = ordre
            demande.point_de_controle = point
            demande.reponse_origine = reponse
            demande.cree_par = request.user
            demande.save()
            
            # Créer un historique
            HistoriqueModification.objects.create(
                type_objet='DEMANDE_REPARATION',
                objet_id=demande.id,
                type_action='CREATION',
                description=f"Création de la demande de réparation {demande.numero_demande}",
                utilisateur=request.user
            )
            
            messages.success(request, f"Demande de réparation {demande.numero_demande} créée avec succès!")
            return redirect('detail_demande_reparation', pk=demande.pk)
    else:
        # Pré-remplir le formulaire avec des données contextuelles
        initial_data = {
            'titre': f"Réparation nécessaire - {point.label}",
            'description': f"Problème détecté lors du contrôle '{point.label}' sur l'équipement {ordre.asset.nom}",
            'priorite': 2,  # Normale par défaut
        }
        
        if reponse:
            initial_data['description'] += f"\nValeur constatée: {reponse.valeur}"
        
        form = DemandeReparationForm(initial=initial_data)
    
    context = {
        'form': form,
        'ordre_de_travail': ordre,
        'point_de_controle': point,
        'reponse': reponse,
    }
    
    return render(request, 'core/reparation/creer_demande.html', context)

@login_required
def detail_demande_reparation(request, pk):
    """
    Affiche les détails d'une demande de réparation
    """
    demande = get_object_or_404(DemandeReparation, pk=pk)
    
    # Vérifier les permissions
    user_role = get_user_role(request.user)
    peut_voir = (
        user_role in ['MANAGER', 'ADMIN'] or
        demande.cree_par == request.user or
        demande.assignee_a == request.user or
        demande.ordre_de_travail.assigne_a_technicien == request.user
    )
    
    if not peut_voir:
        messages.error(request, "Vous n'avez pas accès à cette demande de réparation.")
        return redirect('liste_demandes_reparation')
    
    # Actions POST
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'valider' and user_role in ['MANAGER', 'ADMIN']:
            demande.statut = 'VALIDEE'
            demande.validee_par = request.user
            demande.date_validation = timezone.now()
            demande.commentaire_manager = request.POST.get('commentaire_manager', '')
            demande.save()
            
            messages.success(request, f"Demande {demande.numero_demande} validée!")
            
        elif action == 'rejeter' and user_role in ['MANAGER', 'ADMIN']:
            demande.statut = 'REJETEE'
            demande.validee_par = request.user
            demande.date_validation = timezone.now()
            demande.commentaire_manager = request.POST.get('commentaire_manager', '')
            demande.save()
            
            messages.warning(request, f"Demande {demande.numero_demande} rejetée.")
            
        elif action == 'commencer' and demande.peut_etre_commencee():
            if demande.assignee_a == request.user or user_role in ['MANAGER', 'ADMIN']:
                demande.statut = 'EN_COURS'
                demande.date_debut_reparation = timezone.now()
                demande.save()
                
                messages.success(request, "Réparation démarrée!")
                
        elif action == 'terminer' and demande.statut == 'EN_COURS':
            if demande.assignee_a == request.user or user_role in ['MANAGER', 'ADMIN']:
                demande.statut = 'TERMINEE'
                demande.date_fin_reparation = timezone.now()
                demande.cout_reel = request.POST.get('cout_reel', 0) or 0
                demande.commentaire_resolution = request.POST.get('commentaire_resolution', '')
                demande.save()
                
                messages.success(request, f"Réparation {demande.numero_demande} terminée!")
                
        elif action == 'assigner' and user_role in ['MANAGER', 'ADMIN']:
            technicien_id = request.POST.get('technicien_id')
            if technicien_id:
                from django.contrib.auth.models import User
                technicien = get_object_or_404(User, pk=technicien_id)
                demande.assignee_a = technicien
                demande.save()
                
                messages.success(request, f"Demande assignée à {technicien.get_full_name()}")
        
        return redirect('detail_demande_reparation', pk=pk)
    
    # Récupérer l'historique
    historique = HistoriqueModification.objects.filter(
        type_objet='DEMANDE_REPARATION',
        objet_id=demande.id
    ).order_by('-date_modification')
    
    # Techniciens disponibles pour assignment
    techniciens_disponibles = None
    if user_role in ['MANAGER', 'ADMIN']:
        from django.contrib.auth.models import User
        techniciens_disponibles = User.objects.filter(
            profil__role='TECHNICIEN',
            is_active=True
        ).select_related('profil')
    
    context = {
        'demande': demande,
        'historique': historique,
        'techniciens_disponibles': techniciens_disponibles,
        'user_role': user_role,
        'peut_valider': user_role in ['MANAGER', 'ADMIN'] and demande.peut_etre_validee(),
        'peut_commencer': demande.peut_etre_commencee() and (
            demande.assignee_a == request.user or user_role in ['MANAGER', 'ADMIN']
        ),
        'peut_terminer': demande.statut == 'EN_COURS' and (
            demande.assignee_a == request.user or user_role in ['MANAGER', 'ADMIN']
        ),
    }
    
    return render(request, 'core/reparation/detail_demande.html', context)

# ==============================================================================
# VUES POUR LE DRAG & DROP ET RÉORGANISATION
# ==============================================================================

@login_required
@user_passes_test(is_manager_or_admin)
def reorder_operations(request):
    """
    API AJAX pour réorganiser l'ordre des opérations par drag & drop
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            operation_ids = data.get('operation_ids', [])
            
            # Mettre à jour l'ordre de chaque opération
            for index, operation_id in enumerate(operation_ids, 1):
                from .models import Operation
                Operation.objects.filter(pk=operation_id).update(ordre=index)
            
            return JsonResponse({
                'success': True,
                'message': 'Ordre des opérations mis à jour'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
    
    return JsonResponse({'success': False}, status=405)

@login_required
@user_passes_test(is_manager_or_admin)
def reorder_points_controle(request):
    """
    API AJAX pour réorganiser les points de contrôle (au sein d'une opération ou entre opérations)
    """
    if request.method == 'POST':
        try:
            # Accepter JSON ou form-encoded
            if request.content_type == 'application/json':
                data = json.loads(request.body)
                point_ids = data.get('point_ids', [])
                operation_id = data.get('operation_id')
            else:
                point_ids_str = request.POST.get('point_ids', '')
                point_ids = [id.strip() for id in point_ids_str.split(',') if id.strip()]
                operation_id = request.POST.get('operation_id')
            
            if not point_ids:
                return JsonResponse({
                    'success': False,
                    'error': 'Aucun ID de point fourni'
                }, status=400)
            
            if not operation_id:
                return JsonResponse({
                    'success': False,
                    'error': 'ID d\'opération manquant'
                }, status=400)
            
            # Vérifier que l'opération existe
            try:
                operation = Operation.objects.get(pk=int(operation_id))
            except Operation.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': 'Opération non trouvée'
                }, status=404)
            
            with transaction.atomic():
                # Récupérer tous les points concernés
                points = list(PointDeControle.objects.filter(
                    pk__in=[int(pid) for pid in point_ids if pid]
                ))
                
                if len(points) != len(point_ids):
                    return JsonResponse({
                        'success': False,
                        'error': 'Certains points n\'ont pas été trouvés'
                    }, status=404)
                
                # Mettre à jour l'opération et l'ordre de chaque point
                for index, point_id in enumerate(point_ids, 1):
                    PointDeControle.objects.filter(pk=int(point_id)).update(
                        operation=operation,
                        ordre=index
                    )
                
                # Réorganiser les points restants dans les opérations sources
                # (pour combler les trous laissés par les points déplacés)
                operations_a_reordonner = set()
                for point in points:
                    if point.operation_id != operation.id:
                        operations_a_reordonner.add(point.operation_id)
                
                for op_id in operations_a_reordonner:
                    points_restants = PointDeControle.objects.filter(
                        operation_id=op_id
                    ).order_by('ordre')
                    for idx, point in enumerate(points_restants, 1):
                        if point.ordre != idx:
                            point.ordre = idx
                            point.save(update_fields=['ordre'])
            
            return JsonResponse({
                'success': True,
                'message': 'Points de contrôle réorganisés avec succès',
                'operation_id': operation_id
            })
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'error': 'Méthode non autorisée'
    }, status=405)

# ==============================================================================
# VUES POUR LA GESTION AVANCÉE DES MÉDIAS
# ==============================================================================

@login_required
def upload_media_avance(request):
    """
    Upload de médias avec validation avancée et métadonnées
    """
    if request.method == 'POST':
        try:
            files = request.FILES.getlist('files')
            point_id = request.POST.get('point_id')
            reponse_id = request.POST.get('reponse_id')
            
            point = get_object_or_404(PointDeControle, pk=point_id)
            reponse = get_object_or_404(Reponse, pk=reponse_id) if reponse_id else None
            
            # Validation des types de fichiers
            types_autorises = []
            if point.types_fichiers_autorises:
                types_autorises = [t.strip().upper() for t in point.types_fichiers_autorises.split(',')]
            
            uploaded_files = []
            
            for file in files:
                # Vérifier l'extension
                file_ext = os.path.splitext(file.name)[1][1:].upper()
                
                if types_autorises and file_ext not in types_autorises:
                    return JsonResponse({
                        'success': False,
                        'error': f'Type de fichier {file_ext} non autorisé pour ce point de contrôle'
                    }, status=400)
                
                # Vérifier la taille
                taille_max_mb = getattr(point, 'taille_max_fichier_mb', 10)
                if file.size > taille_max_mb * 1024 * 1024:
                    return JsonResponse({
                        'success': False,
                        'error': f'Fichier trop volumineux. Maximum: {taille_max_mb}MB'
                    }, status=400)
                
                # Déterminer le type de média
                type_fichier = 'DOCUMENT'
                if file_ext in ['JPG', 'JPEG', 'PNG', 'GIF', 'BMP']:
                    type_fichier = 'PHOTO'
                elif file_ext in ['MP3', 'WAV', 'M4A', 'OGG']:
                    type_fichier = 'AUDIO'
                elif file_ext in ['MP4', 'AVI', 'MOV', 'MKV', 'WEBM']:
                    type_fichier = 'VIDEO'
                
                # Créer le fichier média
                fichier_media = FichierMedia.objects.create(
                    reponse=reponse,
                    type_fichier=type_fichier,
                    fichier=file,
                    nom_original=file.name,
                    taille_octets=file.size
                )
                
                # Créer l'enrichissement
                MediaEnrichi.objects.create(
                    fichier_media=fichier_media,
                    legende=request.POST.get(f'legende_{file.name}', ''),
                    mots_cles=request.POST.get(f'mots_cles_{file.name}', ''),
                    latitude_capture=request.POST.get('latitude'),
                    longitude_capture=request.POST.get('longitude')
                )
                
                uploaded_files.append({
                    'id': fichier_media.id,
                    'nom': fichier_media.nom_original,
                    'type': fichier_media.type_fichier,
                    'taille': fichier_media.taille_octets
                })
            
            return JsonResponse({
                'success': True,
                'files': uploaded_files,
                'message': f'{len(uploaded_files)} fichier(s) uploadé(s) avec succès'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    return JsonResponse({'success': False}, status=405)

@login_required
def supprimer_media(request, media_id):
    """
    Supprime un fichier média
    """
    if request.method == 'POST':
        try:
            fichier = get_object_or_404(FichierMedia, pk=media_id)
            
            # Vérifier les permissions
            if (fichier.reponse.rapport_execution.ordre_de_travail.assigne_a_technicien != request.user and
                get_user_role(request.user) not in ['MANAGER', 'ADMIN']):
                return JsonResponse({
                    'success': False,
                    'error': 'Permission refusée'
                }, status=403)
            
            # Supprimer le fichier physique
            if fichier.fichier:
                default_storage.delete(fichier.fichier.name)
            
            fichier.delete()
            
            return JsonResponse({
                'success': True,
                'message': 'Fichier supprimé avec succès'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    return JsonResponse({'success': False}, status=405)



# ==============================================================================
# VUES SIMPLIFIÉES POUR LA GESTION DES MÉDIAS
# À ajouter dans core/views.py (VERSION CORRIGÉE)
# ==============================================================================

import json
import os
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required

# ==============================================================================
# VUE UPLOAD MEDIA SIMPLE AMÉLIORÉE
# À remplacer dans core/views.py
# ==============================================================================

@login_required
def upload_media_simple(request):
    """
    Version améliorée pour tester l'upload et la preview
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Méthode non autorisée'}, status=405)
    
    try:
        # Récupérer les paramètres
        fichier = request.FILES.get('fichier')
        point_id = request.POST.get('point_id')
        type_fichier = request.POST.get('type_fichier', 'PHOTO')
        ordre_travail_id = request.POST.get('ordre_travail_id')
        
        print(f"DEBUG: fichier={fichier}, point_id={point_id}, type_fichier={type_fichier}, ordre_travail_id={ordre_travail_id}")
        
        if not fichier:
            return JsonResponse({'success': False, 'error': 'Pas de fichier'}, status=400)
        
        if not point_id:
            return JsonResponse({'success': False, 'error': 'point_id manquant'}, status=400)
            
        if not ordre_travail_id:
            return JsonResponse({'success': False, 'error': 'ordre_travail_id manquant'}, status=400)
        
        # Récupérer les objets nécessaires
        try:
            point = PointDeControle.objects.get(id=point_id)
            ordre_travail = OrdreDeTravail.objects.get(id=ordre_travail_id)
        except (PointDeControle.DoesNotExist, OrdreDeTravail.DoesNotExist) as e:
            return JsonResponse({'success': False, 'error': f'Objet introuvable: {str(e)}'}, status=404)
        
        # Créer ou récupérer le rapport et la réponse
        rapport, created = RapportExecution.objects.get_or_create(
            ordre_de_travail=ordre_travail,
            defaults={
                'statut_rapport': 'EN_COURS',
                'technicien_execution': request.user
            }
        )
        
        reponse, created = Reponse.objects.get_or_create(
            rapport_execution=rapport,
            point_de_controle=point,
            defaults={'valeur': 'Média ajouté'}
        )
        
        # Sauvegarder le fichier média
        fichier_media = FichierMedia.objects.create(
            reponse=reponse,
            type_fichier=type_fichier.upper(),
            fichier=fichier,
            nom_original=fichier.name,
            taille_octets=fichier.size
        )
        
        # Déterminer le type de fichier
        file_ext = os.path.splitext(fichier.name)[1].lower() if '.' in fichier.name else ''
        is_image = file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']
        is_video = file_ext in ['.mp4', '.avi', '.mov', '.webm']
        is_audio = file_ext in ['.mp3', '.wav', '.aac', '.m4a']
        
        # Préparer la réponse avec toutes les données nécessaires
        media_data = {
            'id': fichier_media.id,
            'url': fichier_media.fichier.url,
            'nom_original': fichier_media.nom_original,
            'taille_formatee': _format_file_size(fichier_media.taille_octets),
            'type_mime': fichier.content_type or 'application/octet-stream',
            'is_image': is_image,
            'is_video': is_video,
            'is_audio': is_audio,
            'extension': file_ext[1:] if file_ext else ''
        }
        
        print(f"DEBUG: média créé avec succès - {media_data}")
        
        return JsonResponse({
            'success': True, 
            'message': f'Fichier {fichier.name} uploadé avec succès',
            'media': media_data
        })
        
    except Exception as e:
        print(f"ERREUR dans upload_media_simple: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': f'Erreur serveur: {str(e)}'}, status=500)


@login_required
def delete_media_simple(request):
    """
    Version améliorée pour tester la suppression
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Méthode non autorisée'}, status=405)
    
    try:
        # Récupérer l'ID du média à supprimer
        if request.content_type == 'application/json':
            data = json.loads(request.body)
            media_id = data.get('media_id')
        else:
            media_id = request.POST.get('media_id')
        
        print(f"DEBUG: suppression média ID={media_id}")
        
        if not media_id:
            return JsonResponse({'success': False, 'error': 'media_id manquant'}, status=400)
        
        try:
            media = FichierMedia.objects.get(id=media_id)
            
            # Supprimer le fichier physique
            if media.fichier:
                try:
                    media.fichier.delete(save=False)
                except Exception as e:
                    print(f"Erreur suppression fichier physique: {e}")
            
            # Supprimer l'enregistrement
            media.delete()
            
            print(f"DEBUG: média {media_id} supprimé avec succès")
            return JsonResponse({'success': True, 'message': f'Média {media_id} supprimé'})
            
        except FichierMedia.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Média introuvable'}, status=404)
        
    except Exception as e:
        print(f"ERREUR dans delete_media_simple: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': f'Erreur serveur: {str(e)}'}, status=500)




# ==============================================================================
# VUES POUR LES INFORMATIONS ENRICHIES DES ASSETS
# ==============================================================================

@login_required
def detail_asset_enrichi(request, pk):
    """
    Vue détaillée enrichie d'un asset avec toutes ses informations
    """
    asset = get_object_or_404(Asset, pk=pk)
    
    # Récupérer l'historique de maintenance
    ordres_maintenance = OrdreDeTravail.objects.filter(
        asset=asset
    ).select_related('intervention', 'statut', 'cree_par').order_by('-date_creation')[:10]
    
    # Demandes de réparation en cours
    demandes_reparation = DemandeReparation.objects.filter(
        ordre_de_travail__asset=asset,
        statut__in=['EN_ATTENTE', 'VALIDEE', 'EN_COURS']
    ).order_by('-date_creation')
    
    # Calculs de disponibilité
    from datetime import datetime, timedelta
    
    # Temps total d'indisponibilité ce mois
    debut_mois = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    ordres_ce_mois = OrdreDeTravail.objects.filter(
        asset=asset,
        date_creation__gte=debut_mois,
        date_fin_reelle__isnull=False
    )
    
    temps_indisponibilite = timedelta()
    for ordre in ordres_ce_mois:
        if ordre.date_debut_reel and ordre.date_fin_reelle:
            temps_indisponibilite += ordre.date_fin_reelle - ordre.date_debut_reel
    
    # Calcul du pourcentage de disponibilité
    temps_total_mois = timezone.now() - debut_mois
    if temps_total_mois.total_seconds() > 0:
        disponibilite_pct = max(0, 100 - (temps_indisponibilite.total_seconds() / temps_total_mois.total_seconds() * 100))
    else:
        disponibilite_pct = 100
    
    context = {
        'asset': asset,
        'ordres_maintenance': ordres_maintenance,
        'demandes_reparation': demandes_reparation,
        'disponibilite_pct': round(disponibilite_pct, 1),
        'temps_indisponibilite': temps_indisponibilite,
        'peut_modifier': get_user_role(request.user) in ['MANAGER', 'ADMIN'],
    }
    
    return render(request, 'core/asset/detail_asset_enrichi.html', context)

@login_required
def generer_qr_code_asset(request, pk):
    """
    Génère et retourne le QR code d'un asset
    """
    asset = get_object_or_404(Asset, pk=pk)
    
    try:
        import qrcode
        from io import BytesIO
        
        # Créer le QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        
        # URL vers les détails de l'asset
        qr_data = request.build_absolute_uri(f"/asset/{asset.id}/")
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        # Créer l'image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Retourner l'image
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        response = HttpResponse(buffer.getvalue(), content_type='image/png')
        response['Content-Disposition'] = f'attachment; filename="qr_asset_{asset.id}.png"'
        
        return response
        
    except ImportError:
        messages.error(request, "La génération de QR codes n'est pas disponible. Installez la bibliothèque qrcode.")
        return redirect('detail_asset_enrichi', pk=pk)
    


# ==============================================================================
# VUES POUR L'EXPORT PDF ENRICHI
# ==============================================================================

@login_required
def export_rapport_pdf(request, pk):
    """
    Export PDF enrichi avec médias et demandes de réparation
    """
    rapport = get_object_or_404(RapportExecution, pk=pk)
    ordre = rapport.ordre_de_travail
    
    # Vérifications de permissions...
    user_role = get_user_role(request.user)
    can_export = (
        user_role in ['MANAGER', 'ADMIN'] or
        ordre.cree_par == request.user or
        ordre.assigne_a_technicien == request.user or
        (ordre.assigne_a_equipe and request.user in ordre.assigne_a_equipe.membres.all())
    )
    
    if not can_export:
        messages.error(request, "Vous n'avez pas accès à ce rapport.")
        return redirect('liste_ordres_travail')
    
    # Préparer les données
    reponses_avec_medias = []
    for reponse in rapport.reponses.all().order_by(
        'point_de_controle__operation__ordre', 
        'point_de_controle__ordre'
    ):
        medias = reponse.fichiers_media.all()
        reponses_avec_medias.append({
            'reponse': reponse,
            'medias': medias,
            'nb_photos': medias.filter(type_fichier='PHOTO').count(),
            'nb_documents': medias.filter(type_fichier='DOCUMENT').count(),
        })
    
    # Demandes de réparation liées
    demandes_reparation = DemandeReparation.objects.filter(
        ordre_de_travail=ordre
    ).order_by('-date_creation')
    
    context = {
        'rapport': rapport,
        'ordre': ordre,
        'reponses_avec_medias': reponses_avec_medias,
        'demandes_reparation': demandes_reparation,
        'date_export': timezone.now(),
        'exporte_par': request.user,
    }
    
    try:
        from django.template.loader import get_template
        from xhtml2pdf import pisa
        from io import BytesIO
        
        template_path = 'core/export/rapport_pdf_enrichi.html'
        template = get_template(template_path)
        html = template.render(context)
        
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="rapport_enrichi_OT_{ordre.id}.pdf"'
        
        result = BytesIO()
        pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
        
        if not pdf.err:
            response.write(result.getvalue())
            return response
        else:
            messages.error(request, "Erreur lors de la génération du PDF.")
            
    except ImportError:
        messages.error(request, "La génération de PDF n'est pas disponible. Installez xhtml2pdf.")
    
    return redirect('detail_ordre_travail', pk=ordre.pk)



@login_required
def get_notifications_utilisateur(request):
    """
    API pour récupérer les notifications de l'utilisateur
    """
    notifications = Notification.objects.filter(
        utilisateur=request.user
    ).order_by('-date_creation')[:20]
    
    data = []
    for notif in notifications:
        data.append({
            'id': notif.id,
            'titre': notif.titre,
            'message': notif.message,
            'type': notif.type_notification,
            'lue': notif.lue,
            'date_creation': notif.date_creation.isoformat(),
        })
    
    return JsonResponse({
        'notifications': data,
        'non_lues': notifications.filter(lue=False).count()
    })

@login_required
def get_statistiques_dashboard(request):
    """
    API pour les statistiques du dashboard
    """
    user = request.user
    user_role = get_user_role(user)
    
    # Statistiques selon le rôle
    if user_role in ['MANAGER', 'ADMIN']:
        # Stats globales pour managers
        stats = {
            'ordres_actifs': OrdreDeTravail.objects.exclude(statut__est_statut_final=True).count(),
            'ordres_en_retard': OrdreDeTravail.objects.filter(
                date_prevue_debut__lt=timezone.now(),
                statut__est_statut_final=False
            ).count(),
            'demandes_reparation_en_attente': DemandeReparation.objects.filter(
                statut='EN_ATTENTE'
            ).count(),
            'assets_en_panne': Asset.objects.filter(statut='EN_PANNE').count(),
            'techniciens_actifs': User.objects.filter(
                profil__role='TECHNICIEN',
                is_active=True
            ).count(),
        }
    else:
        # Stats personnelles pour techniciens
        mes_ot = OrdreDeTravail.objects.filter(
            Q(assigne_a_technicien=user) | 
            Q(assigne_a_equipe__membres=user)
        )
        
        stats = {
            'mes_taches_total': mes_ot.exclude(statut__est_statut_final=True).count(),
            'mes_taches_en_retard': mes_ot.filter(
                date_prevue_debut__lt=timezone.now(),
                statut__est_statut_final=False
            ).count(),
            'mes_taches_aujourdhui': mes_ot.filter(
                date_prevue_debut__date=timezone.now().date()
            ).count(),
            'mes_demandes_reparation': DemandeReparation.objects.filter(
                cree_par=user
            ).count(),
        }
    
    # Graphique évolution cette semaine
    debut_semaine = timezone.now() - timedelta(days=7)
    evolution_semaine = []
    
    for i in range(7):
        date = debut_semaine + timedelta(days=i)
        count = OrdreDeTravail.objects.filter(
            date_fin_reelle__date=date.date()
        ).count()
        evolution_semaine.append({
            'date': date.strftime('%Y-%m-%d'),
            'completed': count
        })
    
    return JsonResponse({
        'statistiques': stats,
        'evolution_semaine': evolution_semaine,
        'timestamp': timezone.now().isoformat()
    })

@login_required
def recherche_globale(request):
    """
    API de recherche globale dans l'application
    """
    query = request.GET.get('q', '').strip()
    
    if not query or len(query) < 2:
        return JsonResponse({'results': []})
    
    results = []
    
    # Recherche dans les OT
    ots = OrdreDeTravail.objects.filter(
        Q(titre__icontains=query) |
        Q(id__icontains=query)
    )[:5]
    
    for ot in ots:
        results.append({
            'type': 'ordre_travail',
            'id': ot.id,
            'title': ot.titre,
            'subtitle': f"OT-{ot.id} - {ot.asset.nom}",
            'url': f"/ordres-travail/{ot.id}/",
            'icon': 'clipboard'
        })
    
    # Recherche dans les assets
    assets = Asset.objects.filter(
        Q(nom__icontains=query) |
        Q(reference__icontains=query)
    )[:5]
    
    for asset in assets:
        results.append({
            'type': 'asset',
            'id': asset.id,
            'title': asset.nom,
            'subtitle': f"{asset.reference} - {asset.get_statut_display()}",
            'url': f"/assets/{asset.id}/detail-enrichi/",
            'icon': 'cog'
        })
    
    # Recherche dans les demandes de réparation
    demandes = DemandeReparation.objects.filter(
        Q(numero_demande__icontains=query) |
        Q(titre__icontains=query)
    )[:5]
    
    for demande in demandes:
        results.append({
            'type': 'demande_reparation',
            'id': demande.id,
            'title': demande.numero_demande,
            'subtitle': f"{demande.titre} - {demande.get_statut_display()}",
            'url': f"/demandes-reparation/{demande.id}/",
            'icon': 'wrench'
        })
    
    return JsonResponse({
        'query': query,
        'results': results,
        'total': len(results)
    })



# ==============================================================================
# SUPPRESSION OPÉRATIONS
# ==============================================================================

@login_required
@user_passes_test(is_manager_or_admin)
def supprimer_operation(request, pk):
    """
    Supprime une opération et tous ses points de contrôle associés
    """
    operation = get_object_or_404(Operation, pk=pk)
    intervention = operation.intervention
    
    # Vérifier que l'intervention n'est pas validée
    if intervention.statut == 'VALIDATED':
        messages.error(request, "Impossible de supprimer une opération d'une intervention validée.")
        return redirect('intervention_builder', pk=intervention.pk)
    
    # Vérifier s'il y a des réponses associées aux points de contrôle
    points_avec_reponses = []
    for point in operation.points_de_controle.all():
        nb_reponses = Reponse.objects.filter(point_de_controle=point).count()
        if nb_reponses > 0:
            points_avec_reponses.append({
                'point': point,
                'nb_reponses': nb_reponses
            })
    
    if request.method == 'POST':
        # Confirmation de suppression
        confirmer = request.POST.get('confirmer_suppression')
        
        if confirmer == 'oui':
            try:
                with transaction.atomic():
                    operation_nom = operation.nom
                    nb_points = operation.points_de_controle.count()
                    
                    # Supprimer l'opération (cascade sur les points de contrôle)
                    operation.delete()
                    
                    # Réorganiser l'ordre des opérations restantes
                    operations_restantes = Operation.objects.filter(
                        intervention=intervention
                    ).order_by('ordre')
                    
                    for index, op in enumerate(operations_restantes, 1):
                        if op.ordre != index:
                            op.ordre = index
                            op.save()
                    
                    messages.success(
                        request, 
                        f'Opération "{operation_nom}" supprimée avec succès '
                        f'(ainsi que {nb_points} point(s) de contrôle associé(s)).'
                    )
                    
                return redirect('intervention_builder', pk=intervention.pk)
                
            except Exception as e:
                messages.error(request, f"Erreur lors de la suppression : {str(e)}")
                return redirect('intervention_builder', pk=intervention.pk)
        else:
            messages.info(request, "Suppression annulée.")
            return redirect('intervention_builder', pk=intervention.pk)
    
    # Si requête AJAX, retourner JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        if points_avec_reponses:
            return JsonResponse({
                'success': False,
                'error': 'Cette opération contient des points de contrôle avec des réponses existantes',
                'points_avec_reponses': [
                    {
                        'nom': p['point'].label,
                        'nb_reponses': p['nb_reponses']
                    } for p in points_avec_reponses
                ]
            }, status=400)
        
        try:
            with transaction.atomic():
                operation_nom = operation.nom
                nb_points = operation.points_de_controle.count()
                operation.delete()
                
                # Réorganiser l'ordre
                operations_restantes = Operation.objects.filter(
                    intervention=intervention
                ).order_by('ordre')
                
                for index, op in enumerate(operations_restantes, 1):
                    if op.ordre != index:
                        op.ordre = index
                        op.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Opération "{operation_nom}" supprimée ({nb_points} points de contrôle)'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    # Affichage du template de confirmation
    context = {
        'operation': operation,
        'intervention': intervention,
        'points_avec_reponses': points_avec_reponses,
        'nb_points_total': operation.points_de_controle.count(),
    }
    
    return render(request, 'core/operation/supprimer_operation.html', context)

@login_required
@user_passes_test(is_manager_or_admin)
def supprimer_operation_ajax(request, pk):
    """
    Suppression d'opération via AJAX (pour l'interface drag & drop)
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Méthode non autorisée'}, status=405)
    
    operation = get_object_or_404(Operation, pk=pk)
    intervention = operation.intervention
    
    # Vérifications de sécurité
    if intervention.statut == 'VALIDATED':
        return JsonResponse({
            'success': False,
            'error': 'Impossible de supprimer une opération d\'une intervention validée'
        }, status=400)
    
    # Vérifier s'il y a des réponses
    points_avec_reponses = []
    for point in operation.points_de_controle.all():
        if Reponse.objects.filter(point_de_controle=point).exists():
            points_avec_reponses.append(point.label)
    
    if points_avec_reponses:
        return JsonResponse({
            'success': False,
            'error': f'Cette opération contient des points avec des réponses : {", ".join(points_avec_reponses)}',
            'require_confirmation': True
        }, status=400)
    
    try:
        with transaction.atomic():
            operation_nom = operation.nom
            nb_points = operation.points_de_controle.count()
            operation.delete()
            
            # Réorganiser les ordres
            operations_restantes = Operation.objects.filter(
                intervention=intervention
            ).order_by('ordre')
            
            for index, op in enumerate(operations_restantes, 1):
                if op.ordre != index:
                    op.ordre = index
                    op.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Opération "{operation_nom}" supprimée ({nb_points} points de contrôle)',
            'intervention_id': intervention.id
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Erreur lors de la suppression : {str(e)}'
        }, status=500)

# ==============================================================================
# SUPPRESSION POINTS DE CONTRÔLE
# ==============================================================================

@login_required
@user_passes_test(is_manager_or_admin)
def supprimer_point_de_controle(request, pk):
    """
    Supprime un point de contrôle
    """
    point = get_object_or_404(PointDeControle, pk=pk)
    operation = point.operation
    intervention = operation.intervention
    
    # Vérifier que l'intervention n'est pas validée
    if intervention.statut == 'VALIDATED':
        messages.error(request, "Impossible de supprimer un point de contrôle d'une intervention validée.")
        return redirect('intervention_builder', pk=intervention.pk)
    
    # Vérifier s'il y a des réponses associées
    nb_reponses = Reponse.objects.filter(point_de_controle=point).count()
    reponses_existantes = nb_reponses > 0
    
    if request.method == 'POST':
        # Confirmation de suppression
        confirmer = request.POST.get('confirmer_suppression')
        
        if confirmer == 'oui':
            try:
                with transaction.atomic():
                    point_label = point.label
                    
                    # Supprimer le point de contrôle
                    point.delete()
                    
                    # Réorganiser l'ordre des points restants dans l'opération
                    points_restants = PointDeControle.objects.filter(
                        operation=operation
                    ).order_by('ordre')
                    
                    for index, p in enumerate(points_restants, 1):
                        if p.ordre != index:
                            p.ordre = index
                            p.save()
                    
                    messages.success(
                        request, 
                        f'Point de contrôle "{point_label}" supprimé avec succès'
                        + (f' (ainsi que {nb_reponses} réponse(s) associée(s))' if reponses_existantes else '') + '.'
                    )
                    
                return redirect('intervention_builder', pk=intervention.pk)
                
            except Exception as e:
                messages.error(request, f"Erreur lors de la suppression : {str(e)}")
                return redirect('intervention_builder', pk=intervention.pk)
        else:
            messages.info(request, "Suppression annulée.")
            return redirect('intervention_builder', pk=intervention.pk)
    
    # Si requête AJAX, traitement direct
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        if reponses_existantes:
            return JsonResponse({
                'success': False,
                'error': f'Ce point de contrôle a {nb_reponses} réponse(s) associée(s)',
                'require_confirmation': True,
                'nb_reponses': nb_reponses
            }, status=400)
        
        try:
            with transaction.atomic():
                point_label = point.label
                point.delete()
                
                # Réorganiser l'ordre
                points_restants = PointDeControle.objects.filter(
                    operation=operation
                ).order_by('ordre')
                
                for index, p in enumerate(points_restants, 1):
                    if p.ordre != index:
                        p.ordre = index
                        p.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Point de contrôle "{point_label}" supprimé',
                'operation_id': operation.id
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    # Affichage du template de confirmation
    context = {
        'point': point,
        'operation': operation,
        'intervention': intervention,
        'nb_reponses': nb_reponses,
        'reponses_existantes': reponses_existantes,
    }
    
    return render(request, 'core/point_controle/supprimer_point_controle.html', context)

@login_required
@user_passes_test(is_manager_or_admin)
def supprimer_point_de_controle_ajax(request, pk):
    """
    Suppression de point de contrôle via AJAX (pour l'interface drag & drop)
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Méthode non autorisée'}, status=405)
    
    point = get_object_or_404(PointDeControle, pk=pk)
    operation = point.operation
    intervention = operation.intervention
    
    # Vérifications de sécurité
    if intervention.statut == 'VALIDATED':
        return JsonResponse({
            'success': False,
            'error': 'Impossible de supprimer un point de contrôle d\'une intervention validée'
        }, status=400)
    
    # Vérifier s'il y a des réponses
    nb_reponses = Reponse.objects.filter(point_de_controle=point).count()
    if nb_reponses > 0:
        return JsonResponse({
            'success': False,
            'error': f'Ce point de contrôle a {nb_reponses} réponse(s) associée(s)',
            'require_confirmation': True,
            'nb_reponses': nb_reponses
        }, status=400)
    
    try:
        with transaction.atomic():
            point_label = point.label
            point.delete()
            
            # Réorganiser les ordres
            points_restants = PointDeControle.objects.filter(
                operation=operation
            ).order_by('ordre')
            
            for index, p in enumerate(points_restants, 1):
                if p.ordre != index:
                    p.ordre = index
                    p.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Point de contrôle "{point_label}" supprimé',
            'operation_id': operation.id
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Erreur lors de la suppression : {str(e)}'
        }, status=500)

# ==============================================================================
# SUPPRESSION AVEC CONFIRMATION FORCÉE
# ==============================================================================

@login_required
@user_passes_test(is_manager_or_admin)
def forcer_suppression_operation(request, pk):
    """
    Force la suppression d'une opération même si elle a des réponses
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Méthode non autorisée'}, status=405)
    
    operation = get_object_or_404(Operation, pk=pk)
    intervention = operation.intervention
    
    if intervention.statut == 'VALIDATED':
        return JsonResponse({
            'success': False,
            'error': 'Impossible de supprimer une opération d\'une intervention validée'
        }, status=400)
    
    confirmation = request.POST.get('confirmation')
    if confirmation != 'CONFIRMER_SUPPRESSION':
        return JsonResponse({
            'success': False,
            'error': 'Confirmation requise'
        }, status=400)
    
    try:
        with transaction.atomic():
            operation_nom = operation.nom
            
            # Compter les réponses qui vont être supprimées
            nb_reponses_total = 0
            for point in operation.points_de_controle.all():
                nb_reponses_total += Reponse.objects.filter(point_de_controle=point).count()
            
            # Supprimer l'opération (cascade)
            operation.delete()
            
            # Réorganiser
            operations_restantes = Operation.objects.filter(
                intervention=intervention
            ).order_by('ordre')
            
            for index, op in enumerate(operations_restantes, 1):
                if op.ordre != index:
                    op.ordre = index
                    op.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Opération "{operation_nom}" supprimée de force ({nb_reponses_total} réponses supprimées)',
            'intervention_id': intervention.id
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Erreur lors de la suppression forcée : {str(e)}'
        }, status=500)

@login_required
@user_passes_test(is_manager_or_admin)
def forcer_suppression_point_controle(request, pk):
    """
    Force la suppression d'un point de contrôle même s'il a des réponses
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Méthode non autorisée'}, status=405)
    
    point = get_object_or_404(PointDeControle, pk=pk)
    operation = point.operation
    intervention = operation.intervention
    
    if intervention.statut == 'VALIDATED':
        return JsonResponse({
            'success': False,
            'error': 'Impossible de supprimer un point de contrôle d\'une intervention validée'
        }, status=400)
    
    confirmation = request.POST.get('confirmation')
    if confirmation != 'CONFIRMER_SUPPRESSION':
        return JsonResponse({
            'success': False,
            'error': 'Confirmation requise'
        }, status=400)
    
    try:
        with transaction.atomic():
            point_label = point.label
            nb_reponses = Reponse.objects.filter(point_de_controle=point).count()
            
            # Supprimer le point (cascade sur les réponses)
            point.delete()
            
            # Réorganiser
            points_restants = PointDeControle.objects.filter(
                operation=operation
            ).order_by('ordre')
            
            for index, p in enumerate(points_restants, 1):
                if p.ordre != index:
                    p.ordre = index
                    p.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Point de contrôle "{point_label}" supprimé de force ({nb_reponses} réponses supprimées)',
            'operation_id': operation.id
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Erreur lors de la suppression forcée : {str(e)}'
        }, status=500)

# ==============================================================================
# VUES UTILITAIRES POUR LA VÉRIFICATION
# ==============================================================================

@login_required
@user_passes_test(is_manager_or_admin)
def verifier_suppressions_possibles(request, intervention_id):
    """
    Vérifie quels éléments peuvent être supprimés dans une intervention
    """
    intervention = get_object_or_404(Intervention, pk=intervention_id)
    
    if intervention.statut == 'VALIDATED':
        return JsonResponse({
            'can_delete_anything': False,
            'reason': 'Intervention validée'
        })
    
    suppressions_info = {
        'can_delete_anything': True,
        'operations': [],
        'points_controle': []
    }
    
    for operation in intervention.operations.all():
        op_info = {
            'id': operation.id,
            'nom': operation.nom,
            'can_delete': True,
            'nb_reponses': 0,
            'points_avec_reponses': []
        }
        
        for point in operation.points_de_controle.all():
            nb_reponses = Reponse.objects.filter(point_de_controle=point).count()
            
            point_info = {
                'id': point.id,
                'label': point.label,
                'can_delete': nb_reponses == 0,
                'nb_reponses': nb_reponses
            }
            
            if nb_reponses > 0:
                op_info['can_delete'] = False
                op_info['nb_reponses'] += nb_reponses
                op_info['points_avec_reponses'].append(point.label)
            
            suppressions_info['points_controle'].append(point_info)
        
        suppressions_info['operations'].append(op_info)
    
    return JsonResponse(suppressions_info)








# ==============================================================================
# FONCTIONS UTILITAIRES
# ==============================================================================

def _check_media_permissions(point, type_fichier):
    """
    Vérifie si le type de média est autorisé pour ce point
    """
    type_fichier = type_fichier.upper()
    
    if type_fichier == 'PHOTO' and not point.permettre_photo:
        return False
    elif type_fichier == 'VIDEO' and not point.permettre_video:
        return False
    elif type_fichier == 'AUDIO' and not point.permettre_audio:
        return False
    elif type_fichier == 'FILE' and not point.permettre_fichiers:
        return False
    
    return True


def _validate_file_type(fichier, point):
    """
    Valide le type de fichier selon les restrictions du point
    """
    if not point.types_fichiers_autorises:
        return True  # Aucune restriction
    
    file_ext = os.path.splitext(fichier.name)[1][1:].upper()
    types_autorises = [t.strip().upper() for t in point.types_fichiers_autorises.split(',')]
    
    return file_ext in types_autorises


def _process_image(fichier, max_size_mb):
    """
    Traite et compresse une image si nécessaire
    """
    try:
        # Ouvrir l'image avec Pillow
        image = Image.open(fichier)
        
        # Redimensionner si trop grande
        max_dimension = 1920  # pixels
        if image.width > max_dimension or image.height > max_dimension:
            image.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
        
        # Convertir en RGB si nécessaire
        if image.mode in ('RGBA', 'P'):
            image = image.convert('RGB')
        
        # Sauvegarder avec compression
        from io import BytesIO
        output = BytesIO()
        quality = 85
        
        # Ajuster la qualité selon la taille cible
        max_size_bytes = max_size_mb * 1024 * 1024
        
        while True:
            output.seek(0)
            output.truncate()
            image.save(output, format='JPEG', quality=quality, optimize=True)
            
            if output.tell() <= max_size_bytes or quality <= 20:
                break
            
            quality -= 10
        
        # Créer un nouveau fichier Django
        output.seek(0)
        new_name = f"compressed_{uuid.uuid4().hex}.jpg"
        return ContentFile(output.read(), name=new_name)
        
    except Exception:
        # En cas d'erreur, retourner le fichier original
        return fichier


def _format_file_size(size_bytes):
    """
    Formate la taille du fichier en unités lisibles
    """
    if size_bytes == 0:
        return "0 B"
    
    units = ['B', 'KB', 'MB', 'GB']
    unit_index = 0
    size = float(size_bytes)
    
    while size >= 1024.0 and unit_index < len(units) - 1:
        size /= 1024.0
        unit_index += 1
    
    return f"{size:.1f} {units[unit_index]}"


def _can_delete_media(user, media):
    """
    Vérifie si l'utilisateur peut supprimer ce média
    """
    user_role = get_user_role(user)
    
    # Admin et Manager peuvent toujours supprimer
    if user_role in ['ADMIN', 'MANAGER']:
        return True
    
    # Le technicien assigné peut supprimer pendant l'exécution
    ordre_travail = media.reponse.rapport_execution.ordre_de_travail
    
    if ordre_travail.assigne_a_technicien == user:
        return True
    
    if (ordre_travail.assigne_a_equipe and 
        user in ordre_travail.assigne_a_equipe.membres.all()):
        return True
    
    return False


# ==============================================================================
# VUES POUR LA SYNCHRONISATION HORS LIGNE (OPTIONNEL)
# ==============================================================================

@login_required
@require_http_methods(["POST"])
def sync_offline_data(request):
    """
    Synchronise les données sauvegardées hors ligne
    """
    try:
        data = json.loads(request.body)
        offline_data = data.get('offline_data', {})
        
        # Traiter chaque élément de données hors ligne
        results = []
        
        for item in offline_data:
            try:
                # Traitement selon le type de données
                if item.get('type') == 'draft':
                    # Sauvegarder le brouillon
                    save_result = _sync_draft_data(request.user, item)
                    results.append(save_result)
                    
                elif item.get('type') == 'media':
                    # Sauvegarder le média
                    save_result = _sync_media_data(request.user, item)
                    results.append(save_result)
                    
            except Exception as e:
                results.append({
                    'success': False,
                    'error': str(e),
                    'item_id': item.get('id')
                })
        
        return JsonResponse({
            'success': True,
            'results': results
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Erreur synchronisation: {str(e)}'
        }, status=500)


def _sync_draft_data(user, draft_item):
    """
    Synchronise un brouillon hors ligne
    """
    # Implémentation de la synchronisation de brouillon
    return {'success': True, 'item_id': draft_item.get('id')}


def _sync_media_data(user, media_item):
    """
    Synchronise un média hors ligne
    """
    # Implémentation de la synchronisation de média
    return {'success': True, 'item_id': media_item.get('id')}


# À ajouter dans core/views.py

@login_required
@require_http_methods(["POST"])
def save_draft_intervention(request, pk):
    """
    Sauvegarde des données de brouillon SANS validation des champs obligatoires
    """
    print(f"DEBUG: save_draft_intervention appelée avec pk={pk}")
    print(f"DEBUG: content_type={request.content_type}")
    print(f"DEBUG: user={request.user}")
    
    try:
        ordre_travail = get_object_or_404(OrdreDeTravail, pk=pk)
        print(f"DEBUG: ordre_travail trouvé - {ordre_travail}")
        
        # Vérifier les permissions
        user_role = get_user_role(request.user)
        print(f"DEBUG: user_role={user_role}")
        
        peut_executer = (
            ordre_travail.assigne_a_technicien == request.user or
            (ordre_travail.assigne_a_equipe and request.user in ordre_travail.assigne_a_equipe.membres.all()) or
            user_role in ['MANAGER', 'ADMIN']
        )
        
        print(f"DEBUG: peut_executer={peut_executer}")
        
        if not peut_executer:
            return JsonResponse({
                'success': False,
                'error': 'Permission refusée'
            }, status=403)
        
        # Récupérer les données JSON du brouillon
        if request.content_type == 'application/json':
            draft_data = json.loads(request.body)
        else:
            # Fallback pour form data
            draft_data = {key: value for key, value in request.POST.items() if key.startswith('reponse_')}
        
        print(f"DEBUG: draft_data={draft_data}")
        
        # Créer ou mettre à jour le rapport
        rapport, created = RapportExecution.objects.get_or_create(
            ordre_de_travail=ordre_travail,
            defaults={
                'statut_rapport': 'BROUILLON',
                'cree_par': request.user,
                'date_execution_debut': timezone.now()
            }
        )
        
        print(f"DEBUG: rapport {'créé' if created else 'existant'} - ID {rapport.id}")
        
        # Sauvegarder les réponses individuelles (SANS validation)
        saved_count = 0
        for key, value in draft_data.items():
            if key.startswith('reponse_') and value:
                try:
                    point_id = int(key.replace('reponse_', ''))
                    point = PointDeControle.objects.get(pk=point_id)
                    
                    # Créer ou mettre à jour la réponse
                    reponse, created = Reponse.objects.get_or_create(
                        rapport_execution=rapport,
                        point_de_controle=point,
                        defaults={
                            'valeur': str(value),
                            'est_conforme': True  # Par défaut conforme pour brouillon
                        }
                    )
                    
                    if not created:
                        reponse.valeur = str(value)
                        reponse.save()
                    
                    saved_count += 1
                    print(f"DEBUG: réponse {'créée' if created else 'mise à jour'} pour point {point_id}")
                        
                except (ValueError, PointDeControle.DoesNotExist) as e:
                    print(f"DEBUG: erreur pour {key}: {e}")
                    continue  # Ignorer les erreurs pour les brouillons
        
        print(f"DEBUG: {saved_count} réponses sauvegardées")
        
        return JsonResponse({
            'success': True,
            'message': f'Brouillon sauvegardé ({saved_count} réponses)'
        })
        
    except Exception as e:
        print(f"ERREUR save_draft_intervention: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': f'Erreur serveur: {str(e)}'
        }, status=500)
    
@login_required
@require_http_methods(["GET"])
def load_draft_intervention(request, pk):
    """
    Chargement des données de brouillon sauvegardées
    """
    try:
        ordre_travail = get_object_or_404(OrdreDeTravail, pk=pk)
        
        # Vérifier les permissions
        user_role = get_user_role(request.user)
        peut_executer = (
            ordre_travail.assigne_a_technicien == request.user or
            (ordre_travail.assigne_a_equipe and request.user in ordre_travail.assigne_a_equipe.membres.all()) or
            user_role in ['MANAGER', 'ADMIN']
        )
        
        if not peut_executer:
            return JsonResponse({
                'success': False,
                'error': 'Permission refusée'
            }, status=403)
        
        try:
            rapport = RapportExecution.objects.get(ordre_de_travail=ordre_travail)
            
            # Charger les réponses existantes
            reponses = Reponse.objects.filter(rapport_execution=rapport)
            draft_data = {}
            
            for reponse in reponses:
                key = f'reponse_{reponse.point_de_controle.id}'
                draft_data[key] = reponse.valeur
            
            return JsonResponse({
                'success': True,
                'draft': draft_data
            })
            
        except RapportExecution.DoesNotExist:
            return JsonResponse({
                'success': True,
                'draft': {}
            })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Erreur serveur: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def upload_media_ajax(request):
    """
    Upload de médias via AJAX pour les points de contrôle
    """
    try:
        fichier = request.FILES.get('fichier')
        point_id = request.POST.get('point_id')
        type_fichier = request.POST.get('type_fichier')
        ordre_travail_id = request.POST.get('ordre_travail_id')
        
        if not all([fichier, point_id, type_fichier, ordre_travail_id]):
            return JsonResponse({
                'success': False,
                'error': 'Paramètres manquants'
            }, status=400)
        
        # Vérifications
        point = get_object_or_404(PointDeControle, pk=point_id)
        ordre_travail = get_object_or_404(OrdreDeTravail, pk=ordre_travail_id)
        
        # Vérifier permissions
        user_role = get_user_role(request.user)
        peut_executer = (
            ordre_travail.assigne_a_technicien == request.user or
            (ordre_travail.assigne_a_equipe and request.user in ordre_travail.assigne_a_equipe.membres.all()) or
            user_role in ['MANAGER', 'ADMIN']
        )
        
        if not peut_executer:
            return JsonResponse({
                'success': False,
                'error': 'Permission refusée'
            }, status=403)
        
        # Vérifier si les médias sont autorisés pour ce point
        if not point.permettre_fichiers:
            return JsonResponse({
                'success': False,
                'error': 'Les fichiers ne sont pas autorisés pour ce point de contrôle'
            }, status=400)
        
        # Vérifier la taille du fichier (max 50MB)
        max_size = 50 * 1024 * 1024  # 50MB
        if fichier.size > max_size:
            return JsonResponse({
                'success': False,
                'error': 'Fichier trop volumineux (max 50MB)'
            }, status=400)
        
        # Créer le rapport s'il n'existe pas
        rapport, created = RapportExecution.objects.get_or_create(
            ordre_de_travail=ordre_travail,
            defaults={
                'statut_rapport': 'BROUILLON',
                'cree_par': request.user,
                'date_execution_debut': timezone.now()
            }
        )
        
        # Créer la réponse si elle n'existe pas
        reponse, created = Reponse.objects.get_or_create(
            rapport_execution=rapport,
            point_de_controle=point,
            defaults={
                'valeur': 'Média ajouté',
                'est_conforme': True
            }
        )
        
        # Créer le média
        media = FichierMedia.objects.create(
            reponse=reponse,
            fichier=fichier,
            nom_original=fichier.name,
            type_fichier=type_fichier.upper(),
            taille_octets=fichier.size,
            uploade_par=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Fichier uploadé avec succès',
            'media': {
                'id': media.id,
                'nom_original': media.nom_original,
                'type_fichier': media.type_fichier,
                'fichier_url': media.fichier.url,
                'point_id': point.id,
                'taille_octets': media.taille_octets
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Erreur upload: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def delete_media_ajax(request, media_id):
    """
    Suppression d'un média via AJAX
    """
    try:
        media = get_object_or_404(FichierMedia, pk=media_id)
        
        # Vérifier permissions
        ordre_travail = media.reponse.rapport_execution.ordre_de_travail
        user_role = get_user_role(request.user)
        peut_supprimer = (
            ordre_travail.assigne_a_technicien == request.user or
            (ordre_travail.assigne_a_equipe and request.user in ordre_travail.assigne_a_equipe.membres.all()) or
            media.uploade_par == request.user or
            user_role in ['MANAGER', 'ADMIN']
        )
        
        if not peut_supprimer:
            return JsonResponse({
                'success': False,
                'error': 'Permission refusée'
            }, status=403)
        
        # Supprimer le fichier physique
        if media.fichier:
            try:
                media.fichier.delete(save=False)
            except:
                pass  # Ignorer les erreurs de suppression de fichier
        
        # Supprimer l'enregistrement
        media.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Média supprimé'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Erreur suppression: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def get_medias_intervention(request, pk):
    """
    Récupération de tous les médias pour une intervention
    """
    try:
        ordre_travail = get_object_or_404(OrdreDeTravail, pk=pk)
        
        # Vérifier permissions
        user_role = get_user_role(request.user)
        peut_voir = (
            ordre_travail.assigne_a_technicien == request.user or
            (ordre_travail.assigne_a_equipe and request.user in ordre_travail.assigne_a_equipe.membres.all()) or
            user_role in ['MANAGER', 'ADMIN']
        )
        
        if not peut_voir:
            return JsonResponse({
                'success': False,
                'error': 'Permission refusée'
            }, status=403)
        
        try:
            rapport = RapportExecution.objects.get(ordre_de_travail=ordre_travail)
            medias = FichierMedia.objects.filter(
                reponse__rapport_execution=rapport
            ).select_related('reponse__point_de_controle')
            
            medias_data = []
            for media in medias:
                medias_data.append({
                    'id': media.id,
                    'nom_original': media.nom_original,
                    'type_fichier': media.type_fichier,
                    'fichier_url': media.fichier.url,
                    'point_id': media.reponse.point_de_controle.id,
                    'taille_octets': media.taille_octets,
                    'date_upload': media.date_upload.isoformat()
                })
            
            return JsonResponse({
                'success': True,
                'medias': medias_data
            })
            
        except RapportExecution.DoesNotExist:
            return JsonResponse({
                'success': True,
                'medias': []
            })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Erreur serveur: {str(e)}'
        }, status=500)




# À ajouter dans core/views.py

@login_required
@require_http_methods(["POST"])
def upload_media_complete(request):
    """
    Vue complète qui gère upload + permissions + création auto des objets manquants
    """
    try:
        fichier = request.FILES.get('fichier')
        point_id = request.POST.get('point_id')
        type_fichier = request.POST.get('type_fichier', 'PHOTO')
        ordre_travail_id = request.POST.get('ordre_travail_id')
        
        print(f"DEBUG upload_media_complete: fichier={fichier}, point_id={point_id}, type_fichier={type_fichier}, ordre_travail_id={ordre_travail_id}")
        
        if not fichier or not point_id or not ordre_travail_id:
            return JsonResponse({
                'success': False,
                'error': 'Paramètres manquants (fichier, point_id, ordre_travail_id requis)'
            }, status=400)
        
        # Récupérer les objets
        try:
            point = PointDeControle.objects.get(id=point_id)
            ordre_travail = OrdreDeTravail.objects.get(id=ordre_travail_id)
        except (PointDeControle.DoesNotExist, OrdreDeTravail.DoesNotExist):
            return JsonResponse({
                'success': False,
                'error': 'Point de contrôle ou ordre de travail introuvable'
            }, status=404)
        
        # Vérifier les permissions d'upload
        if not _check_media_permissions(point, type_fichier):
            return JsonResponse({
                'success': False,
                'error': f'Type de média non autorisé pour ce point. type_fichier={type_fichier}, permettre_photo={point.permettre_photo}, permettre_audio={point.permettre_audio}, permettre_video={point.permettre_video}, permettre_fichiers={point.permettre_fichiers}'
            }, status=403)
        
        # Vérifier permissions utilisateur
        user_role = get_user_role(request.user)
        peut_executer = (
            ordre_travail.assigne_a_technicien == request.user or
            (ordre_travail.assigne_a_equipe and request.user in ordre_travail.assigne_a_equipe.membres.all()) or
            user_role in ['MANAGER', 'ADMIN']
        )
        
        if not peut_executer:
            return JsonResponse({
                'success': False,
                'error': 'Permission refusée pour cet ordre de travail'
            }, status=403)
        
        # Vérifier la taille du fichier
        max_size = getattr(point, 'taille_max_fichier_mb', 10) * 1024 * 1024
        if fichier.size > max_size:
            return JsonResponse({
                'success': False,
                'error': f'Fichier trop volumineux. Taille max: {point.taille_max_fichier_mb}MB'
            }, status=400)
        
        # Créer ou récupérer le rapport d'exécution
        rapport, rapport_created = RapportExecution.objects.get_or_create(
            ordre_de_travail=ordre_travail,
            defaults={
                'statut_rapport': 'BROUILLON',
                'cree_par': request.user,
                'date_execution_debut': timezone.now()
            }
        )
        
        # Créer ou récupérer la réponse pour ce point
        reponse, reponse_created = Reponse.objects.get_or_create(
            rapport_execution=rapport,
            point_de_controle=point,
            defaults={
                'valeur': f'Média ajouté: {fichier.name}',
                'est_conforme': True
            }
        )
        
        # Si la réponse existait déjà, on met à jour la valeur
        if not reponse_created:
            reponse.valeur = f'Média mis à jour: {fichier.name}'
            reponse.save()
        
        # Créer le fichier média
        fichier_media = FichierMedia.objects.create(
            reponse=reponse,
            type_fichier=type_fichier.upper(),
            fichier=fichier,
            nom_original=fichier.name,
            taille_octets=fichier.size,
            uploade_par=request.user
        )
        
        # Préparer les données de réponse
        file_ext = os.path.splitext(fichier.name)[1] if '.' in fichier.name else ''
        is_image = file_ext.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.webp']
        is_video = file_ext.lower() in ['.mp4', '.avi', '.mov', '.webm']
        is_audio = file_ext.lower() in ['.mp3', '.wav', '.aac', '.m4a']
        
        media_data = {
            'id': fichier_media.id,
            'fichier_url': fichier_media.fichier.url,
            'nom_original': fichier_media.nom_original,
            'type_fichier': fichier_media.type_fichier,
            'taille_octets': fichier_media.taille_octets,
            'taille_formatee': _format_file_size(fichier_media.taille_octets),
            'date_upload': fichier_media.date_upload.isoformat(),
            'is_image': is_image,
            'is_video': is_video,
            'is_audio': is_audio,
            'extension': file_ext[1:] if file_ext else '',
            'point_id': point.id,
            'reponse_id': reponse.id
        }
        
        print(f"DEBUG: Média créé avec succès - {media_data}")
        
        return JsonResponse({
            'success': True,
            'message': f'Fichier {fichier.name} uploadé avec succès',
            'media': media_data
        })
        
    except Exception as e:
        print(f"ERREUR dans upload_media_complete: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': f'Erreur serveur: {str(e)}'
        }, status=500)

@login_required
@require_http_methods(["GET"])
def get_medias_point(request, point_id):
    """
    Récupère tous les médias pour un point de contrôle donné
    """
    print(f"DEBUG get_medias_point: appelée pour point_id={point_id}")
    
    try:
        point = get_object_or_404(PointDeControle, pk=point_id)
        print(f"DEBUG get_medias_point: point trouvé - {point.label}")
        
        # Récupérer les médias liés à ce point via les réponses
        medias = FichierMedia.objects.filter(
            reponse__point_de_controle=point
        ).select_related('reponse__rapport_execution__ordre_de_travail')
        
        print(f"DEBUG get_medias_point: {medias.count()} médias trouvés")
        
        medias_data = []
        for media in medias:
            print(f"DEBUG get_medias_point: traitement média {media.id} - {media.nom_original}")
            
            file_ext = os.path.splitext(media.nom_original)[1] if '.' in media.nom_original else ''
            is_image = file_ext.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.webp']
            is_video = file_ext.lower() in ['.mp4', '.avi', '.mov', '.webm']
            is_audio = file_ext.lower() in ['.mp3', '.wav', '.aac', '.m4a']
            
            medias_data.append({
                'id': media.id,
                'fichier_url': media.fichier.url,
                'nom_original': media.nom_original,
                'type_fichier': media.type_fichier,
                'taille_octets': media.taille_octets,
                'taille_formatee': _format_file_size(media.taille_octets),
                'date_upload': media.date_upload.isoformat(),
                'is_image': is_image,
                'is_video': is_video,
                'is_audio': is_audio,
                'extension': file_ext[1:] if file_ext else '',
                'point_id': point.id,
                'uploade_par': media.uploade_par.username if media.uploade_par else 'Inconnu'
            })
        
        print(f"DEBUG get_medias_point: retour de {len(medias_data)} médias")
        
        return JsonResponse({
            'success': True,
            'medias': medias_data
        })
        
    except Exception as e:
        print(f"ERREUR get_medias_point: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': f'Erreur serveur: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def delete_media_complete(request, media_id):
    """
    Supprime un média avec vérifications complètes
    """
    try:
        media = get_object_or_404(FichierMedia, pk=media_id)
        
        # Vérifier permissions
        ordre_travail = media.reponse.rapport_execution.ordre_de_travail
        user_role = get_user_role(request.user)
        peut_supprimer = (
            ordre_travail.assigne_a_technicien == request.user or
            (ordre_travail.assigne_a_equipe and request.user in ordre_travail.assigne_a_equipe.membres.all()) or
            media.uploade_par == request.user or
            user_role in ['MANAGER', 'ADMIN']
        )
        
        if not peut_supprimer:
            return JsonResponse({
                'success': False,
                'error': 'Permission refusée pour supprimer ce média'
            }, status=403)
        
        # Supprimer le fichier physique
        if media.fichier:
            try:
                media.fichier.delete(save=False)
            except Exception as e:
                print(f"Erreur suppression fichier physique: {e}")
        
        # Supprimer l'enregistrement
        media_name = media.nom_original
        media.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Média {media_name} supprimé avec succès'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Erreur serveur: {str(e)}'
        }, status=500)


def _format_file_size(size_bytes):
    """
    Formate la taille d'un fichier en format lisible
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"


# À ajouter dans core/views.py
# À ajouter/modifier dans core/views.py

import json
from decimal import Decimal, InvalidOperation
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Avg, Count
from django.core.paginator import Paginator
from django.db import models

from .models import Asset, CategorieAsset, OrdreDeTravail

@login_required
def carte_ftth(request):
    """
    Interface cartographique FTTH avec gestion robuste des erreurs
    """
    try:
        print(f"🗺️ Chargement de la carte FTTH pour l'utilisateur {request.user.username}")
        
        # ✅ CORRECTION: Récupérer TOUS les assets avec latitude/longitude non NULL
        all_assets = Asset.objects.filter(
            latitude__isnull=False,
            longitude__isnull=False
        ).select_related('categorie').prefetch_related('attributs_perso')
        
        print(f"📊 Nombre total d'assets trouvés: {all_assets.count()}")
        
        # Préparer les données GeoJSON avec validation stricte
        assets_geojson = {
            "type": "FeatureCollection",
            "features": []
        }
        
        assets_valides = 0
        assets_ignores = 0
        
        # ✅ CORRECTION: Compter tous les assets, même ceux avec coordonnées invalides
        for asset in all_assets:
            feature = prepare_asset_geojson(asset)
            if feature:
                assets_geojson["features"].append(feature)
                assets_valides += 1
            else:
                assets_ignores += 1  # ✅ Maintenant on compte les assets ignorés
        
        # ✅ CORRECTION: Calculer le centre seulement sur les assets valides
        valid_assets = [asset for asset in all_assets if validate_coordinates(asset.latitude, asset.longitude)]
        center_lat, center_lng = calculate_map_center(valid_assets)
        
        # Calculer les statistiques sur tous les assets
        stats = {
            'total_assets': assets_valides,
            'en_service': all_assets.filter(statut='en_service').count(),
            'en_panne': all_assets.filter(statut='en_panne').count(),
            'en_maintenance': all_assets.filter(statut='en_maintenance').count(),
            'hors_service': all_assets.filter(statut='hors_service').count(),
            'categories': []
        }
        
        # Statistiques par catégorie
        try:
            categories_stats = all_assets.values('categorie__nom').annotate(
                count=Count('id')
            ).order_by('-count')
            
            for cat_stat in categories_stats:
                if cat_stat['categorie__nom']:
                    stats['categories'].append({
                        'nom': cat_stat['categorie__nom'],
                        'count': cat_stat['count']
                    })
        except Exception as e:
            print(f"⚠️ Erreur lors du calcul des statistiques: {e}")
            stats['categories'] = []
        
        # Préparer le contexte
        context = {
            'assets_geojson': json.dumps(assets_geojson),
            'stats': stats,
            'center_lat': center_lat,
            'center_lng': center_lng,
            'categories': CategorieAsset.objects.all(),
            'assets_valides': assets_valides,
            'assets_ignores': assets_ignores,  # ✅ Maintenant correct
            'default_region': getattr(settings, 'GMAO_DEFAULT_REGION', 'france'),
        }
        
        print(f"✅ Carte FTTH: {assets_valides} assets valides, {assets_ignores} ignorés")
        
        return render(request, 'core/carte/carte_ftth.html', context)
        
    except Exception as e:
        print(f"❌ Erreur critique dans carte_ftth: {e}")
        
        # Contexte d'urgence en cas d'erreur
        default_center = get_default_center()
        context = {
            'assets_geojson': json.dumps({"type": "FeatureCollection", "features": []}),
            'stats': {
                'total_assets': 0,
                'en_service': 0,
                'en_panne': 0,
                'en_maintenance': 0,
                'hors_service': 0,
                'categories': []
            },
            'center_lat': default_center['lat'],
            'center_lng': default_center['lng'],
            'categories': CategorieAsset.objects.all(),
            'assets_valides': 0,
            'assets_ignores': 0,
            'error_message': "Erreur lors du chargement des données cartographiques",
            'default_region': getattr(settings, 'GMAO_DEFAULT_REGION', 'france'),
        }
        
        return render(request, 'core/carte/carte_ftth.html', context)
        
    except Exception as e:
        print(f"Erreur dans carte_ftth: {e}")
        
        # Contexte d'urgence en cas d'erreur
        context = {
            'assets_geojson': json.dumps({"type": "FeatureCollection", "features": []}),
            'stats': {
                'total_assets': 0,
                'en_service': 0,
                'en_panne': 0,
                'en_maintenance': 0,
                'categories': []
            },
            'center_lat': 48.8566,  # Paris par défaut
            'center_lng': 2.3522,
            'categories': CategorieAsset.objects.all(),
            'error_message': "Erreur lors du chargement des données cartographiques"
        }
        
        return render(request, 'core/carte/carte_ftth.html', context)


def _validate_coordinates(latitude, longitude):
    """
    Valide que les coordonnées sont utilisables
    """
    try:
        if latitude is None or longitude is None:
            return False
            
        # Convertir en float si c'est un Decimal
        if isinstance(latitude, Decimal):
            latitude = float(latitude)
        if isinstance(longitude, Decimal):
            longitude = float(longitude)
            
        # Vérifier les types
        if not isinstance(latitude, (int, float)) or not isinstance(longitude, (int, float)):
            return False
            
        # Vérifier les valeurs NaN
        if latitude != latitude or longitude != longitude:  # Test NaN
            return False
            
        # Vérifier les plages valides
        if latitude < -90 or latitude > 90:
            return False
        if longitude < -180 or longitude > 180:
            return False
            
        # Exclure les coordonnées nulles (souvent des valeurs par défaut erronées)
        if latitude == 0 and longitude == 0:
            return False
            
        return True
        
    except (TypeError, ValueError, InvalidOperation):
        return False


def _calculate_map_center(assets):
    """
    Calcule le centre de la carte de manière sécurisée
    """
    try:
        # Tenter de calculer la moyenne des coordonnées
        aggregates = assets.aggregate(
            avg_lat=Avg('latitude'),
            avg_lng=Avg('longitude')
        )
        
        center_lat = aggregates.get('avg_lat')
        center_lng = aggregates.get('avg_lng')
        
        # Valider les résultats
        if _validate_coordinates(center_lat, center_lng):
            return float(center_lat), float(center_lng)
        else:
            raise ValueError("Coordonnées moyennes invalides")
            
    except Exception as e:
        print(f"Erreur calcul centre carte: {e}")
        # Fallback vers Paris
        return 48.8566, 2.3522




@csrf_exempt
@require_http_methods(["DELETE"])
def delete_equipment_api(request, asset_id):
    """
    API pour supprimer un équipement
    """
    try:
        asset = Asset.objects.get(id=asset_id)
        asset_name = asset.nom
        asset.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Équipement {asset_name} supprimé'
        })
        
    except Asset.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Équipement non trouvé'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Erreur: {str(e)}'
        }, status=500)
    


# À ajouter dans core/views.py

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from decimal import Decimal

@csrf_exempt
@require_http_methods(["POST"])
def create_equipment_api(request):
    """
    API pour créer un nouvel équipement depuis la carte
    """
    try:
        data = json.loads(request.body)
        
        # Validation des données
        required_fields = ['type', 'name', 'latitude', 'longitude', 'status']
        for field in required_fields:
            if field not in data:
                return JsonResponse({
                    'success': False,
                    'error': f'Champ requis manquant: {field}'
                }, status=400)
        
        # Déterminer la catégorie selon le type
        type_to_category = {
            'NRO': 'NRO',
            'PM': 'Point de Mutualisation', 
            'PB': 'Point de Branchement',
            'PTO': 'Prise Terminale Optique'
        }
        
        category_name = type_to_category.get(data['type'], 'Équipement FTTH')
        category, created = CategorieAsset.objects.get_or_create(nom=category_name)
        
        # Créer l'asset
        asset = Asset.objects.create(
            nom=data['name'],
            reference=data.get('reference', data['name']),
            categorie=category,
            marque=data.get('brand', ''),
            modele=data.get('model', ''),
            statut=data['status'],
            criticite=data.get('criticality', 'MOYENNE'),
            latitude=Decimal(str(data['latitude'])),
            longitude=Decimal(str(data['longitude'])),
            localisation_texte=data.get('location', ''),
            date_mise_en_service=data.get('service_date') or None,
            fin_garantie=data.get('warranty_end') or None,
            
            # Champs FTTH spécifiques
            nb_fibres_total=data.get('fibers_total', None),
            nb_fibres_utilisees=data.get('fibers_used', 0),
            type_connecteur=data.get('connector', ''),
            niveau_hierarchique=get_hierarchy_level(data['type'])
        )
        
        # La géométrie sera automatiquement mise à jour par la méthode save()
        
        # Ajouter des attributs personnalisés si nécessaire
        if data.get('notes'):
            AttributPersonnaliseAsset.objects.create(
                asset=asset,
                cle='Notes',
                valeur=data['notes']
            )
        
        return JsonResponse({
            'success': True,
            'asset_id': asset.id,
            'coordinates': asset.coordinates_dict,
            'point_geojson': asset.point_geojson,
            'message': f'Équipement {asset.nom} créé avec succès'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Données JSON invalides'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Erreur serveur: {str(e)}'
        }, status=500)


def get_hierarchy_level(equipment_type):
    """
    Retourne le niveau hiérarchique selon le type d'équipement
    """
    hierarchy = {
        'NRO': 1,
        'PM': 2,
        'PB': 3,
        'PTO': 4
    }
    return hierarchy.get(equipment_type, 1)


@csrf_exempt
@require_http_methods(["POST"])
def create_cable_api(request):
    """
    API pour créer un câble/segment depuis la carte
    """
    try:
        data = json.loads(request.body)
        
        # Validation
        required_fields = ['points', 'startRef', 'endRef']
        for field in required_fields:
            if field not in data:
                return JsonResponse({
                    'success': False,
                    'error': f'Champ requis manquant: {field}'
                }, status=400)
        
        # Créer ou récupérer la zone géographique
        zone, created = ZoneGeographique.objects.get_or_create(
            nom=data.get('zone', 'Zone par défaut'),
            defaults={
                'code_postal': '00000',
                'commune': 'Non définie',
                'type_zone': 'ZONE_DENSE',
                'contour_geojson': {}
            }
        )
        
        # Préparer la géométrie GeoJSON
        coordinates = [[point['lng'], point['lat']] for point in data['points']]
        geometry_geojson = {
            "type": "LineString",
            "coordinates": coordinates
        }
        
        # Créer le plan/schéma pour le câble
        plan = PlanSchema.objects.create(
            nom=data.get('name', f"Câble {data['startRef']} - {data['endRef']}"),
            zone_geographique=zone,
            type_plan='SCHEMA_RACCORDEMENT',
            emprise_geojson=geometry_geojson,
            version="1.0"
        )
        
        # Associer les assets concernés si ils existent
        if data.get('startAssetId'):
            try:
                start_asset = Asset.objects.get(id=data['startAssetId'])
                plan.assets_concernes.add(start_asset)
            except Asset.DoesNotExist:
                pass
                
        if data.get('endAssetId'):
            try:
                end_asset = Asset.objects.get(id=data['endAssetId'])
                plan.assets_concernes.add(end_asset)
            except Asset.DoesNotExist:
                pass
        
        # Optionnel: Créer un asset pour le câble lui-même
        if data.get('createAsset', True):
            cable_category, created = CategorieAsset.objects.get_or_create(
                nom='Câble FTTH'
            )
            
            cable_asset = Asset.objects.create(
                nom=plan.nom,
                reference=f"CBL-{plan.id}",
                categorie=cable_category,
                statut='EN_SERVICE',
                criticite='MOYENNE',
                geometrie_geojson=geometry_geojson,
                nb_fibres_total=data.get('fiberCount', 12),
                type_connecteur=data.get('cableType', 'LC')
            )
            
            plan.assets_concernes.add(cable_asset)
        
        return JsonResponse({
            'success': True,
            'plan_id': plan.id,
            'cable_asset_id': cable_asset.id if 'cable_asset' in locals() else None,
            'message': f'Câble {plan.nom} créé avec succès',
            'length': data.get('distance', 0)
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Données JSON invalides'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Erreur serveur: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["PUT"])
def update_equipment_api(request, asset_id):
    """
    API pour modifier un équipement
    """
    try:
        asset = Asset.objects.get(id=asset_id)
        data = json.loads(request.body)
        
        # Mise à jour des champs
        if 'name' in data:
            asset.nom = data['name']
        if 'status' in data:
            asset.statut = data['status']
        if 'criticality' in data:
            asset.criticite = data['criticality']
        if 'fibers' in data:
            asset.nb_fibres_total = data['fibers']
        if 'connector' in data:
            asset.type_connecteur = data['connector']
            
        asset.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Équipement {asset.nom} mis à jour'
        })
        
    except Asset.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Équipement non trouvé'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Erreur: {str(e)}'
        }, status=500)


@require_http_methods(["GET"])
def find_nearby_equipment_api(request):
    """
    API pour trouver les équipements proches d'un point
    """
    try:
        latitude = float(request.GET.get('lat'))
        longitude = float(request.GET.get('lng'))
        radius = int(request.GET.get('radius', 100))  # 100m par défaut
        
        # Utiliser la nouvelle méthode find_nearby
        nearby_assets = Asset.find_nearby(latitude, longitude, radius)
        
        equipment_list = []
        for asset in nearby_assets:
            if asset.is_geolocated:
                distance = asset.distance_to_point(latitude, longitude)
                equipment_list.append({
                    'id': asset.id,
                    'name': asset.nom,
                    'type': asset.categorie.nom if asset.categorie else 'Inconnu',
                    'reference': asset.reference,
                    'coordinates': asset.coordinates_dict,
                    'distance': round(distance, 1) if distance else None,
                    'status': asset.statut
                })
        
        # Trier par distance
        equipment_list.sort(key=lambda x: x['distance'] if x['distance'] else float('inf'))
        
        return JsonResponse({
            'success': True,
            'count': len(equipment_list),
            'equipments': equipment_list
        })
        
    except (ValueError, TypeError):
        return JsonResponse({
            'success': False,
            'error': 'Paramètres lat/lng invalides'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Erreur: {str(e)}'
        }, status=500)


@require_http_methods(["GET"])
def equipment_list_api(request):
    """
    API pour lister tous les équipements géolocalisés
    """
    try:
        # Filtrer les assets géolocalisés
        assets = Asset.objects.filter(
            latitude__isnull=False,
            longitude__isnull=False
        ).select_related('categorie')
        
        equipment_list = []
        for asset in assets:
            equipment_list.append({
                'id': asset.id,
                'name': asset.nom,
                'reference': asset.reference,
                'type': asset.categorie.nom if asset.categorie else 'Inconnu',
                'brand': asset.marque,
                'model': asset.modele,
                'status': asset.statut,
                'criticality': asset.criticite,
                'coordinates': asset.coordinates_dict,
                'point_geojson': asset.point_geojson,
                'fibers_total': asset.nb_fibres_total,
                'fibers_used': asset.nb_fibres_utilisees,
                'location': asset.localisation_texte,
                'service_date': asset.date_mise_en_service.isoformat() if asset.date_mise_en_service else None,
                'warranty_end': asset.fin_garantie.isoformat() if asset.fin_garantie else None
            })
        
        return JsonResponse({
            'success': True,
            'count': len(equipment_list),
            'equipments': equipment_list
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Erreur: {str(e)}'
        }, status=500)
    
import json
import logging
from decimal import Decimal, InvalidOperation
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Avg, Count, Q
from django.core.paginator import Paginator
from django.db import models
from django.conf import settings

from .models import Asset, CategorieAsset, OrdreDeTravail

# Configuration du logging
logger = logging.getLogger(__name__)

# Configuration des coordonnées par défaut selon la région
DEFAULT_COORDINATES = {
    'france': {'lat': 46.603354, 'lng': 1.888334},  # Centre de la France
    'paris': {'lat': 48.8566, 'lng': 2.3522},       # Paris
    'lyon': {'lat': 45.7640, 'lng': 4.8357},        # Lyon
    'marseille': {'lat': 43.2965, 'lng': 5.3698},   # Marseille
}

def get_default_center():
    """
    Retourne les coordonnées par défaut selon la configuration
    """
    region = getattr(settings, 'GMAO_DEFAULT_REGION', 'france')
    return DEFAULT_COORDINATES.get(region, DEFAULT_COORDINATES['france'])

def validate_coordinates(latitude, longitude):
    """
    Valide que les coordonnées sont utilisables et géographiquement correctes
    
    Args:
        latitude: Latitude à valider
        longitude: Longitude à valider
        
    Returns:
        bool: True si les coordonnées sont valides
    """
    try:
        # Vérifier que les valeurs ne sont pas None
        if latitude is None or longitude is None:
            return False
            
        # Convertir en float si c'est un Decimal
        if isinstance(latitude, Decimal):
            latitude = float(latitude)
        if isinstance(longitude, Decimal):
            longitude = float(longitude)
            
        # Vérifier les types
        if not isinstance(latitude, (int, float)) or not isinstance(longitude, (int, float)):
            return False
            
        # Vérifier les valeurs NaN et infinies
        if (latitude != latitude or longitude != longitude or  # Test NaN
            latitude == float('inf') or latitude == float('-inf') or
            longitude == float('inf') or longitude == float('-inf')):
            return False
            
        # Vérifier les plages valides GPS
        if not (-90 <= latitude <= 90):
            return False
        if not (-180 <= longitude <= 180):
            return False
            
        # Exclure les coordonnées nulles (souvent des valeurs par défaut erronées)
        if latitude == 0 and longitude == 0:
            return False
            
        # Vérifier les coordonnées aberrantes (océan, pôles)
        # Pour la France métropolitaine et DOM-TOM, on peut être plus strict
        if hasattr(settings, 'GMAO_STRICT_COORDINATES') and settings.GMAO_STRICT_COORDINATES:
            # Coordonnées approximatives de la France étendue
            if not (41.0 <= latitude <= 51.5 and -5.5 <= longitude <= 10.0):
                # Vérifier les DOM-TOM
                dom_tom_ranges = [
                    (14.0, 18.5, -63.5, -60.5),  # Antilles
                    (3.0, 6.0, -55.0, -51.0),    # Guyane
                    (-23.0, -20.0, 54.0, 57.0),  # Réunion
                    (-13.0, -11.0, 44.0, 47.0),  # Mayotte
                ]
                
                valid_dom_tom = False
                for min_lat, max_lat, min_lng, max_lng in dom_tom_ranges:
                    if min_lat <= latitude <= max_lat and min_lng <= longitude <= max_lng:
                        valid_dom_tom = True
                        break
                
                if not valid_dom_tom:
                    return False
            
        return True
        
    except (TypeError, ValueError, InvalidOperation):
        return False

def calculate_map_center(assets):
    """
    Calcule le centre de la carte de manière sécurisée
    
    Args:
        assets: QuerySet d'assets avec coordonnées
        
    Returns:
        tuple: (latitude, longitude) du centre
    """
    try:
        # Filtrer les assets avec coordonnées valides
        valid_assets = []
        for asset in assets:
            if validate_coordinates(asset.latitude, asset.longitude):
                valid_assets.append(asset)
        
        if not valid_assets:
            logger.warning("Aucun asset avec coordonnées valides trouvé")
            default_center = get_default_center()
            return default_center['lat'], default_center['lng']
        
        # Calculer la moyenne des coordonnées valides
        total_lat = sum(float(asset.latitude) for asset in valid_assets)
        total_lng = sum(float(asset.longitude) for asset in valid_assets)
        
        center_lat = total_lat / len(valid_assets)
        center_lng = total_lng / len(valid_assets)
        
        # Valider le centre calculé
        if validate_coordinates(center_lat, center_lng):
            logger.info(f"Centre calculé: {center_lat}, {center_lng} sur {len(valid_assets)} assets")
            return center_lat, center_lng
        else:
            logger.warning("Centre calculé invalide, utilisation du centre par défaut")
            default_center = get_default_center()
            return default_center['lat'], default_center['lng']
            
    except Exception as e:
        logger.error(f"Erreur lors du calcul du centre de carte: {e}")
        default_center = get_default_center()
        return default_center['lat'], default_center['lng']

def prepare_asset_geojson(asset):
    """
    Prépare les données GeoJSON pour un asset
    
    Args:
        asset: Instance d'Asset
        
    Returns:
        dict: Feature GeoJSON ou None si invalide
    """
    try:
        # Validation des coordonnées
        if not validate_coordinates(asset.latitude, asset.longitude):
            return None
        
        # Récupérer les attributs personnalisés
        attributs = {}
        try:
            for attr in asset.attributs_perso.all():
                attributs[attr.cle] = attr.valeur
        except Exception as e:
            logger.warning(f"Erreur lors de la récupération des attributs pour asset {asset.id}: {e}")
            attributs = {}
        
        # Déterminer l'icône selon la catégorie
        icon_type = "default"
        if asset.categorie:
            icon_type = asset.categorie.nom.lower().replace(' ', '_')
        
        # Déterminer la couleur selon le statut
        status_colors = {
            'en_service': '#10b981',
            'en_panne': '#ef4444',
            'en_maintenance': '#f59e0b',
            'hors_service': '#6b7280',
        }
        
        asset_color = status_colors.get(asset.statut, '#6b7280')
        
        # Construire la feature GeoJSON
        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [float(asset.longitude), float(asset.latitude)]
            },
            "properties": {
                "id": asset.id,
                "nom": asset.nom or "Asset sans nom",
                "reference": asset.reference or "",
                "categorie": asset.categorie.nom if asset.categorie else "Non définie",
                "statut": asset.get_statut_display(),
                "criticite": asset.get_criticite_display(),
                "localisation": asset.localisation_texte or "",
                "adresse": asset.adresse_complete or "",
                "icon_type": icon_type,
                "color": asset_color,
                "attributs": attributs,
                "derniere_maintenance": asset.derniere_maintenance.isoformat() if asset.derniere_maintenance else None,
                "prochaine_maintenance": asset.prochaine_maintenance.isoformat() if asset.prochaine_maintenance else None,
            }
        }
        
        return feature
        
    except Exception as e:
        logger.error(f"Erreur lors de la préparation GeoJSON pour asset {asset.id}: {e}")
        return None

@login_required
def carte_ftth(request):
    """
    Interface cartographique FTTH avec gestion robuste des erreurs
    """
    try:
        logger.info(f"Chargement de la carte FTTH pour l'utilisateur {request.user.username}")
        
        # Récupérer tous les assets avec coordonnées potentiellement valides
        assets = Asset.objects.filter(
            latitude__isnull=False,
            longitude__isnull=False
        ).exclude(
            # Exclure les coordonnées évidemment invalides
            Q(latitude=0) | Q(longitude=0)
        ).select_related('categorie').prefetch_related('attributs_perso')
        
        logger.info(f"Nombre d'assets trouvés: {assets.count()}")
        
        # Préparer les données GeoJSON avec validation stricte
        assets_geojson = {
            "type": "FeatureCollection",
            "features": []
        }
        
        assets_valides = 0
        assets_ignores = 0
        
        for asset in assets:
            feature = prepare_asset_geojson(asset)
            if feature:
                assets_geojson["features"].append(feature)
                assets_valides += 1
            else:
                assets_ignores += 1
        
        # Calculer le centre de la carte
        center_lat, center_lng = calculate_map_center(assets)
        
        # Calculer les statistiques
        stats = {
            'total_assets': assets_valides,
            'en_service': assets.filter(statut='en_service').count(),
            'en_panne': assets.filter(statut='en_panne').count(),
            'en_maintenance': assets.filter(statut='en_maintenance').count(),
            'hors_service': assets.filter(statut='hors_service').count(),
            'categories': []
        }
        
        # Statistiques par catégorie
        categories_stats = assets.values('categorie__nom').annotate(
            count=Count('id')
        ).order_by('-count')
        
        for cat_stat in categories_stats:
            if cat_stat['categorie__nom']:
                stats['categories'].append({
                    'nom': cat_stat['categorie__nom'],
                    'count': cat_stat['count']
                })
        
        # Préparer le contexte
        context = {
            'assets_geojson': json.dumps(assets_geojson),
            'stats': stats,
            'center_lat': center_lat,
            'center_lng': center_lng,
            'categories': CategorieAsset.objects.all(),
            'assets_valides': assets_valides,
            'assets_ignores': assets_ignores,
            'default_region': getattr(settings, 'GMAO_DEFAULT_REGION', 'france'),
        }
        
        # Log pour debugging
        logger.info(f"Carte FTTH: {assets_valides} assets valides, {assets_ignores} ignorés")
        logger.info(f"Centre de carte: {center_lat}, {center_lng}")
        
        return render(request, 'core/carte/carte_ftth.html', context)
        
    except Exception as e:
        logger.error(f"Erreur critique dans carte_ftth: {e}", exc_info=True)
        
        # Contexte d'urgence en cas d'erreur
        default_center = get_default_center()
        context = {
            'assets_geojson': json.dumps({"type": "FeatureCollection", "features": []}),
            'stats': {
                'total_assets': 0,
                'en_service': 0,
                'en_panne': 0,
                'en_maintenance': 0,
                'hors_service': 0,
                'categories': []
            },
            'center_lat': default_center['lat'],
            'center_lng': default_center['lng'],
            'categories': CategorieAsset.objects.all(),
            'assets_valides': 0,
            'assets_ignores': 0,
            'error_message': "Erreur lors du chargement des données cartographiques",
            'default_region': getattr(settings, 'GMAO_DEFAULT_REGION', 'france'),
        }
        
        return render(request, 'core/carte/carte_ftth.html', context)

@login_required
def asset_details_ajax(request, asset_id):
    """
    Détails d'un asset via AJAX pour la popup carte
    """
    try:
        asset = get_object_or_404(Asset, pk=asset_id)
        print(f"📋 Récupération des détails pour asset {asset_id}")
        
        # ... (rest of your existing logic for derniers_ots, enfants, assets_proches)
        
        # Préparer la réponse avec validation des données
        data = {
            'success': True,
            'asset': {
                'id': asset.id,
                'nom': asset.nom or "Asset sans nom",
                'reference': asset.reference or "",
                'categorie': asset.categorie.nom if asset.categorie else "Non définie",
                'statut': asset.get_statut_display(),
                'criticite': asset.get_criticite_display(),
                'localisation': asset.localisation_texte or "",
                'adresse': asset.adresse_complete or "",
                'coordinates': {
                    'latitude': float(asset.latitude) if asset.latitude else None,
                    'longitude': float(asset.longitude) if asset.longitude else None,
                    'valid': validate_coordinates(asset.latitude, asset.longitude)
                },
                'photo': asset.photo_principale.url if asset.photo_principale else None,
                'derniere_maintenance': asset.derniere_maintenance.strftime('%d/%m/%Y %H:%M') if asset.derniere_maintenance else None,
                'prochaine_maintenance': asset.prochaine_maintenance.strftime('%d/%m/%Y %H:%M') if asset.prochaine_maintenance else None,
            }
        }
        
        print(f"✅ Détails asset {asset_id} récupérés avec succès")
        return JsonResponse(data)
        
    except Http404:
        # ✅ CORRECTION: Retourner explicitement 404 pour les assets non trouvés
        print(f"❌ Asset {asset_id} non trouvé")
        return JsonResponse({
            'success': False,
            'error': 'Asset non trouvé'
        }, status=404)
    except Exception as e:
        # ✅ CORRECTION: Autres erreurs = 500
        print(f"❌ Erreur lors de la récupération des détails pour asset {asset_id}: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
    
@login_required
def api_assets_search(request):
    """
    API de recherche d'assets avec gestion d'erreurs
    """
    try:
        query = request.GET.get('q', '').strip()
        
        if not query or len(query) < 2:
            return JsonResponse({
                'success': False,
                'error': 'Requête de recherche trop courte (minimum 2 caractères)',
                'results': []
            })
        
        # Recherche dans les assets
        assets = Asset.objects.filter(
            Q(nom__icontains=query) |
            Q(reference__icontains=query) |
            Q(localisation_texte__icontains=query)
        ).select_related('categorie')[:20]  # Limiter à 20 résultats
        
        results = []
        for asset in assets:
            # Vérifier que l'asset a des coordonnées valides
            has_valid_coordinates = validate_coordinates(asset.latitude, asset.longitude)
            
            results.append({
                'id': asset.id,
                'nom': asset.nom or "Asset sans nom",
                'reference': asset.reference or "",
                'categorie': asset.categorie.nom if asset.categorie else "Non définie",
                'localisation': asset.localisation_texte or "",
                'statut': asset.get_statut_display(),
                'coordinates': {
                    'latitude': float(asset.latitude) if asset.latitude else None,
                    'longitude': float(asset.longitude) if asset.longitude else None,
                    'valid': has_valid_coordinates
                },
                'can_show_on_map': has_valid_coordinates
            })
        
        return JsonResponse({
            'success': True,
            'results': results,
            'total': len(results),
            'query': query
        })
        
    except Exception as e:
        logger.error(f"Erreur lors de la recherche d'assets: {e}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': f'Erreur lors de la recherche: {str(e)}',
            'results': []
        }, status=500)

# Fonction utilitaire pour nettoyer les coordonnées en base (à exécuter via management command)
def clean_invalid_coordinates():
    """
    Nettoie les coordonnées invalides en base de données
    Cette fonction peut être appelée via un management command
    """
    logger.info("Début du nettoyage des coordonnées invalides")
    
    assets = Asset.objects.filter(
        latitude__isnull=False,
        longitude__isnull=False
    )
    
    cleaned_count = 0
    for asset in assets:
        if not validate_coordinates(asset.latitude, asset.longitude):
            logger.warning(f"Asset {asset.id} a des coordonnées invalides: {asset.latitude}, {asset.longitude}")
            # Option 1: Mettre à NULL
            asset.latitude = None
            asset.longitude = None
            asset.save()
            cleaned_count += 1
            
            # Option 2: Marquer comme nécessitant une vérification
            # asset.needs_coordinate_verification = True
            # asset.save()
    
    logger.info(f"Nettoyage terminé: {cleaned_count} assets nettoyés")
    return cleaned_count