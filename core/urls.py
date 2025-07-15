# Fichier : core/urls.py - Version corrigée sans doublons

from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views 
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views, api_views_mobile

# ==============================================================================
# CONFIGURATION DU ROUTEUR API
# ==============================================================================

# Routeur pour l'API mobile
mobile_router = DefaultRouter()
mobile_router.register('auth', api_views_mobile.MobileAuthViewSet, basename='mobile-auth')
mobile_router.register('ordres-travail', api_views_mobile.OrdreDeTravailMobileViewSet, basename='mobile-ot')
mobile_router.register('reponses', api_views_mobile.ReponseMobileViewSet, basename='mobile-reponses')
mobile_router.register('medias', api_views_mobile.FichierMediaMobileViewSet, basename='mobile-medias')
mobile_router.register('demandes-reparation', api_views_mobile.DemandeReparationMobileViewSet, basename='mobile-demandes')
mobile_router.register('assets', api_views_mobile.AssetMobileViewSet, basename='mobile-assets')
mobile_router.register('sync', api_views_mobile.SynchronisationMobileViewSet, basename='mobile-sync')

urlpatterns = [
    # ==============================================================================
    # API MOBILE
    # ==============================================================================
    path('api/mobile/', include(mobile_router.urls)),
    
    # ==============================================================================
    # AUTHENTIFICATION
    # ==============================================================================
    path('', views.dashboard, name='dashboard'),
    path('connexion/', views.connexion_view, name='connexion'),
    path('inscription/', views.inscription_view, name='inscription'),
    path('deconnexion/', views.deconnexion_view, name='deconnexion'),
    
    # ==============================================================================
    # TABLEAU DE BORD ADAPTÉ PAR RÔLE
    # ==============================================================================
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # ==============================================================================
    # GESTION DES INTERVENTIONS (Manager/Admin uniquement)
    # ==============================================================================
    path('interventions/', views.liste_interventions, name='liste_interventions'),
    path('interventions/creer/', views.creer_intervention, name='creer_intervention'),
    path('interventions/<int:pk>/', views.intervention_builder, name='intervention_builder'),
    path('interventions/<int:pk>/detail/', views.intervention_builder, name='intervention_detail'),  # Alias
    path('interventions/<int:pk>/supprimer/', views.supprimer_intervention, name='supprimer_intervention'),
    path('interventions/<int:pk>/preview/', views.preview_intervention, name='preview_intervention'),
    path('interventions/<int:pk>/valider/', views.valider_intervention, name='valider_intervention'),

    # ==============================================================================
    # GESTION DES ORDRES DE TRAVAIL
    # ==============================================================================
    path('ordres-travail/', views.liste_ordres_travail, name='liste_ordres_travail'),
    path('ordres-travail/creer/', views.creer_ordre_travail, name='creer_ordre_travail'),  # Manager uniquement
    path('ordres-travail/<int:pk>/', views.detail_ordre_travail, name='detail_ordre_travail'),
    path('ordres-travail/<int:pk>/modifier/', views.modifier_ordre_travail, name='modifier_ordre_travail'),
    path('ordres-travail/<int:pk>/supprimer/', views.supprimer_ordre_travail, name='supprimer_ordre_travail'),
    
    # ==============================================================================
    # EXÉCUTION DES INTERVENTIONS (Techniciens assignés)
    # ==============================================================================
    path('ordres-travail/<int:pk>/commencer/', views.commencer_intervention, name='commencer_intervention'),
    path('ordres-travail/<int:pk>/executer/', views.executer_intervention, name='executer_intervention'),
    
    # ==============================================================================
    # GESTION DES BROUILLONS D'INTERVENTION
    # ==============================================================================
    path('ordres-travail/<int:pk>/save-draft/', views.save_draft_intervention, name='save_draft_intervention'),
    path('ordres-travail/<int:pk>/load-draft/', views.load_draft_intervention, name='load_draft_intervention'),
    
    # ==============================================================================
    # NOUVELLES VUES WEB - DEMANDES DE RÉPARATION
    # ==============================================================================
    path('demandes-reparation/', views.liste_demandes_reparation, name='liste_demandes_reparation'),
    path('demandes-reparation/<int:pk>/', views.detail_demande_reparation, name='detail_demande_reparation'),
    path('demandes-reparation/creer/<int:ordre_id>/<int:point_id>/', views.creer_demande_reparation, name='creer_demande_reparation'),
    path('demandes-reparation/creer/<int:ordre_id>/<int:point_id>/<int:reponse_id>/', views.creer_demande_reparation, name='creer_demande_reparation_avec_reponse'),
    
    # ==============================================================================
    # SUPPRESSION OPÉRATIONS
    # ==============================================================================
    path('operations/<int:pk>/supprimer/', views.supprimer_operation, name='supprimer_operation'),
    path('api/supprimer-operation/<int:pk>/', views.supprimer_operation_ajax, name='supprimer_operation_ajax'),
    path('api/forcer-suppression-operation/<int:pk>/', views.forcer_suppression_operation, name='forcer_suppression_operation'),

    # ==============================================================================
    # SUPPRESSION POINTS DE CONTRÔLE
    # ==============================================================================
    path('points-controle/<int:pk>/get-data/', views.get_point_data, name='get_point_data'),
    path('points-controle/<int:pk>/supprimer/', views.supprimer_point_de_controle, name='supprimer_point_de_controle'),
    path('api/supprimer-point-controle/<int:pk>/', views.supprimer_point_de_controle_ajax, name='supprimer_point_de_controle_ajax'),
    path('api/forcer-suppression-point-controle/<int:pk>/', views.forcer_suppression_point_controle, name='forcer_suppression_point_controle'),
    path('ajax/point/<int:point_id>/details/', views.ajax_edit_point, name='ajax_details_point'),

    # ==============================================================================
    # VUES UTILITAIRES DE VÉRIFICATION
    # ==============================================================================
    path('api/verifier-suppressions/<int:intervention_id>/', views.verifier_suppressions_possibles, name='verifier_suppressions_possibles'),
    
    # ==============================================================================
    # APIs AJAX POUR LE CONSTRUCTEUR D'INTERVENTION
    # ==============================================================================
    path('ajax/operation/<int:operation_id>/edit/', views.ajax_edit_operation, name='ajax_edit_operation'),
    path('ajax/point/<int:point_id>/edit/', views.ajax_edit_point, name='ajax_edit_point'),
    path('api/reorder-operations/', views.ajax_reorder_operations, name='ajax_reorder_operations'),
    path('api/reorder-points/', views.reorder_points_controle, name='reorder_points_controle'),
    
    # ==============================================================================
    # GESTION DES MÉDIAS - VERSION CORRIGÉE UNIQUE
    # ==============================================================================
    path('ajax/upload-media/', views.upload_media_ajax, name='upload_media_ajax'),
    path('ajax/delete-media/', views.delete_media_ajax, name='delete_media_ajax'),
    
    # URLs de test pour debugging (optionnelles)
    path('ajax/upload-media-simple/', views.upload_media_simple, name='upload_media_simple'),
    path('ajax/delete-media-simple/', views.delete_media_simple, name='delete_media_simple'),
    
    # Gestion avancée des médias (existant)
    path('api/upload-media/', views.upload_media_avance, name='upload_media_avance'),
    path('api/supprimer-media/<int:media_id>/', views.supprimer_media, name='supprimer_media'),
    
    # ==============================================================================
    # SYNCHRONISATION HORS LIGNE
    # ==============================================================================
    path('ajax/sync-offline/', views.sync_offline_data, name='sync_offline_data'),
    
    # ==============================================================================
    # ASSETS ENRICHIS
    # ==============================================================================
    path('assets/<int:pk>/detail-enrichi/', views.detail_asset_enrichi, name='detail_asset_enrichi'),
    path('assets/<int:pk>/qr-code/', views.generer_qr_code_asset, name='generer_qr_code_asset'),
    
    # ==============================================================================
    # GESTION DES PROFILS UTILISATEURS
    # ==============================================================================
    path('profil/', views.profil_utilisateur, name='profil_utilisateur'),
    path('profil/mot-de-passe/', views.changer_mot_de_passe, name='changer_mot_de_passe'),
    
    # ==============================================================================
    # APIs AJAX ET UTILITAIRES
    # ==============================================================================
    path('ajax/assets-par-categorie/', views.ajax_assets_par_categorie, name='ajax_assets_par_categorie'),
    path('ajax/interventions-validees/', views.ajax_interventions_validees, name='ajax_interventions_validees'),
    
    # ==============================================================================
    # RAPPORTS ET EXPORTS
    # ==============================================================================
    path('rapports/<int:pk>/export-pdf/', views.export_rapport_pdf, name='export_rapport_pdf'),
    
    # ==============================================================================
    # APIs UTILITAIRES
    # ==============================================================================
    path('api/notifications/', views.get_notifications_utilisateur, name='get_notifications'),
    path('api/statistiques-dashboard/', views.get_statistiques_dashboard, name='statistiques_dashboard'),
    path('api/recherche-globale/', views.recherche_globale, name='recherche_globale'),
    path('save-draft/<int:ordre_id>/', views.save_draft_intervention, name='save_draft_intervention'),
    path('ordres-travail/<int:pk>/save-draft/', views.save_draft_intervention, name='save_draft_intervention'),
    path('ordres-travail/<int:pk>/load-draft/', views.load_draft_intervention, name='load_draft_intervention'),
    path('ordres-travail/<int:pk>/medias/', views.get_medias_intervention, name='get_medias_intervention'),
    path('upload-media-ajax/', views.upload_media_ajax, name='upload_media_ajax'),
    path('media/<int:media_id>/delete/', views.delete_media_ajax, name='delete_media_ajax'),

    # Dans la section GESTION DES MÉDIAS
    path('ajax/upload-media-complete/', views.upload_media_complete, name='upload_media_complete'),
    path('ajax/get-medias-point/<int:point_id>/', views.get_medias_point, name='get_medias_point'),
    path('ajax/delete-media-complete/<int:media_id>/', views.delete_media_complete, name='delete_media_complete'),

   # Carte FTTH
    # ==============================================================================
    # INTERFACE CARTOGRAPHIQUE FTTH - CORRIGÉE
    # ==============================================================================
    path('carte/', views.carte_ftth, name='carte_ftth'),
    path('api/assets/<int:asset_id>/details/', views.asset_details_ajax, name='asset_details_ajax'),
    path('api/assets/search/', views.api_assets_search, name='api_assets_search'),
   

]



# Servir les fichiers media en développement
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)