# core/middleware.py

import json
import time
from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from django.core.cache import cache
from django.conf import settings

class MobileAPIMiddleware(MiddlewareMixin):
    """
    Middleware pour l'API mobile avec gestion de rate limiting et logging
    """
    
    def process_request(self, request):
        # Marquer le début de la requête pour les métriques
        request.start_time = time.time()
        
        # Vérifier si c'est une requête API mobile
        if request.path.startswith('/api/mobile/'):
            request.is_mobile_api = True
            
            # Rate limiting pour l'API mobile
            if hasattr(request, 'user') and request.user.is_authenticated:
                cache_key = f"mobile_api_rate_limit_{request.user.id}"
                requests_count = cache.get(cache_key, 0)
                
                if requests_count > 1000:  # 1000 requêtes par heure
                    return JsonResponse({
                        'error': 'Rate limit exceeded',
                        'retry_after': 3600
                    }, status=429)
                
                cache.set(cache_key, requests_count + 1, 3600)
        
        return None
    
    def process_response(self, request, response):
        # Ajouter des headers pour l'API mobile
        if getattr(request, 'is_mobile_api', False):
            response['X-API-Version'] = settings.GMAO_SETTINGS.get('MOBILE_API_VERSION', '1.0')
            response['X-Response-Time'] = f"{time.time() - request.start_time:.3f}s"
            
            # CORS spécifique pour mobile
            response['Access-Control-Allow-Origin'] = '*'
            response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
        
        return response

class OfflineSyncMiddleware(MiddlewareMixin):
    """
    Middleware pour gérer la synchronisation offline
    """
    
    def process_request(self, request):
        # Détecter les requêtes de synchronisation offline
        if request.META.get('HTTP_X_OFFLINE_SYNC') == 'true':
            request.is_offline_sync = True
            
            # Valider le timestamp de la requête
            timestamp = request.META.get('HTTP_X_SYNC_TIMESTAMP')
            if timestamp:
                try:
                    sync_time = float(timestamp)
                    current_time = time.time()
                    
                    # Rejeter les requêtes trop anciennes (plus de 7 jours)
                    if current_time - sync_time > 7 * 24 * 3600:
                        return JsonResponse({
                            'error': 'Sync request too old',
                            'max_age_days': 7
                        }, status=400)
                except ValueError:
                    pass
        
        return None

# ==============================================================================
# TÂCHES CELERY POUR LE TRAITEMENT ASYNCHRONE
# ==============================================================================

# core/tasks.py

from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .models import OrdreDeTravail, DemandeReparation, Asset, Notification

@shared_task
def generer_notifications_automatiques():
    """
    Génère des notifications automatiques pour les événements importants
    """
    now = timezone.now()
    
    # Notifications pour les OT en retard
    ots_en_retard = OrdreDeTravail.objects.filter(
        date_prevue_debut__lt=now - timedelta(hours=1),
        statut__est_statut_final=False
    )
    
    for ot in ots_en_retard:
        if ot.assigne_a_technicien:
            Notification.objects.get_or_create(
                utilisateur=ot.assigne_a_technicien,
                titre=f"OT en retard: {ot.titre}",
                message=f"L'ordre de travail {ot.titre} était prévu pour {ot.date_prevue_debut.strftime('%d/%m/%Y %H:%M')}",
                type_notification='ALERTE',
                defaults={'lue': False}
            )
    
    # Notifications pour les demandes de réparation en attente
    demandes_en_attente = DemandeReparation.objects.filter(
        statut='EN_ATTENTE',
        date_creation__lt=now - timedelta(hours=24)
    )
    
    for demande in demandes_en_attente:
        # Notifier les managers
        from django.contrib.auth.models import User
        managers = User.objects.filter(profil__role__in=['MANAGER', 'ADMIN'], is_active=True)
        
        for manager in managers:
            Notification.objects.get_or_create(
                utilisateur=manager,
                titre=f"Demande de réparation en attente: {demande.numero_demande}",
                message=f"La demande {demande.numero_demande} attend validation depuis 24h",
                type_notification='ALERTE',
                defaults={'lue': False}
            )
    
    return f"Généré des notifications pour {ots_en_retard.count()} OT en retard et {demandes_en_attente.count()} demandes en attente"

@shared_task
def nettoyer_anciennes_notifications():
    """
    Supprime les anciennes notifications
    """
    retention_days = settings.GMAO_SETTINGS.get('NOTIFICATION_RETENTION_DAYS', 30)
    date_limite = timezone.now() - timedelta(days=retention_days)
    
    count = Notification.objects.filter(date_creation__lt=date_limite).delete()[0]
    return f"Supprimé {count} anciennes notifications"

@shared_task
def compresser_medias():
    """
    Compresse les médias volumineux en arrière-plan
    """
    from .models import FichierMedia
    from PIL import Image
    import os
    
    if not settings.MEDIA_COMPRESSION.get('ENABLE_IMAGE_COMPRESSION', False):
        return "Compression désactivée"
    
    # Traiter les images non compressées
    images_a_compresser = FichierMedia.objects.filter(
        type_fichier='PHOTO',
        taille_octets__gt=1024*1024,  # Plus de 1MB
    ).exclude(
        nom_original__contains='_compressed'
    )[:10]  # Traiter 10 images par batch
    
    compressed_count = 0
    
    for media in images_a_compresser:
        try:
            if media.fichier and os.path.exists(media.fichier.path):
                # Ouvrir et compresser l'image
                with Image.open(media.fichier.path) as img:
                    # Redimensionner si nécessaire
                    max_size = settings.MEDIA_COMPRESSION.get('MAX_IMAGE_RESOLUTION', (1920, 1080))
                    if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                        img.thumbnail(max_size, Image.Resampling.LANCZOS)
                    
                    # Sauvegarder avec compression
                    quality = settings.MEDIA_COMPRESSION.get('IMAGE_QUALITY', 85)
                    img.save(media.fichier.path, optimize=True, quality=quality)
                    
                    # Mettre à jour la taille
                    media.taille_octets = os.path.getsize(media.fichier.path)
                    media.nom_original = f"{media.nom_original}_compressed"
                    media.save()
                    
                    compressed_count += 1
        except Exception as e:
            print(f"Erreur compression {media.id}: {e}")
    
    return f"Compressé {compressed_count} images"

@shared_task
def synchroniser_donnees_iot():
    """
    Synchronise les données des capteurs IoT avec les assets
    """
    # Placeholder pour l'intégration IoT future
    # Ici vous pourriez intégrer des APIs de capteurs
    # pour mettre à jour automatiquement le statut des assets
    
    assets_avec_capteurs = Asset.objects.exclude(
        attributs_perso__cle='iot_sensor_id'
    )
    
    # Simulation de mise à jour de statut basée sur des données IoT
    updates_count = 0
    
    for asset in assets_avec_capteurs[:5]:  # Traiter 5 assets par batch
        # Simulation d'une vérification IoT
        # En réalité, vous feriez un appel API vers vos capteurs
        
        # Exemple: si température > seuil, marquer comme nécessitant maintenance
        # if sensor_data['temperature'] > asset.seuil_temperature:
        #     asset.prochaine_maintenance = timezone.now() + timedelta(days=7)
        #     asset.save()
        #     updates_count += 1
        
        pass
    
    return f"Synchronisé {updates_count} assets avec données IoT"