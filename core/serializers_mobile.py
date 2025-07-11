# core/serializers_mobile.py
# Serializers pour l'API mobile GMAO

from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    OrdreDeTravail, Intervention, Operation, PointDeControle,
    Asset, RapportExecution, Reponse, FichierMedia, 
    DemandeReparation, ProfilUtilisateur, StatutWorkflow
)

# ==============================================================================
# SERIALIZERS DE BASE
# ==============================================================================

class UserMobileSerializer(serializers.ModelSerializer):
    """
    Serializer pour les informations utilisateur mobile
    """
    role = serializers.CharField(source='profil.role', read_only=True)
    telephone = serializers.CharField(source='profil.telephone', read_only=True)
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 
            'full_name', 'role', 'telephone', 'is_active'
        ]
        read_only_fields = ['id', 'username']

class StatutWorkflowMobileSerializer(serializers.ModelSerializer):
    """
    Serializer pour les statuts de workflow
    """
    class Meta:
        model = StatutWorkflow
        fields = ['id', 'nom', 'description', 'couleur_html', 'est_statut_final']

# ==============================================================================
# SERIALIZERS ASSETS
# ==============================================================================

class AssetMobileSerializer(serializers.ModelSerializer):
    """
    Serializer pour les assets sur mobile
    """
    categorie_nom = serializers.CharField(source='categorie.nom', read_only=True)
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    criticite_display = serializers.CharField(source='get_criticite_display', read_only=True)
    qr_code_data = serializers.CharField(source='qr_code_identifier', read_only=True)
    
    # Localisation
    position = serializers.SerializerMethodField()
    
    # Informations de maintenance
    derniere_maintenance_date = serializers.DateTimeField(source='derniere_maintenance', read_only=True)
    prochaine_maintenance_date = serializers.DateTimeField(source='prochaine_maintenance', read_only=True)
    
    class Meta:
        model = Asset
        fields = [
            'id', 'nom', 'reference', 'categorie', 'categorie_nom',
            'marque', 'modele', 'statut', 'statut_display',
            'criticite', 'criticite_display', 'localisation_texte',
            'latitude', 'longitude', 'position', 'qr_code_data',
            'photo_principale', 'date_mise_en_service', 'fin_garantie',
            'derniere_maintenance_date', 'prochaine_maintenance_date'
        ]
    
    def get_position(self, obj):
        """
        Retourne la position GPS si disponible
        """
        if obj.latitude and obj.longitude:
            return {
                'latitude': float(obj.latitude),
                'longitude': float(obj.longitude)
            }
        return None

# ==============================================================================
# SERIALIZERS INTERVENTIONS
# ==============================================================================

class PointDeControleMobileSerializer(serializers.ModelSerializer):
    """
    Serializer pour les points de contrôle mobile
    """
    type_champ_display = serializers.CharField(source='get_type_champ_display', read_only=True)
    options_list = serializers.SerializerMethodField()
    types_fichiers_list = serializers.SerializerMethodField()
    
    # Nouvelles fonctionnalités
    peut_demander_reparation = serializers.BooleanField(default=False)
    types_fichiers_autorises = serializers.CharField(allow_blank=True, default='')
    taille_max_fichier_mb = serializers.IntegerField(default=10)
    
    class Meta:
        model = PointDeControle
        fields = [
            'id', 'label', 'type_champ', 'type_champ_display',
            'aide', 'options', 'options_list', 'est_obligatoire',
            'ordre', 'permettre_photo', 'permettre_audio', 'permettre_video',
            'peut_demander_reparation', 'types_fichiers_autorises', 
            'types_fichiers_list', 'taille_max_fichier_mb'
        ]
    
    def get_options_list(self, obj):
        """
        Retourne les options sous forme de liste
        """
        if obj.options:
            return [opt.strip() for opt in obj.options.split(';') if opt.strip()]
        return []
    
    def get_types_fichiers_list(self, obj):
        """
        Retourne les types de fichiers autorisés sous forme de liste
        """
        types_str = getattr(obj, 'types_fichiers_autorises', '')
        if types_str:
            return [t.strip().upper() for t in types_str.split(',') if t.strip()]
        return []

class OperationMobileSerializer(serializers.ModelSerializer):
    """
    Serializer pour les opérations mobile
    """
    points_de_controle = PointDeControleMobileSerializer(many=True, read_only=True)
    
    class Meta:
        model = Operation
        fields = ['id', 'nom', 'ordre', 'points_de_controle']

