# core/api_views_mobile.py
# API REST pour l'application mobile GMAO

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, JSONParser
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.db.models import Q, F, Count, Sum
from django.utils import timezone
from datetime import timedelta
import uuid

from .models import (
    OrdreDeTravail, Intervention, Asset, RapportExecution, 
    Reponse, FichierMedia, DemandeReparation, ProfilUtilisateur
)
from .serializers_mobile import (
    OrdreDeTravailMobileSerializer, InterventionMobileSerializer,
    AssetMobileSerializer, RapportExecutionMobileSerializer,
    ReponseMobileSerializer, FichierMediaMobileSerializer,
    DemandeReparationMobileSerializer, UserMobileSerializer
)

# ==============================================================================
# AUTHENTIFICATION MOBILE
# ==============================================================================

class MobileAuthViewSet(viewsets.ViewSet):
    """
    API d'authentification pour l'application mobile
    """
    permission_classes = [permissions.AllowAny]
    
    @action(detail=False, methods=['post'])
    def login(self, request):
        """
        Connexion mobile avec génération de token
        """
        username = request.data.get('username')
        password = request.data.get('password')
        device_id = request.data.get('device_id')
        
        if not username or not password:
            return Response({
                'error': 'Username et password requis'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user = authenticate(username=username, password=password)
        
        if user and user.is_active:
            # Créer ou récupérer le token
            from rest_framework.authtoken.models import Token
            token, created = Token.objects.get_or_create(user=user)
            
            # Enregistrer les infos de l'appareil
            if device_id:
                profile, _ = ProfilUtilisateur.objects.get_or_create(user=user)
                # Vous pouvez ajouter un champ device_id au modèle ProfilUtilisateur
            
            return Response({
                'token': token.key,
                'user_id': user.id,
                'username': user.username,
                'full_name': user.get_full_name(),
                'role': getattr(user.profil, 'role', 'OPERATEUR') if hasattr(user, 'profil') else 'OPERATEUR',
                'permissions': self._get_user_permissions(user)
            })
        else:
            return Response({
                'error': 'Identifiants invalides'
            }, status=status.HTTP_401_UNAUTHORIZED)
    
    @action(detail=False, methods=['post'])
    def logout(self, request):
        """
        Déconnexion mobile
        """
        if request.user.is_authenticated:
            # Supprimer le token pour forcer une nouvelle connexion
            try:
                request.user.auth_token.delete()
            except:
                pass
        
        return Response({'message': 'Déconnecté avec succès'})
    
    @action(detail=False, methods=['get'])
    def profile(self, request):
        """
        Récupère le profil de l'utilisateur connecté
        """
        if not request.user.is_authenticated:
            return Response({
                'error': 'Non authentifié'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        return Response(UserMobileSerializer(request.user).data)
    
    def _get_user_permissions(self, user):
        """
        Retourne les permissions de l'utilisateur pour l'app mobile
        """
        try:
            role = user.profil.role
        except:
            role = 'OPERATEUR'
        
        permissions = {
            'can_create_ot': role in ['MANAGER', 'ADMIN'],
            'can_execute_ot': role in ['TECHNICIEN', 'MANAGER', 'ADMIN'],
            'can_validate_intervention': role in ['MANAGER', 'ADMIN'],
            'can_manage_reparation': role in ['MANAGER', 'ADMIN'],
            'can_view_all_ot': role in ['MANAGER', 'ADMIN'],
        }
        
        return permissions

# ==============================================================================
# API ORDRES DE TRAVAIL MOBILE
# ==============================================================================

class OrdreDeTravailMobileViewSet(viewsets.ModelViewSet):
    """
    API pour la gestion des ordres de travail sur mobile
    """
    serializer_class = OrdreDeTravailMobileSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['statut', 'priorite', 'type_OT', 'asset']
    
    def get_queryset(self):
        """
        Filtre les OT selon le rôle de l'utilisateur
        """
        user = self.request.user
        
        try:
            role = user.profil.role
        except:
            role = 'OPERATEUR'
        
        if role in ['MANAGER', 'ADMIN']:
            # Managers voient tous les OT
            return OrdreDeTravail.objects.all().select_related(
                'intervention', 'asset', 'statut', 'cree_par', 'assigne_a_technicien'
            ).order_by('-date_creation')
        else:
            # Techniciens voient leurs OT assignés
            return OrdreDeTravail.objects.filter(
                Q(assigne_a_technicien=user) | 
                Q(assigne_a_equipe__membres=user) |
                Q(cree_par=user)
            ).select_related(
                'intervention', 'asset', 'statut', 'cree_par', 'assigne_a_technicien'
            ).order_by('-date_creation')
    
    @action(detail=True, methods=['post'])
    def commencer(self, request, pk=None):
        """
        Démarre l'exécution d'un OT
        """
        ordre = self.get_object()
        
        # Vérifier les permissions
        if not self._can_execute_ot(request.user, ordre):
            return Response({
                'error': 'Vous n\'êtes pas autorisé à exécuter cet OT'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Récupérer ou créer le rapport
        rapport, created = RapportExecution.objects.get_or_create(
            ordre_de_travail=ordre,
            defaults={'cree_par': request.user}
        )
        
        # Marquer le début
        if not rapport.date_execution_debut:
            rapport.date_execution_debut = timezone.now()
            rapport.statut_rapport = 'EN_COURS'
            rapport.save()
            
            ordre.date_debut_reel = timezone.now()
            ordre.save()
        
        return Response({
            'message': 'Intervention démarrée',
            'rapport_id': rapport.id,
            'date_debut': rapport.date_execution_debut
        })
    
    @action(detail=True, methods=['post'])
    def finaliser(self, request, pk=None):
        """
        Finalise l'exécution d'un OT
        """
        ordre = self.get_object()
        
        if not self._can_execute_ot(request.user, ordre):
            return Response({
                'error': 'Permission refusée'
            }, status=status.HTTP_403_FORBIDDEN)
        
        try:
            rapport = RapportExecution.objects.get(ordre_de_travail=ordre)
        except RapportExecution.DoesNotExist:
            return Response({
                'error': 'Aucun rapport d\'exécution trouvé'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Vérifier les demandes de réparation bloquantes
        demandes_bloquantes = DemandeReparation.objects.filter(
            ordre_de_travail=ordre,
            bloque_cloture_ot=True,
            statut__in=['EN_ATTENTE', 'VALIDEE', 'EN_COURS']
        )
        
        if demandes_bloquantes.exists():
            return Response({
                'error': 'Impossible de finaliser: demandes de réparation en attente',
                'demandes_bloquantes': [d.numero_demande for d in demandes_bloquantes]
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Vérifier les points obligatoires
        points_manquants = self._check_points_obligatoires(ordre, rapport)
        
        if points_manquants:
            return Response({
                'error': 'Points obligatoires manquants',
                'points_manquants': points_manquants
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Finaliser
        rapport.statut_rapport = 'FINALISE'
        rapport.date_execution_fin = timezone.now()
        rapport.commentaire_global = request.data.get('commentaire_global', '')
        rapport.save()
        
        ordre.date_fin_reelle = timezone.now()
        # Changer le statut vers "Terminé"
        from .models import StatutWorkflow
        statut_termine = StatutWorkflow.objects.filter(nom='TERMINE').first()
        if statut_termine:
            ordre.statut = statut_termine
        ordre.save()
        
        return Response({
            'message': 'Intervention finalisée avec succès',
            'date_fin': rapport.date_execution_fin
        })
    
    @action(detail=True, methods=['get'])
    def execution_details(self, request, pk=None):
        """
        Récupère les détails pour l'exécution mobile
        """
        ordre = self.get_object()
        
        if not self._can_execute_ot(request.user, ordre):
            return Response({
                'error': 'Permission refusée'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Récupérer le rapport
        try:
            rapport = RapportExecution.objects.get(ordre_de_travail=ordre)
        except RapportExecution.DoesNotExist:
            rapport = RapportExecution.objects.create(
                ordre_de_travail=ordre,
                cree_par=request.user
            )
        
        # Préparer les données pour mobile
        operations = ordre.intervention.operations.all().order_by('ordre')
        operations_data = []
        
        for operation in operations:
            points_data = []
            for point in operation.points_de_controle.all().order_by('ordre'):
                # Récupérer la réponse existante
                try:
                    reponse = rapport.reponses.get(point_de_controle=point)
                    reponse_data = ReponseMobileSerializer(reponse).data
                except Reponse.DoesNotExist:
                    reponse_data = None
                
                point_data = {
                    'id': point.id,
                    'label': point.label,
                    'type_champ': point.type_champ,
                    'aide': point.aide,
                    'options': point.options.split(';') if point.options else [],
                    'est_obligatoire': point.est_obligatoire,
                    'permettre_photo': point.permettre_photo,
                    'permettre_audio': point.permettre_audio,
                    'permettre_video': point.permettre_video,
                    'peut_demander_reparation': getattr(point, 'peut_demander_reparation', False),
                    'types_fichiers_autorises': getattr(point, 'types_fichiers_autorises', '').split(',') if getattr(point, 'types_fichiers_autorises', '') else [],
                    'reponse': reponse_data
                }
                points_data.append(point_data)
            
            operations_data.append({
                'id': operation.id,
                'nom': operation.nom,
                'ordre': operation.ordre,
                'points_de_controle': points_data
            })
        
        return Response({
            'ordre_de_travail': OrdreDeTravailMobileSerializer(ordre).data,
            'rapport': RapportExecutionMobileSerializer(rapport).data,
            'operations': operations_data
        })
    
    @action(detail=False, methods=['get'])
    def mes_taches(self, request):
        """
        Récupère les tâches assignées à l'utilisateur connecté
        """
        user = request.user
        
        # Tâches assignées
        taches = OrdreDeTravail.objects.filter(
            Q(assigne_a_technicien=user) | 
            Q(assigne_a_equipe__membres=user)
        ).exclude(
            statut__est_statut_final=True
        ).select_related(
            'intervention', 'asset', 'statut'
        ).order_by('date_prevue_debut')
        
        # Statistiques
        stats = {
            'total': taches.count(),
            'en_retard': taches.filter(date_prevue_debut__lt=timezone.now()).count(),
            'aujourdhui': taches.filter(
                date_prevue_debut__date=timezone.now().date()
            ).count(),
            'cette_semaine': taches.filter(
                date_prevue_debut__week=timezone.now().isocalendar()[1]
            ).count()
        }
        
        return Response({
            'taches': OrdreDeTravailMobileSerializer(taches, many=True).data,
            'statistiques': stats
        })
    
    def _can_execute_ot(self, user, ordre):
        """
        Vérifie si un utilisateur peut exécuter un OT
        """
        try:
            role = user.profil.role
        except:
            role = 'OPERATEUR'
        
        return (
            ordre.assigne_a_technicien == user or
            (ordre.assigne_a_equipe and user in ordre.assigne_a_equipe.membres.all()) or
            role in ['MANAGER', 'ADMIN']
        )
    
    def _check_points_obligatoires(self, ordre, rapport):
        """
        Vérifie les points obligatoires manquants
        """
        points_manquants = []
        
        for operation in ordre.intervention.operations.all():
            for point in operation.points_de_controle.filter(est_obligatoire=True):
                if not rapport.reponses.filter(point_de_controle=point).exists():
                    points_manquants.append({
                        'operation': operation.nom,
                        'point': point.label
                    })
        
        return points_manquants

# ==============================================================================
# API RÉPONSES MOBILE
# ==============================================================================

class ReponseMobileViewSet(viewsets.ModelViewSet):
    """
    API pour la gestion des réponses sur mobile
    """
    serializer_class = ReponseMobileSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser]
    
    def get_queryset(self):
        rapport_id = self.request.query_params.get('rapport_id')
        if rapport_id:
            return Reponse.objects.filter(
                rapport_execution_id=rapport_id
            ).select_related('point_de_controle', 'saisi_par')
        return Reponse.objects.none()
    
    def create(self, request, *args, **kwargs):
        """
        Crée ou met à jour une réponse
        """
        rapport_id = request.data.get('rapport_execution')
        point_id = request.data.get('point_de_controle')
        valeur = request.data.get('valeur')
        
        if not all([rapport_id, point_id]):
            return Response({
                'error': 'rapport_execution et point_de_controle requis'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            rapport = RapportExecution.objects.get(id=rapport_id)
            point = PointDeControle.objects.get(id=point_id)
        except (RapportExecution.DoesNotExist, PointDeControle.DoesNotExist):
            return Response({
                'error': 'Rapport ou point de contrôle introuvable'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Vérifier les permissions
        if not self._can_edit_rapport(request.user, rapport):
            return Response({
                'error': 'Permission refusée'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Créer ou mettre à jour la réponse
        reponse, created = Reponse.objects.get_or_create(
            rapport_execution=rapport,
            point_de_controle=point,
            defaults={
                'valeur': valeur,
                'saisi_par': request.user
            }
        )
        
        if not created:
            reponse.valeur = valeur
            reponse.saisi_par = request.user
            reponse.date_reponse = timezone.now()
            reponse.save()
        
        return Response(
            ReponseMobileSerializer(reponse).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['post'])
    def bulk_save(self, request):
        """
        Sauvegarde en masse pour la synchronisation mobile
        """
        reponses_data = request.data.get('reponses', [])
        rapport_id = request.data.get('rapport_id')
        
        if not rapport_id:
            return Response({
                'error': 'rapport_id requis'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            rapport = RapportExecution.objects.get(id=rapport_id)
        except RapportExecution.DoesNotExist:
            return Response({
                'error': 'Rapport introuvable'
            }, status=status.HTTP_404_NOT_FOUND)
        
        if not self._can_edit_rapport(request.user, rapport):
            return Response({
                'error': 'Permission refusée'
            }, status=status.HTTP_403_FORBIDDEN)
        
        success_count = 0
        errors = []
        
        for reponse_data in reponses_data:
            try:
                point_id = reponse_data.get('point_de_controle')
                valeur = reponse_data.get('valeur')
                
                point = PointDeControle.objects.get(id=point_id)
                
                reponse, created = Reponse.objects.get_or_create(
                    rapport_execution=rapport,
                    point_de_controle=point,
                    defaults={
                        'valeur': valeur,
                        'saisi_par': request.user
                    }
                )
                
                if not created:
                    reponse.valeur = valeur
                    reponse.saisi_par = request.user
                    reponse.date_reponse = timezone.now()
                    reponse.save()
                
                success_count += 1
                
            except Exception as e:
                errors.append({
                    'point_id': reponse_data.get('point_de_controle'),
                    'error': str(e)
                })
        
        return Response({
            'success_count': success_count,
            'errors': errors,
            'message': f'{success_count} réponses sauvegardées'
        })
    
    def _can_edit_rapport(self, user, rapport):
        """
        Vérifie si un utilisateur peut modifier un rapport
        """
        ordre = rapport.ordre_de_travail
        
        try:
            role = user.profil.role
        except:
            role = 'OPERATEUR'
        
        return (
            ordre.assigne_a_technicien == user or
            (ordre.assigne_a_equipe and user in ordre.assigne_a_equipe.membres.all()) or
            role in ['MANAGER', 'ADMIN']
        )

# ==============================================================================
# API MÉDIAS MOBILE
# ==============================================================================

class FichierMediaMobileViewSet(viewsets.ModelViewSet):
    """
    API pour la gestion des médias sur mobile
    """
    serializer_class = FichierMediaMobileSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, JSONParser]
    
    def get_queryset(self):
        reponse_id = self.request.query_params.get('reponse_id')
        if reponse_id:
            return FichierMedia.objects.filter(reponse_id=reponse_id)
        return FichierMedia.objects.none()
    
    def create(self, request, *args, **kwargs):
        """
        Upload de média mobile avec validation
        """
        reponse_id = request.data.get('reponse_id')
        fichier = request.FILES.get('fichier')
        type_fichier = request.data.get('type_fichier', 'PHOTO')
        
        if not reponse_id or not fichier:
            return Response({
                'error': 'reponse_id et fichier requis'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            reponse = Reponse.objects.get(id=reponse_id)
        except Reponse.DoesNotExist:
            return Response({
                'error': 'Réponse introuvable'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Vérifier les permissions
        if not self._can_edit_rapport(request.user, reponse.rapport_execution):
            return Response({
                'error': 'Permission refusée'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Validation du type de fichier
        point = reponse.point_de_controle
        if not self._validate_file_type(fichier, point, type_fichier):
            return Response({
                'error': 'Type de fichier non autorisé'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validation de la taille
        max_size = getattr(point, 'taille_max_fichier_mb', 10) * 1024 * 1024
        if fichier.size > max_size:
            return Response({
                'error': f'Fichier trop volumineux. Maximum: {max_size // (1024*1024)}MB'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Créer le fichier média
        fichier_media = FichierMedia.objects.create(
            reponse=reponse,
            type_fichier=type_fichier,
            fichier=fichier,
            nom_original=fichier.name,
            taille_octets=fichier.size
        )
        
        return Response(
            FichierMediaMobileSerializer(fichier_media).data,
            status=status.HTTP_201_CREATED
        )
    
    def _validate_file_type(self, fichier, point, type_fichier):
        """
        Valide le type de fichier selon les permissions du point
        """
        file_ext = fichier.name.split('.')[-1].upper() if '.' in fichier.name else ''
        
        # Vérifier les autorisations de média
        if type_fichier == 'PHOTO' and not point.permettre_photo:
            return False
        elif type_fichier == 'AUDIO' and not point.permettre_audio:
            return False
        elif type_fichier == 'VIDEO' and not point.permettre_video:
            return False
        
        # Vérifier les types de fichiers autorisés
        if hasattr(point, 'types_fichiers_autorises') and point.types_fichiers_autorises:
            types_autorises = [t.strip().upper() for t in point.types_fichiers_autorises.split(',')]
            if file_ext not in types_autorises:
                return False
        
        return True
    
    def _can_edit_rapport(self, user, rapport):
        """
        Vérifie si un utilisateur peut modifier un rapport
        """
        ordre = rapport.ordre_de_travail
        
        try:
            role = user.profil.role
        except:
            role = 'OPERATEUR'
        
        return (
            ordre.assigne_a_technicien == user or
            (ordre.assigne_a_equipe and user in ordre.assigne_a_equipe.membres.all()) or
            role in ['MANAGER', 'ADMIN']
        )

# ==============================================================================
# API DEMANDES DE RÉPARATION MOBILE
# ==============================================================================

class DemandeReparationMobileViewSet(viewsets.ModelViewSet):
    """
    API pour les demandes de réparation sur mobile
    """
    serializer_class = DemandeReparationMobileSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['statut', 'priorite', 'assignee_a']
    
    def get_queryset(self):
        user = self.request.user
        
        try:
            role = user.profil.role
        except:
            role = 'OPERATEUR'
        
        if role in ['MANAGER', 'ADMIN']:
            return DemandeReparation.objects.all().select_related(
                'ordre_de_travail', 'point_de_controle', 'cree_par', 'assignee_a'
            ).order_by('-date_creation')
        else:
            return DemandeReparation.objects.filter(
                Q(cree_par=user) | Q(assignee_a=user)
            ).select_related(
                'ordre_de_travail', 'point_de_controle', 'cree_par', 'assignee_a'
            ).order_by('-date_creation')
    
    def create(self, request, *args, **kwargs):
        """
        Crée une demande de réparation depuis mobile
        """
        ordre_id = request.data.get('ordre_de_travail')
        point_id = request.data.get('point_de_controle')
        reponse_id = request.data.get('reponse_origine')
        
        try:
            ordre = OrdreDeTravail.objects.get(id=ordre_id)
            point = PointDeControle.objects.get(id=point_id)
            reponse = Reponse.objects.get(id=reponse_id) if reponse_id else None
        except (OrdreDeTravail.DoesNotExist, PointDeControle.DoesNotExist, Reponse.DoesNotExist):
            return Response({
                'error': 'Ordre de travail, point de contrôle ou réponse introuvable'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Vérifier que le point autorise les demandes de réparation
        if not getattr(point, 'peut_demander_reparation', False):
            return Response({
                'error': 'Ce point de contrôle n\'autorise pas les demandes de réparation'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Vérifier les permissions
        if not self._can_create_demande(request.user, ordre):
            return Response({
                'error': 'Permission refusée'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Créer la demande
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            demande = serializer.save(
                ordre_de_travail=ordre,
                point_de_controle=point,
                reponse_origine=reponse,
                cree_par=request.user
            )
            
            return Response(
                DemandeReparationMobileSerializer(demande).data,
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def commencer_reparation(self, request, pk=None):
        """
        Démarre une réparation
        """
        demande = self.get_object()
        
        if demande.statut != 'VALIDEE':
            return Response({
                'error': 'La demande doit être validée pour commencer'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            role = request.user.profil.role
        except:
            role = 'OPERATEUR'
        
        if demande.assignee_a != request.user and role not in ['MANAGER', 'ADMIN']:
            return Response({
                'error': 'Vous n\'êtes pas assigné à cette réparation'
            }, status=status.HTTP_403_FORBIDDEN)
        
        demande.statut = 'EN_COURS'
        demande.date_debut_reparation = timezone.now()
        demande.save()
        
        return Response({
            'message': 'Réparation démarrée',
            'date_debut': demande.date_debut_reparation
        })
    
    @action(detail=True, methods=['post'])
    def terminer_reparation(self, request, pk=None):
        """
        Termine une réparation
        """
        demande = self.get_object()
        
        if demande.statut != 'EN_COURS':
            return Response({
                'error': 'La réparation doit être en cours'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            role = request.user.profil.role
        except:
            role = 'OPERATEUR'
        
        if demande.assignee_a != request.user and role not in ['MANAGER', 'ADMIN']:
            return Response({
                'error': 'Permission refusée'
            }, status=status.HTTP_403_FORBIDDEN)
        
        demande.statut = 'TERMINEE'
        demande.date_fin_reparation = timezone.now()
        demande.cout_reel = request.data.get('cout_reel', 0)
        demande.commentaire_resolution = request.data.get('commentaire_resolution', '')
        demande.save()
        
        return Response({
            'message': 'Réparation terminée',
            'date_fin': demande.date_fin_reparation
        })
    
    def _can_create_demande(self, user, ordre):
        """
        Vérifie si un utilisateur peut créer une demande de réparation
        """
        try:
            role = user.profil.role
        except:
            role = 'OPERATEUR'
        
        return (
            ordre.assigne_a_technicien == user or
            (ordre.assigne_a_equipe and user in ordre.assigne_a_equipe.membres.all()) or
            role in ['MANAGER', 'ADMIN']
        )

# ==============================================================================
# API SYNCHRONISATION MOBILE
# ==============================================================================

class SynchronisationMobileViewSet(viewsets.ViewSet):
    """
    API pour la synchronisation offline/online mobile
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def donnees_initiales(self, request):
        """
        Récupère toutes les données nécessaires pour le mode offline
        """
        user = request.user
        
        # OT assignés à l'utilisateur
        mes_ot = OrdreDeTravail.objects.filter(
            Q(assigne_a_technicien=user) | 
            Q(assigne_a_equipe__membres=user)
        ).exclude(
            statut__est_statut_final=True
        ).select_related('intervention', 'asset', 'statut')
        
        # Interventions associées
        interventions = Intervention.objects.filter(
            ordredetravail__in=mes_ot
        ).distinct().prefetch_related('operations__points_de_controle')
        
        # Assets associés
        assets = Asset.objects.filter(
            ordredetravail__in=mes_ot
        ).distinct()
        
        # Demandes de réparation
        demandes = DemandeReparation.objects.filter(
            Q(cree_par=user) | Q(assignee_a=user)
        ).select_related('ordre_de_travail', 'point_de_controle')
        
        return Response({
            'timestamp': timezone.now().isoformat(),
            'ordres_travail': OrdreDeTravailMobileSerializer(mes_ot, many=True).data,
            'interventions': InterventionMobileSerializer(interventions, many=True).data,
            'assets': AssetMobileSerializer(assets, many=True).data,
            'demandes_reparation': DemandeReparationMobileSerializer(demandes, many=True).data,
            'user_profile': UserMobileSerializer(user).data
        })
    
    @action(detail=False, methods=['post'])
    def synchroniser_modifications(self, request):
        """
        Synchronise les modifications faites en mode offline
        """
        modifications = request.data.get('modifications', [])
        resultats = []
        
        for modif in modifications:
            try:
                resultat = self._traiter_modification(modif, request.user)
                resultats.append({
                    'id_local': modif.get('id_local'),
                    'success': True,
                    'data': resultat
                })
            except Exception as e:
                resultats.append({
                    'id_local': modif.get('id_local'),
                    'success': False,
                    'error': str(e)
                })
        
        return Response({
            'resultats': resultats,
            'timestamp': timezone.now().isoformat()
        })
    
    def _traiter_modification(self, modif, user):
        """
        Traite une modification offline
        """
        type_objet = modif.get('type')
        action = modif.get('action')
        data = modif.get('data')
        
        if type_objet == 'reponse' and action == 'create_or_update':
            return self._sync_reponse(data, user)
        elif type_objet == 'media' and action == 'create':
            return self._sync_media(data, user)
        elif type_objet == 'demande_reparation' and action == 'create':
            return self._sync_demande_reparation(data, user)
        else:
            raise ValueError(f"Type de modification non supporté: {type_objet}/{action}")
    
    def _sync_reponse(self, data, user):
        """
        Synchronise une réponse
        """
        rapport_id = data.get('rapport_execution')
        point_id = data.get('point_de_controle')
        valeur = data.get('valeur')
        
        rapport = RapportExecution.objects.get(id=rapport_id)
        point = PointDeControle.objects.get(id=point_id)
        
        reponse, created = Reponse.objects.get_or_create(
            rapport_execution=rapport,
            point_de_controle=point,
            defaults={
                'valeur': valeur,
                'saisi_par': user
            }
        )
        
        if not created:
            reponse.valeur = valeur
            reponse.saisi_par = user
            reponse.date_reponse = timezone.now()
            reponse.save()
        
        return ReponseMobileSerializer(reponse).data
    
    def _sync_media(self, data, user):
        """
        Synchronise un média (placeholder - nécessite traitement spécial pour les fichiers)
        """
        # TODO: Implémenter la synchronisation des médias
        # Nécessite une approche spéciale pour les fichiers binaires
        pass
    
    def _sync_demande_reparation(self, data, user):
        """
        Synchronise une demande de réparation
        """
        ordre_id = data.get('ordre_de_travail')
        point_id = data.get('point_de_controle')
        
        ordre = OrdreDeTravail.objects.get(id=ordre_id)
        point = PointDeControle.objects.get(id=point_id)
        
        demande = DemandeReparation.objects.create(
            ordre_de_travail=ordre,
            point_de_controle=point,
            titre=data.get('titre'),
            description=data.get('description'),
            priorite=data.get('priorite', 2),
            cree_par=user
        )
        
        return DemandeReparationMobileSerializer(demande).data

# ==============================================================================
# API ASSETS MOBILE
# ==============================================================================

class AssetMobileViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API lecture seule pour les assets sur mobile
    """
    serializer_class = AssetMobileSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['statut', 'criticite', 'categorie']
    
    def get_queryset(self):
        return Asset.objects.all().select_related('categorie')
    
    @action(detail=True, methods=['get'])
    def qr_scan(self, request, pk=None):
        """
        Récupère les infos d'un asset scanné via QR code
        """
        asset = self.get_object()
        
        # OT en cours sur cet asset
        ot_en_cours = OrdreDeTravail.objects.filter(
            asset=asset,
            statut__est_statut_final=False
        ).select_related('intervention', 'statut', 'assigne_a_technicien')
        
        # Dernière maintenance
        derniere_maintenance = OrdreDeTravail.objects.filter(
            asset=asset,
            statut__est_statut_final=True
        ).order_by('-date_fin_reelle').first()
        
        return Response({
            'asset': AssetMobileSerializer(asset).data,
            'ordres_travail_actifs': OrdreDeTravailMobileSerializer(ot_en_cours, many=True).data,
            'derniere_maintenance': OrdreDeTravailMobileSerializer(derniere_maintenance).data if derniere_maintenance else None,
            'peut_creer_ot': self._peut_creer_ot(request.user)
        })
    
    def _peut_creer_ot(self, user):
        """
        Vérifie si l'utilisateur peut créer des OT
        """
        try:
            role = user.profil.role
        except:
            role = 'OPERATEUR'
        
        return role in ['MANAGER', 'ADMIN']