class InterventionMobileSerializer(serializers.ModelSerializer):
    """
    Serializer pour les interventions mobile
    """
    operations = OperationMobileSerializer(many=True, read_only=True)
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    
    # Statistiques
    nb_operations = serializers.SerializerMethodField()
    nb_points_controle = serializers.SerializerMethodField()
    
    class Meta:
        model = Intervention
        fields = [
            'id', 'nom', 'description', 'statut', 'statut_display',
            'duree_estimee_heures', 'techniciens_requis',
            'nb_operations', 'nb_points_controle', 'operations'
        ]
    
    def get_nb_operations(self, obj):
        """
        Nombre d'opérations dans l'intervention
        """
        return obj.operations.count()
    
    def get_nb_points_controle(self, obj):
        """
        Nombre total de points de contrôle
        """
        return sum(op.points_de_controle.count() for op in obj.operations.all())

# ==============================================================================
# SERIALIZERS ORDRES DE TRAVAIL
# ==============================================================================

class OrdreDeTravailMobileSerializer(serializers.ModelSerializer):
    """
    Serializer pour les ordres de travail mobile
    """
    # Relations
    intervention = InterventionMobileSerializer(read_only=True)
    asset = AssetMobileSerializer(read_only=True)
    statut = StatutWorkflowMobileSerializer(read_only=True)
    
    # Utilisateurs
    cree_par_nom = serializers.CharField(source='cree_par.get_full_name', read_only=True)
    assigne_a_nom = serializers.CharField(source='assigne_a_technicien.get_full_name', read_only=True)
    equipe_nom = serializers.CharField(source='assigne_a_equipe.nom', read_only=True)
    
    # Affichage
    type_ot_display = serializers.CharField(source='get_type_OT_display', read_only=True)
    priorite_display = serializers.CharField(source='get_priorite_display', read_only=True)
    
    # Calculs
    duree_reelle = serializers.SerializerMethodField()
    est_en_retard = serializers.SerializerMethodField()
    peut_etre_execute = serializers.SerializerMethodField()
    progression = serializers.SerializerMethodField()
    
    # Demandes de réparation
    nb_demandes_reparation = serializers.SerializerMethodField()
    demandes_bloquantes = serializers.SerializerMethodField()
    
    class Meta:
        model = OrdreDeTravail
        fields = [
            'id', 'titre', 'type_OT', 'type_ot_display', 'priorite', 'priorite_display',
            'date_creation', 'date_prevue_debut', 'date_debut_reel', 'date_fin_reelle',
            'cout_main_oeuvre_reel', 'cout_pieces_reel',
            'intervention', 'asset', 'statut',
            'cree_par_nom', 'assigne_a_nom', 'equipe_nom',
            'duree_reelle', 'est_en_retard', 'peut_etre_execute', 'progression',
            'nb_demandes_reparation', 'demandes_bloquantes'
        ]
    
    def get_duree_reelle(self, obj):
        """
        Calcule la durée réelle de l'intervention
        """
        if obj.date_debut_reel and obj.date_fin_reelle:
            delta = obj.date_fin_reelle - obj.date_debut_reel
            return int(delta.total_seconds() / 3600)  # en heures
        return None
    
    def get_est_en_retard(self, obj):
        """
        Vérifie si l'OT est en retard
        """
        from django.utils import timezone
        if not obj.statut or not obj.statut.est_statut_final:
            return obj.date_prevue_debut < timezone.now()
        return False
    
    def get_peut_etre_execute(self, obj):
        """
        Vérifie si l'OT peut être exécuté par l'utilisateur courant
        """
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        
        user = request.user
        try:
            role = user.profil.role
        except:
            role = 'OPERATEUR'
        
        return (
            obj.assigne_a_technicien == user or
            (obj.assigne_a_equipe and user in obj.assigne_a_equipe.membres.all()) or
            role in ['MANAGER', 'ADMIN']
        )
    
    def get_progression(self, obj):
        """
        Calcule la progression de l'exécution
        """
        try:
            rapport = obj.rapport
            if not rapport:
                return 0
            
            # Calculer le pourcentage de points de contrôle remplis
            total_points = 0
            points_remplis = 0
            
            for operation in obj.intervention.operations.all():
                for point in operation.points_de_controle.all():
                    total_points += 1
                    if rapport.reponses.filter(point_de_controle=point).exists():
                        points_remplis += 1
            
            if total_points > 0:
                return round((points_remplis / total_points) * 100)
            return 0
            
        except:
            return 0
    
    def get_nb_demandes_reparation(self, obj):
        """
        Nombre de demandes de réparation
        """
        return obj.demandes_reparation.count()
    
    def get_demandes_bloquantes(self, obj):
        """
        Demandes de réparation qui bloquent la clôture
        """
        demandes = obj.demandes_reparation.filter(
            bloque_cloture_ot=True,
            statut__in=['EN_ATTENTE', 'VALIDEE', 'EN_COURS']
        )
        return demandes.count()

# ==============================================================================
# SERIALIZERS EXÉCUTION
# ==============================================================================

class FichierMediaMobileSerializer(serializers.ModelSerializer):
    """
    Serializer pour les fichiers média mobile
    """
    type_fichier_display = serializers.CharField(source='get_type_fichier_display', read_only=True)
    taille_mb = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()
    
    class Meta:
        model = FichierMedia
        fields = [
            'id', 'type_fichier', 'type_fichier_display', 'nom_original',
            'taille_octets', 'taille_mb', 'date_upload', 'url'
        ]
    
    def get_taille_mb(self, obj):
        """
        Taille en MB
        """
        return round(obj.taille_octets / (1024 * 1024), 2)
    
    def get_url(self, obj):
        """
        URL du fichier
        """
        request = self.context.get('request')
        if obj.fichier and request:
            return request.build_absolute_uri(obj.fichier.url)
        return None

class ReponseMobileSerializer(serializers.ModelSerializer):
    """
    Serializer pour les réponses mobile
    """
    point_de_controle = PointDeControleMobileSerializer(read_only=True)
    fichiers_media = FichierMediaMobileSerializer(many=True, read_only=True)
    saisi_par_nom = serializers.CharField(source='saisi_par.get_full_name', read_only=True)
    
    # Champs pour la création/modification
    rapport_execution_id = serializers.IntegerField(write_only=True, required=False)
    point_de_controle_id = serializers.IntegerField(write_only=True, required=False)
    
    class Meta:
        model = Reponse
        fields = [
            'id', 'valeur', 'date_reponse', 'point_de_controle', 
            'fichiers_media', 'saisi_par_nom',
            'rapport_execution_id', 'point_de_controle_id'
        ]
    
    def create(self, validated_data):
        """
        Création avec gestion des IDs
        """
        rapport_id = validated_data.pop('rapport_execution_id', None)
        point_id = validated_data.pop('point_de_controle_id', None)
        
        if rapport_id:
            validated_data['rapport_execution_id'] = rapport_id
        if point_id:
            validated_data['point_de_controle_id'] = point_id
        
        return super().create(validated_data)

class RapportExecutionMobileSerializer(serializers.ModelSerializer):
    """
    Serializer pour les rapports d'exécution mobile
    """
    reponses = ReponseMobileSerializer(many=True, read_only=True)
    statut_display = serializers.CharField(source='get_statut_rapport_display', read_only=True)
    cree_par_nom = serializers.CharField(source='cree_par.get_full_name', read_only=True)
    
    # Statistiques
    nb_reponses = serializers.SerializerMethodField()
    nb_medias = serializers.SerializerMethodField()
    duree_execution = serializers.SerializerMethodField()
    
    class Meta:
        model = RapportExecution
        fields = [
            'id', 'statut_rapport', 'statut_display', 'date_creation',
            'date_derniere_maj', 'date_execution_debut', 'date_execution_fin',
            'commentaire_global', 'cree_par_nom',
            'nb_reponses', 'nb_medias', 'duree_execution', 'reponses'
        ]
    
    def get_nb_reponses(self, obj):
        """
        Nombre de réponses saisies
        """
        return obj.reponses.count()
    
    def get_nb_medias(self, obj):
        """
        Nombre de médias attachés
        """
        return FichierMedia.objects.filter(reponse__rapport_execution=obj).count()
    
    def get_duree_execution(self, obj):
        """
        Durée d'exécution en minutes
        """
        if obj.date_execution_debut and obj.date_execution_fin:
            delta = obj.date_execution_fin - obj.date_execution_debut
            return int(delta.total_seconds() / 60)
        return None

# ==============================================================================
# SERIALIZERS DEMANDES DE RÉPARATION
# ==============================================================================

class DemandeReparationMobileSerializer(serializers.ModelSerializer):
    """
    Serializer pour les demandes de réparation mobile
    """
    # Relations
    ordre_de_travail = OrdreDeTravailMobileSerializer(read_only=True)
    point_de_controle = PointDeControleMobileSerializer(read_only=True)
    
    # Utilisateurs
    cree_par_nom = serializers.CharField(source='cree_par.get_full_name', read_only=True)
    validee_par_nom = serializers.CharField(source='validee_par.get_full_name', read_only=True)
    assignee_a_nom = serializers.CharField(source='assignee_a.get_full_name', read_only=True)
    
    # Affichage
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    priorite_display = serializers.CharField(source='get_priorite_display', read_only=True)
    
    # Calculs
    duree_reparation = serializers.SerializerMethodField()
    est_en_retard = serializers.SerializerMethodField()
    peut_etre_commencee = serializers.SerializerMethodField()
    
    # Champs pour création
    ordre_de_travail_id = serializers.IntegerField(write_only=True, required=False)
    point_de_controle_id = serializers.IntegerField(write_only=True, required=False)
    reponse_origine_id = serializers.IntegerField(write_only=True, required=False)
    
    class Meta:
        model = DemandeReparation
        fields = [
            'id', 'numero_demande', 'titre', 'description', 'priorite', 'priorite_display',
            'statut', 'statut_display', 'date_creation', 'date_validation',
            'date_echeance_souhaitee', 'date_debut_reparation', 'date_fin_reparation',
            'cout_estime', 'cout_reel', 'commentaire_technicien', 'commentaire_manager',
            'commentaire_resolution', 'bloque_cloture_ot',
            'ordre_de_travail', 'point_de_controle',
            'cree_par_nom', 'validee_par_nom', 'assignee_a_nom',
            'duree_reparation', 'est_en_retard', 'peut_etre_commencee',
            'ordre_de_travail_id', 'point_de_controle_id', 'reponse_origine_id'
        ]
    
    def get_duree_reparation(self, obj):
        """
        Durée de la réparation en heures
        """
        if obj.date_debut_reparation and obj.date_fin_reparation:
            delta = obj.date_fin_reparation - obj.date_debut_reparation
            return round(delta.total_seconds() / 3600, 2)
        return None
    
    def get_est_en_retard(self, obj):
        """
        Vérifie si la demande est en retard
        """
        return obj.est_en_retard
    
    def get_peut_etre_commencee(self, obj):
        """
        Vérifie si la réparation peut être commencée
        """
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        
        user = request.user
        try:
            role = user.profil.role
        except:
            role = 'OPERATEUR'
        
        return (
            obj.statut == 'VALIDEE' and
            (obj.assignee_a == user or role in ['MANAGER', 'ADMIN'])
        )

# ==============================================================================
# SERIALIZERS SIMPLIFIÉS POUR SYNCHRONISATION
# ==============================================================================

class OrdreDeTravailSyncSerializer(serializers.ModelSerializer):
    """
    Serializer simplifié pour la synchronisation offline
    """
    intervention_id = serializers.IntegerField(source='intervention.id')
    asset_id = serializers.IntegerField(source='asset.id')
    statut_nom = serializers.CharField(source='statut.nom', allow_null=True)
    
    class Meta:
        model = OrdreDeTravail
        fields = [
            'id', 'titre', 'type_OT', 'priorite', 'date_creation',
            'date_prevue_debut', 'date_debut_reel', 'date_fin_reelle',
            'intervention_id', 'asset_id', 'statut_nom'
        ]

class InterventionSyncSerializer(serializers.ModelSerializer):
    """
    Serializer simplifié pour les interventions
    """
    operations = OperationMobileSerializer(many=True, read_only=True)
    
    class Meta:
        model = Intervention
        fields = [
            'id', 'nom', 'description', 'statut', 'duree_estimee_heures',
            'techniciens_requis', 'operations'
        ]

class AssetSyncSerializer(serializers.ModelSerializer):
    """
    Serializer simplifié pour les assets
    """
    class Meta:
        model = Asset
        fields = [
            'id', 'nom', 'reference', 'statut', 'criticite',
            'localisation_texte', 'latitude', 'longitude',
            'qr_code_identifier'
        ]

# ==============================================================================
# SERIALIZERS DE STATISTIQUES
# ==============================================================================

class StatistiquesMobileSerializer(serializers.Serializer):
    """
    Serializer pour les statistiques du dashboard mobile
    """
    taches_assignees = serializers.IntegerField()
    taches_en_cours = serializers.IntegerField()
    taches_terminees_semaine = serializers.IntegerField()
    taches_en_retard = serializers.IntegerField()
    
    demandes_reparation_creees = serializers.IntegerField()
    demandes_reparation_assignees = serializers.IntegerField()
    
    assets_en_panne = serializers.IntegerField()
    interventions_disponibles = serializers.IntegerField()
    
    # Graphiques
    repartition_par_priorite = serializers.DictField()
    evolution_taches_semaine = serializers.ListField()

class NotificationMobileSerializer(serializers.Serializer):
    """
    Serializer pour les notifications mobile
    """
    id = serializers.CharField()
    type = serializers.ChoiceField(choices=['INFO', 'WARNING', 'ERROR', 'SUCCESS'])
    title = serializers.CharField()
    message = serializers.CharField()
    timestamp = serializers.DateTimeField()
    read = serializers.BooleanField(default=False)
    
    # Données optionnelles pour navigation
    action_url = serializers.CharField(required=False)
    ot_id = serializers.IntegerField(required=False)
    demande_id = serializers.IntegerField(required=False)