# Fichier : core/models.py - Version Corrigée et Complète

from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.utils import timezone
import uuid
import json
from math import radians, cos, sin, asin, sqrt
import json
# ==============================================================================
# AXE 0 : GESTION DES UTILISATEURS & COMPÉTENCES
# ==============================================================================

class ProfilUtilisateur(models.Model):
    ROLE_CHOIX = [
        ('ADMIN', 'Administrateur'),
        ('MANAGER', 'Manager'),
        ('TECHNICIEN', 'Technicien'),
        ('OPERATEUR', 'Opérateur'),
        ('SUPERVISEUR', 'Superviseur'),
    ]
    
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profil')
    telephone = models.CharField(max_length=20, blank=True, null=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOIX, default='OPERATEUR')
    
    def __str__(self):
        return f"{self.user.username} ({self.role})"

class Competence(models.Model):
    nom = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return self.nom

class UtilisateurCompetence(models.Model):
    utilisateur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    competence = models.ForeignKey(Competence, on_delete=models.CASCADE)
    niveau = models.PositiveIntegerField(choices=[(1, 'Débutant'), (2, 'Intermédiaire'), (3, 'Expert')], default=1)
    date_obtention = models.DateField(default=timezone.now)
    
    class Meta:
        unique_together = ('utilisateur', 'competence')
    
    def __str__(self):
        return f"{self.utilisateur.username} - {self.competence.nom} (Niveau {self.niveau})"

class Equipe(models.Model):
    nom = models.CharField(max_length=100, unique=True)
    chef_equipe = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='equipes_dirigees')
    membres = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='equipes')
    
    def __str__(self):
        return self.nom




# ==============================================================================
# AXE 1 : GESTION DES ACTIFS (ASSETS) & LEURS DONNÉES DYNAMIQUES
# ==============================================================================
# 3. MODÈLE ZONE GÉOGRAPHIQUE
class ZoneGeographique(models.Model):
    """
    Zones de déploiement FTTH
    """
    nom = models.CharField(max_length=100)
    code_postal = models.CharField(max_length=10)
    commune = models.CharField(max_length=100)
    
    TYPE_ZONE = [
        ('ZONE_DENSE', 'Zone très dense'),
        ('ZONE_MOINS_DENSE', 'Zone moins dense'),
        ('ZONE_RURALE', 'Zone rurale')
    ]
    type_zone = models.CharField(max_length=20, choices=TYPE_ZONE)
    
    # Géométrie de la zone
    contour_geojson = models.JSONField(help_text="Contour géographique de la zone")
    
    # Statistiques
    nb_logements_total = models.PositiveIntegerField(default=0)
    nb_logements_eligibles = models.PositiveIntegerField(default=0)
    taux_raccordement = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    def __str__(self):
        return f"{self.nom} ({self.commune})"
    
class CategorieAsset(models.Model):
    nom = models.CharField(max_length=100, unique=True)
    
    def __str__(self):
        return self.nom

class Asset(models.Model):
    STATUT_ASSET_CHOIX = [
        ('EN_SERVICE', 'En service'), 
        ('EN_PANNE', 'En panne'), 
        ('EN_MAINTENANCE', 'En maintenance'), 
        ('HORS_SERVICE', 'Hors service')
    ]
    
    nom = models.CharField(max_length=255)
    reference = models.CharField(max_length=100, blank=True, null=True)
    categorie = models.ForeignKey(CategorieAsset, on_delete=models.SET_NULL, null=True, blank=True)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='enfants')
    marque = models.CharField(max_length=100, blank=True, null=True)
    modele = models.CharField(max_length=100, blank=True, null=True)
    date_achat = models.DateField(null=True, blank=True)
    date_mise_en_service = models.DateField(null=True, blank=True)
    fin_garantie = models.DateField(null=True, blank=True)
    statut = models.CharField(max_length=20, choices=STATUT_ASSET_CHOIX, default='EN_SERVICE')
    criticite = models.PositiveIntegerField(choices=[(1, 'Basse'), (2, 'Moyenne'), (3, 'Haute'), (4, 'Critique')], default=2)
    localisation_texte = models.CharField(max_length=255, blank=True, null=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    photo_principale = models.ImageField(upload_to='asset_photos/', null=True, blank=True)
    qr_code_identifier = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    adresse_complete = models.TextField(
        blank=True, 
        null=True,
        help_text="Adresse complète de l'asset"
    )
    
    # QR Code pour identification mobile
    qr_code_image = models.ImageField(
        upload_to='qr_codes/', 
        null=True, 
        blank=True,
        help_text="Image du QR code généré automatiquement"
    )
    
    # Informations techniques étendues
    manuel_technique = models.FileField(
        upload_to='manuels_techniques/',
        null=True,
        blank=True,
        help_text="Manuel technique ou documentation de l'équipement"
    )
    
    derniere_maintenance = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date de la dernière maintenance effectuée"
    )
    
    prochaine_maintenance = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date prévue de la prochaine maintenance"
    )
    # NOUVEAUX CHAMPS FTTH
    zone_geographique = models.ForeignKey(ZoneGeographique, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Capacités techniques
    nb_fibres_total = models.PositiveIntegerField(null=True, blank=True, help_text="Nombre total de fibres")
    nb_fibres_utilisees = models.PositiveIntegerField(default=0, help_text="Nombre de fibres utilisées")
    
    # Position dans l'infrastructure
    niveau_hierarchique = models.PositiveIntegerField(default=1, help_text="1=NRO, 2=PM, 3=PB, 4=PTO")
    
    # Spécifications techniques
    TYPE_CONNECTEUR = [
        ('SC', 'SC'),
        ('LC', 'LC'), 
        ('FC', 'FC'),
        ('ST', 'ST'),
        ('E2000', 'E2000')
    ]
    type_connecteur = models.CharField(max_length=10, choices=TYPE_CONNECTEUR, blank=True)
    
    # Géométrie (pour les câbles)
    geometrie_geojson = models.JSONField(null=True, blank=True, help_text="Géométrie de l'asset (point, ligne, polygone)")
    @property
    def point_geojson(self):
        """
        Retourne la géolocalisation sous forme de Point GeoJSON
        """
        if self.latitude and self.longitude:
            return {
                "type": "Point",
                "coordinates": [float(self.longitude), float(self.latitude)]
            }
        return None
    
    @property
    def coordinates_string(self):
        """
        Retourne les coordonnées sous forme de chaîne
        Format: "latitude,longitude"
        """
        if self.latitude and self.longitude:
            return f"{self.latitude},{self.longitude}"
        return ""
    
    @property
    def coordinates_dict(self):
        """
        Retourne les coordonnées sous forme de dictionnaire
        """
        if self.latitude and self.longitude:
            return {
                'lat': float(self.latitude),
                'lng': float(self.longitude)
            }
        return None
    
    def set_coordinates_from_string(self, coords_string):
        """
        Définit les coordonnées à partir d'une chaîne "lat,lng"
        """
        try:
            lat_str, lng_str = coords_string.split(',')
            self.latitude = float(lat_str.strip())
            self.longitude = float(lng_str.strip())
        except (ValueError, TypeError):
            raise ValueError("Format attendu: 'latitude,longitude'")
    
    def set_coordinates_from_point(self, point_geojson):
        """
        Définit les coordonnées à partir d'un Point GeoJSON
        """
        if point_geojson and point_geojson.get('type') == 'Point':
            coords = point_geojson.get('coordinates', [])
            if len(coords) >= 2:
                self.longitude = coords[0]
                self.latitude = coords[1]
    
    def distance_to(self, other_asset):
        """
        Calcule la distance vers un autre asset (en mètres)
        Utilise la formule de Haversine
        """
        if not (self.latitude and self.longitude and 
                other_asset.latitude and other_asset.longitude):
            return None
            
        # Convertir en radians
        lat1, lng1 = radians(float(self.latitude)), radians(float(self.longitude))
        lat2, lng2 = radians(float(other_asset.latitude)), radians(float(other_asset.longitude))
        
        # Formule de Haversine
        dlat = lat2 - lat1
        dlng = lng2 - lng1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlng/2)**2
        c = 2 * asin(sqrt(a))
        r = 6371000  # Rayon de la Terre en mètres
        
        return c * r
    
    def distance_to_point(self, latitude, longitude):
        """
        Calcule la distance vers un point donné (en mètres)
        """
        if not (self.latitude and self.longitude):
            return None
        
        lat1, lng1 = radians(float(self.latitude)), radians(float(self.longitude))
        lat2, lng2 = radians(float(latitude)), radians(float(longitude))
        
        dlat = lat2 - lat1
        dlng = lng2 - lng1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlng/2)**2
        c = 2 * asin(sqrt(a))
        r = 6371000
        
        return c * r
    
    @property
    def is_geolocated(self):
        """
        Vérifie si l'asset est géolocalisé
        """
        return bool(self.latitude and self.longitude)
    
    def update_geometrie_from_coordinates(self):
        """
        Met à jour le champ geometrie_geojson à partir des coordonnées
        """
        if self.latitude and self.longitude:
            self.geometrie_geojson = self.point_geojson
    
    def save(self, *args, **kwargs):
        """
        Override save pour mettre à jour automatiquement la géométrie
        """
        # Mettre à jour la géométrie si on a des coordonnées
        if self.latitude and self.longitude and not self.geometrie_geojson:
            self.update_geometrie_from_coordinates()
        
        super().save(*args, **kwargs)
    
    @classmethod
    def find_nearby(cls, latitude, longitude, radius_meters=1000):
        """
        Trouve les assets dans un rayon donné
        Utilise une approximation simple sans GDAL
        """
        # Calcul approximatif (1 degré ≈ 111 km)
        delta_lat = radius_meters / 111000
        delta_lng = radius_meters / (111000 * cos(radians(float(latitude))))
        
        return cls.objects.filter(
            latitude__range=(latitude - delta_lat, latitude + delta_lat),
            longitude__range=(longitude - delta_lng, longitude + delta_lng),
            latitude__isnull=False,
            longitude__isnull=False
        )
    
    def __str__(self):
        location_info = ""
        if self.is_geolocated:
            location_info = f" ({self.latitude:.6f}, {self.longitude:.6f})"
        
        return f"{self.nom} ({self.reference or 'N/A'}){location_info}"
    def __str__(self):
        location_info = ""
        if self.is_geolocated:
            location_info = f" ({self.latitude:.6f}, {self.longitude:.6f})"
        
        return f"{self.nom} ({self.reference or 'N/A'}){location_info}"
    @property
    def taux_occupation(self):
        """Calcule le taux d'occupation des fibres"""
        if self.nb_fibres_total and self.nb_fibres_total > 0:
            return (self.nb_fibres_utilisees / self.nb_fibres_total) * 100
        return 0
    
    @property 
    def fibres_libres(self):
        """Nombre de fibres disponibles"""
        return (self.nb_fibres_total or 0) - self.nb_fibres_utilisees
    
    def __str__(self):
        return f"{self.nom} ({self.reference or 'N/A'})"

class AttributPersonnaliseAsset(models.Model):
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='attributs_perso')
    cle = models.CharField(max_length=100, help_text="Nom du champ personnalisé. Ex: 'Couleur RAL'")
    valeur = models.CharField(max_length=255, help_text="Valeur du champ. Ex: '5015'")
    
    class Meta:
        unique_together = ('asset', 'cle')
    
    def __str__(self):
        return f"{self.asset.nom} | {self.cle}: {self.valeur}"

# 2. MODÈLE CONNEXION FTTH
class ConnexionFibre(models.Model):
    """
    Relations entre assets FTTH (câbles, connecteurs)
    """
    asset_source = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='connexions_sortantes')
    asset_destination = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='connexions_entrantes')
    
    TYPE_CONNEXION = [
        ('FIBRE', 'Fibre optique'),
        ('CUIVRE', 'Cuivre'),
        ('COAXIAL', 'Coaxial'),
        ('WIRELESS', 'Sans fil')
    ]
    type_connexion = models.CharField(max_length=20, choices=TYPE_CONNEXION, default='FIBRE')
    
    # Spécifique FTTH
    numero_fibre = models.PositiveIntegerField(null=True, blank=True, help_text="Numéro de fibre dans le câble")
    couleur_fibre = models.CharField(max_length=20, blank=True, help_text="Couleur identification fibre")
    longueur_metres = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    affaiblissement_db = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Géométrie du tracé
    trace_geojson = models.JSONField(null=True, blank=True, help_text="Tracé géographique de la connexion")
    
    date_creation = models.DateTimeField(auto_now_add=True)
    actif = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ('asset_source', 'asset_destination', 'numero_fibre')
    
    def __str__(self):
        return f"{self.asset_source} → {self.asset_destination} (Fibre {self.numero_fibre})"


# 5. MODÈLE PLAN/SCHÉMA
class PlanSchema(models.Model):
    """
    Plans et schémas techniques
    """
    nom = models.CharField(max_length=100)
    zone_geographique = models.ForeignKey(ZoneGeographique, on_delete=models.CASCADE)
    
    TYPE_PLAN = [
        ('PLAN_MASSE', 'Plan de masse'),
        ('SCHEMA_SYNOPTIQUE', 'Schéma synoptique'),
        ('PLAN_DETAIL', 'Plan de détail'),
        ('SCHEMA_RACCORDEMENT', 'Schéma de raccordement')
    ]
    type_plan = models.CharField(max_length=30, choices=TYPE_PLAN)
    
    # Fichiers
    fichier_plan = models.FileField(upload_to='plans_ftth/')
    fichier_dwg = models.FileField(upload_to='plans_ftth/dwg/', null=True, blank=True)
    
    # Géoréférencement
    emprise_geojson = models.JSONField(null=True, blank=True)
    
    # Assets concernés
    assets_concernes = models.ManyToManyField(Asset, blank=True)
    
    date_creation = models.DateTimeField(auto_now_add=True)
    version = models.CharField(max_length=10, default="1.0")
    
    def __str__(self):
        return f"{self.nom} v{self.version}"

# ==============================================================================
# AXE 2 : GESTION DES STOCKS & PIÈCES DÉTACHÉES
# ==============================================================================

class PieceDetachee(models.Model):
    reference = models.CharField(max_length=100, unique=True)
    nom = models.CharField(max_length=255)
    stock_actuel = models.PositiveIntegerField(default=0)
    seuil_alerte_stock = models.PositiveIntegerField(default=0, help_text="Le système alertera si le stock passe sous ce seuil.")
    cout_unitaire = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    def __str__(self):
        return f"{self.nom} ({self.reference})"

# ==============================================================================
# AXE 3 : GESTION DES GAMMES DE MAINTENANCE (TEMPLATES)
# ==============================================================================

class Intervention(models.Model):
    STATUT_CHOIX = [
        ('DRAFT', 'Brouillon'),
        ('VALIDATED', 'Validé'),
        ('ARCHIVED', 'Archivé'),
    ]
    
    nom = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True, help_text="Décrivez l'objectif général de cette intervention.")
    statut = models.CharField(max_length=20, choices=STATUT_CHOIX, default='DRAFT')
    duree_estimee_heures = models.PositiveIntegerField(default=1, help_text="Durée estimée de l'intervention en heures.")
    techniciens_requis = models.PositiveIntegerField(default=1, help_text="Nombre de techniciens nécessaires.")
    competences_requises = models.ManyToManyField(Competence, blank=True, help_text="Compétences suggérées pour réaliser cette intervention.")
    pieces_necessaires = models.ManyToManyField(PieceDetachee, blank=True, help_text="Nomenclature des pièces habituellement nécessaires.")
    
    def __str__(self):
        return self.nom

class Operation(models.Model):
    intervention = models.ForeignKey(Intervention, on_delete=models.CASCADE, related_name='operations')
    nom = models.CharField(max_length=255)
    ordre = models.PositiveIntegerField(default=1)
    
    class Meta:
        ordering = ['ordre']
        unique_together = ('intervention', 'ordre')
    
    def __str__(self):
        return f"{self.intervention.nom} | Étape {self.ordre}: {self.nom}"

class PointDeControle(models.Model):
    TYPE_CHAMP_CHOIX = [
        ('TEXT', 'Texte libre'),
        ('NUMBER', 'Nombre'),
        ('BOOLEAN', 'Oui/Non'),
        ('SELECT', 'Liste de choix'),
        ('TEXTAREA', 'Zone de texte'),
        ('DATE', 'Date'),
        ('TIME', 'Heure'),
        ('DATETIME', 'Date et heure'),
    ]
    
    operation = models.ForeignKey(Operation, on_delete=models.CASCADE, related_name='points_de_controle')
    label = models.CharField(max_length=255)
    type_champ = models.CharField(max_length=20, choices=TYPE_CHAMP_CHOIX, default='TEXT')
    aide = models.TextField(blank=True, null=True, help_text="Instructions pour l'utilisateur.")
    options = models.TextField(blank=True, null=True, help_text="Pour les listes, séparez les options par un point-virgule (;).")
    est_obligatoire = models.BooleanField(default=False)
    ordre = models.PositiveIntegerField(default=1)
    depend_de = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='dependances')
    condition_affichage = models.CharField(max_length=100, blank=True, null=True, help_text="Condition à remplir sur le champ parent. Ex: 'OUI', '> 5', 'CONFORME'")
    permettre_photo = models.BooleanField(default=False, help_text="Autoriser l'ajout d'une ou plusieurs photos à cette réponse.")
    permettre_audio = models.BooleanField(default=False, help_text="Autoriser l'enregistrement d'un commentaire audio.")
    permettre_video = models.BooleanField(default=False, help_text="Autoriser l'enregistrement d'une vidéo.")
    permettre_fichiers = models.BooleanField(default=False , help_text="Autoriser l'ajout des fichiers.")

   # Types de fichiers autorisés pour les médias
    types_fichiers_autorises = models.CharField(
        max_length=255, 
        blank=True, 
        null=True,
        help_text="Types de fichiers autorisés séparés par des virgules (ex: PDF,ZIP,DOC,XLS,JPG,PNG,MP4)"
    )
    
    # Option demande de réparation
    peut_demander_reparation = models.BooleanField(
        default=False,
        help_text="Si coché, ce point peut générer une demande de réparation lors de l'exécution"
    )
    
    # Nouveaux champs pour améliorer les médias
    taille_max_fichier_mb = models.PositiveIntegerField(
        default=10,
        help_text="Taille maximale autorisée pour les fichiers en MB"
    )
    class Meta:
        ordering = ['ordre']
        
    def __str__(self):
        return self.label

# ==============================================================================
# AXE 4 : GESTION DES WORKFLOWS & STATUTS DYNAMIQUES
# ==============================================================================

class StatutWorkflow(models.Model):
    nom = models.CharField(max_length=50, unique=True)
    description = models.CharField(max_length=255, blank=True)
    couleur_html = models.CharField(max_length=7, default='#808080', help_text="Code couleur Hex. Ex: #FF5733")
    est_statut_final = models.BooleanField(default=False, help_text="Cocher si c'est un statut de clôture (Terminé, Annulé).")
    
    def __str__(self):
        return self.nom

# ==============================================================================
# AXE 5 : GESTION DE LA PLANIFICATION & ORDRES DE TRAVAIL (OT)
# ==============================================================================

class PlanMaintenancePreventive(models.Model):
    intervention = models.ForeignKey(Intervention, on_delete=models.PROTECT)
    asset_concerne = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name="plans_maintenance")
    frequence_jours = models.PositiveIntegerField(null=True, blank=True)
    date_prochaine_echeance = models.DateField(null=True, blank=True)
    actif = models.BooleanField(default=True)
    
    def __str__(self):
        return f"Plan préventif pour {self.asset_concerne.nom}"

class OrdreDeTravail(models.Model):
    TYPE_OT_CHOIX = [
        ('PREVENTIVE', 'Préventive'),
        ('CORRECTIVE', 'Corrective'),
        ('PREDICTIVE', 'Prédictive'),
        ('INSPECTION', 'Inspection'),
        ('AUDIT', 'Audit'),
        ('AUTRE', 'Autre')
    ]
    
    titre = models.CharField(max_length=255)
    description_detaillee = models.TextField(blank=True, null=True)
    bloque_par_reparation = models.BooleanField(default=False)
    type_OT = models.CharField(max_length=20, choices=TYPE_OT_CHOIX, default='AUTRE')
    intervention = models.ForeignKey(Intervention, on_delete=models.PROTECT)
    cree_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='ordres_de_travail_crees', help_text="L'utilisateur qui a initialement créé l'ordre de travail.")
    assigne_a_technicien = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='taches_assignees')
    assigne_a_equipe = models.ForeignKey(Equipe, on_delete=models.SET_NULL, null=True, blank=True)
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE)
    statut = models.ForeignKey(StatutWorkflow, on_delete=models.SET_NULL, null=True, blank=True)
    priorite = models.PositiveIntegerField(choices=[(1, 'Basse'), (2, 'Normale'), (3, 'Haute'), (4, 'Urgente')], default=2)
    date_creation = models.DateTimeField(default=timezone.now)
    date_prevue_debut = models.DateTimeField()
    date_debut_reel = models.DateTimeField(null=True, blank=True, help_text="Date et heure réelles du début de l'intervention.")
    date_fin_reelle = models.DateTimeField(null=True, blank=True, help_text="Date et heure réelles de la fin de l'intervention.")
    cout_main_oeuvre_reel = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    cout_pieces_reel = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f"OT-{self.id}: {self.titre}"

    def save(self, *args, **kwargs):
        """Logique automatique lors de la sauvegarde"""
        # Si aucun statut n'est défini, on prend le premier statut non-final
        if not self.statut:
            self.statut = StatutWorkflow.objects.filter(est_statut_final=False).first()
        super().save(*args, **kwargs)

# ==============================================================================
# AXE 6 : GESTION DE L'EXÉCUTION & RAPPORTS
# ==============================================================================

class RapportExecution(models.Model):
    STATUT_RAPPORT_CHOIX = [
        ('BROUILLON', 'Brouillon'),
        ('EN_COURS', 'En cours'),
        ('FINALISE', 'Finalisé'),
        ('ARCHIVE', 'Archivé'),
    ]
    
    ordre_de_travail = models.OneToOneField(OrdreDeTravail, on_delete=models.CASCADE, related_name="rapport")
    statut_rapport = models.CharField(max_length=20, choices=STATUT_RAPPORT_CHOIX, default='BROUILLON')
    date_creation = models.DateTimeField(default=timezone.now)
    date_derniere_maj = models.DateTimeField(auto_now=True)
    date_execution_debut = models.DateTimeField(null=True, blank=True)
    date_execution_fin = models.DateTimeField(null=True, blank=True)
    cree_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='rapports_crees')
    commentaire_global = models.TextField(blank=True, null=True, help_text="Commentaire général sur l'intervention.")
    
    def __str__(self):
        return f"Rapport OT-{self.ordre_de_travail.id}"

class MouvementStock(models.Model):
    TYPE_MOUVEMENT_CHOIX = [
        ('ENTREE', 'Entrée'),
        ('SORTIE', 'Sortie'),
        ('TRANSFERT', 'Transfert'),
        ('AJUSTEMENT', 'Ajustement'),
    ]
    
    piece_detachee = models.ForeignKey(PieceDetachee, on_delete=models.CASCADE, related_name='mouvements')
    type_mouvement = models.CharField(max_length=20, choices=TYPE_MOUVEMENT_CHOIX)
    quantite = models.IntegerField()
    ordre_de_travail = models.ForeignKey(OrdreDeTravail, on_delete=models.SET_NULL, null=True, blank=True, related_name='mouvements_stock')
    date_mouvement = models.DateTimeField(default=timezone.now)
    effectue_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    commentaire = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.type_mouvement} - {self.piece_detachee.nom} : {self.quantite}"

class Reponse(models.Model):
    rapport_execution = models.ForeignKey(RapportExecution, on_delete=models.CASCADE, related_name='reponses')
    point_de_controle = models.ForeignKey(PointDeControle, on_delete=models.CASCADE)
    valeur = models.TextField(blank=True, null=True)
    date_reponse = models.DateTimeField(default=timezone.now)
    saisi_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        unique_together = ('rapport_execution', 'point_de_controle')
    
    def __str__(self):
        return f"Réponse à '{self.point_de_controle.label}': {self.valeur}"


class FichierMedia(models.Model):
    TYPE_MEDIA_CHOIX = [
        ('PHOTO', 'Photographie'),
        ('AUDIO', 'Enregistrement audio'),
        ('VIDEO', 'Enregistrement vidéo'),
        ('DOCUMENT', 'Document (PDF, Word, etc.)'),
        ('SCHEMA', 'Schéma technique'),
        ('SIGNATURE', 'Signature électronique'),
    ]
    
    reponse = models.ForeignKey('Reponse', on_delete=models.CASCADE, related_name='fichiers_media')
    type_fichier = models.CharField(max_length=20, choices=TYPE_MEDIA_CHOIX)
    fichier = models.FileField(upload_to='media_rapports/')
    nom_original = models.CharField(max_length=255)
    taille_octets = models.PositiveBigIntegerField()
    date_upload = models.DateTimeField(default=timezone.now)

    # Métadonnées enrichies
    legende = models.CharField(
        max_length=255, 
        blank=True,
        help_text="Légende ou description du média"
    )
    
    mots_cles = models.CharField(
        max_length=500, 
        blank=True,
        help_text="Mots-clés séparés par des virgules pour la recherche"
    )
    
    # Géolocalisation
    latitude_capture = models.DecimalField(
        max_digits=9, 
        decimal_places=6, 
        null=True, 
        blank=True,
        help_text="Latitude où le média a été capturé"
    )
    
    longitude_capture = models.DecimalField(
        max_digits=9, 
        decimal_places=6, 
        null=True, 
        blank=True,
        help_text="Longitude où le média a été capturé"
    )
    
    # Informations techniques
    resolution = models.CharField(
        max_length=50, 
        blank=True,
        help_text="Résolution du média (ex: 1920x1080)"
    )
    
    duree_seconde = models.PositiveIntegerField(
        null=True, 
        blank=True,
        help_text="Durée en secondes pour audio/vidéo"
    )
    
    # Validation et approbation
    valide_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True,
        blank=True,
        related_name='medias_valides'
    )
    
    date_validation = models.DateTimeField(null=True, blank=True)
    
    # Métadonnées de traitement
    traite_automatiquement = models.BooleanField(
        default=False,
        help_text="Indique si le média a été traité automatiquement (compression, etc.)"
    )
    
    hash_fichier = models.CharField(
        max_length=64, 
        blank=True,
        help_text="Hash SHA-256 du fichier pour vérifier l'intégrité"
    )
    taille_originale = models.BigIntegerField(null=True)
    taille_compresse = models.BigIntegerField(null=True)
    resolution = models.CharField(max_length=20, null=True)
    duree_seconde = models.IntegerField(null=True)  # Pour audio/vidéo
    coordonnees_gps = models.JSONField(null=True)
    metadonnees = models.JSONField(default=dict)
    statut_traitement = models.CharField(max_length=20, default='EN_COURS')
    uploade_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='medias_uploades',
        help_text="Utilisateur qui a uploadé ce média"
    )
    class Meta:
        verbose_name = "Média enrichi"
        verbose_name_plural = "Médias enrichis"
    
    def __str__(self):
        return f"{self.type_fichier} - {self.nom_original}"


class AnnotationMedia(models.Model):
    """Annotations sur les médias (dessins, flèches, texte)"""
    media = models.ForeignKey(FichierMedia, on_delete=models.CASCADE)
    type_annotation = models.CharField(max_length=20)  # FLECHE, TEXTE, FORME
    donnees_svg = models.TextField()
    couleur = models.CharField(max_length=7, default='#FF0000')
    utilisateur = models.ForeignKey(User, on_delete=models.CASCADE)
    date_creation = models.DateTimeField(auto_now_add=True)
# ==============================================================================
# AXE 7 : ACTIONS Brouillon Intervention
# ==============================================================================
class BrouillonIntervention(models.Model):
    """Sauvegarde automatique des interventions en cours"""
    rapport_execution = models.OneToOneField(RapportExecution, on_delete=models.CASCADE)
    donnees_json = models.JSONField(default=dict)
    derniere_modification = models.DateTimeField(auto_now=True)
    version = models.IntegerField(default=1)

# ==============================================================================
# AXE 7 : ACTIONS CORRECTIVES & COMMENTAIRES
# ==============================================================================

class ActionCorrective(models.Model):
    STATUT_ACTION_CHOIX = [
        ('A_PLANIFIER', 'À planifier'),
        ('PLANIFIEE', 'Planifiée'),
        ('EN_COURS', 'En cours'),
        ('TERMINEE', 'Terminée'),
        ('ANNULEE', 'Annulée'),
    ]
    
    rapport_execution = models.ForeignKey(RapportExecution, on_delete=models.CASCADE, related_name='actions_correctives')
    titre = models.CharField(max_length=255)
    description = models.TextField()
    priorite = models.PositiveIntegerField(choices=[(1, 'Basse'), (2, 'Normale'), (3, 'Haute'), (4, 'Urgente')], default=2)
    statut = models.CharField(max_length=20, choices=STATUT_ACTION_CHOIX, default='A_PLANIFIER')
    assigne_a = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    date_echeance = models.DateField(null=True, blank=True)
    date_creation = models.DateTimeField(default=timezone.now)
    cree_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='actions_correctives_creees')
    
    def __str__(self):
        return self.titre

class CommentaireOT(models.Model):
    ordre_de_travail = models.ForeignKey(OrdreDeTravail, on_delete=models.CASCADE, related_name='commentaires')
    auteur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    contenu = models.TextField()
    date_creation = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-date_creation']
    
    def __str__(self):
        return f"Commentaire de {self.auteur.username} - {self.date_creation.strftime('%d/%m/%Y %H:%M')}"

# ==============================================================================
# AXE 8 : NOTIFICATIONS & PARAMÈTRES SYSTÈME
# ==============================================================================

class Notification(models.Model):
    TYPE_NOTIFICATION_CHOIX = [
        ('INFO', 'Information'),
        ('ALERTE', 'Alerte'),
        ('ERREUR', 'Erreur'),
        ('SUCCES', 'Succès'),
    ]
    
    utilisateur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    titre = models.CharField(max_length=255)
    message = models.TextField()
    type_notification = models.CharField(max_length=20, choices=TYPE_NOTIFICATION_CHOIX, default='INFO')
    lue = models.BooleanField(default=False)
    date_creation = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-date_creation']
    
    def __str__(self):
        return f"{self.titre} - {self.utilisateur.username}"

class ParametreGlobal(models.Model):
    cle = models.CharField(max_length=100, unique=True)
    valeur = models.TextField()
    description = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.cle}: {self.valeur}"

class ParametreUtilisateur(models.Model):
    utilisateur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='parametres')
    cle = models.CharField(max_length=100)
    valeur = models.TextField()
    
    class Meta:
        unique_together = ('utilisateur', 'cle')
    
    def __str__(self):
        return f"{self.utilisateur.username} - {self.cle}: {self.valeur}"
    

# ==============================================================================
# NOUVEAU MODÈLE : DEMANDES DE RÉPARATION
# ==============================================================================

class DemandeReparation(models.Model):
    """
    Gestion des demandes de réparation liées aux points de contrôle
    """
    
    STATUT_CHOIX = [
        ('EN_ATTENTE', 'En attente de validation'),
        ('VALIDEE', 'Validée par le manager'),
        ('EN_COURS', 'En cours de réalisation'),
        ('TERMINEE', 'Terminée avec succès'),
        ('REJETEE', 'Rejetée'),
        ('REPORTEE', 'Reportée'),
    ]
    
    PRIORITE_CHOIX = [
        (1, 'Basse - Non urgent'),
        (2, 'Normale - Standard'),
        (3, 'Haute - Important'),
        (4, 'Urgente - Critique'),
    ]
    
    # Identifiant unique auto-généré
    numero_demande = models.CharField(
        max_length=20, 
        unique=True, 
        editable=False,
        help_text="Numéro unique auto-généré (ex: DR-2025-001)"
    )
    
    # Références principales
    ordre_de_travail = models.ForeignKey(
        'OrdreDeTravail', 
        on_delete=models.CASCADE,
        related_name='demandes_reparation',
        help_text="Ordre de travail qui a généré cette demande"
    )
    
    point_de_controle = models.ForeignKey(
        'PointDeControle', 
        on_delete=models.CASCADE,
        related_name='demandes_reparation',
        help_text="Point de contrôle à l'origine de la demande"
    )
    
    reponse_origine = models.ForeignKey(
        'Reponse', 
        on_delete=models.CASCADE,
        related_name='demandes_reparation',
        null=True,
        blank=True,
        help_text="Réponse qui a déclenché cette demande"
    )
    
    # Informations de la demande
    titre = models.CharField(
        max_length=255,
        help_text="Titre court décrivant le problème"
    )
    
    description = models.TextField(
        help_text="Description détaillée du problème et des actions nécessaires"
    )
    
    priorite = models.PositiveIntegerField(
        choices=PRIORITE_CHOIX, 
        default=2,
        help_text="Niveau de priorité de la réparation"
    )
    
    statut = models.CharField(
        max_length=20, 
        choices=STATUT_CHOIX, 
        default='EN_ATTENTE',
        help_text="Statut actuel de la demande"
    )
    
    # Traçabilité et gestion
    cree_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='demandes_reparation_creees',
        help_text="Technicien ayant créé la demande"
    )
    
    validee_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True,
        blank=True,
        related_name='demandes_reparation_validees',
        help_text="Manager ayant validé la demande"
    )
    
    assignee_a = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True,
        blank=True,
        related_name='demandes_reparation_assignees',
        help_text="Technicien assigné à la réparation"
    )
    
    # Dates importantes
    date_creation = models.DateTimeField(
        default=timezone.now,
        help_text="Date de création de la demande"
    )
    
    date_validation = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="Date de validation par le manager"
    )
    
    date_echeance_souhaitee = models.DateField(
        null=True, 
        blank=True,
        help_text="Date limite souhaitée pour la réparation"
    )
    
    date_debut_reparation = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="Date de début des travaux de réparation"
    )
    
    date_fin_reparation = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="Date de fin des travaux de réparation"
    )
    
    # Informations financières
    cout_estime = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0.00,
        help_text="Coût estimé de la réparation"
    )
    
    cout_reel = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0.00,
        help_text="Coût réel de la réparation"
    )
    
    # Commentaires et notes
    commentaire_technicien = models.TextField(
        blank=True,
        null=True,
        help_text="Commentaires du technicien sur le problème"
    )
    
    commentaire_manager = models.TextField(
        blank=True,
        null=True,
        help_text="Commentaires du manager lors de la validation"
    )
    
    commentaire_resolution = models.TextField(
        blank=True,
        null=True,
        help_text="Commentaires sur la résolution du problème"
    )
    
    # Métadonnées
    bloque_cloture_ot = models.BooleanField(
        default=True,
        help_text="Si coché, empêche la clôture de l'OT tant que la réparation n'est pas terminée"
    )
    
    class Meta:
        ordering = ['-date_creation']
        verbose_name = "Demande de réparation"
        verbose_name_plural = "Demandes de réparation"
    
    def __str__(self):
        return f"{self.numero_demande} - {self.titre}"
    
    def save(self, *args, **kwargs):
        """Génération automatique du numéro de demande"""
        if not self.numero_demande:
            # Générer un numéro unique
            annee = timezone.now().year
            
            # Compter les demandes de cette année
            count = DemandeReparation.objects.filter(
                date_creation__year=annee
            ).count() + 1
            
            self.numero_demande = f"DR-{annee}-{count:03d}"
        
        super().save(*args, **kwargs)
    
    @property
    def duree_totale(self):
        """Calcule la durée totale de la réparation"""
        if self.date_debut_reparation and self.date_fin_reparation:
            return self.date_fin_reparation - self.date_debut_reparation
        return None
    
    @property
    def est_en_retard(self):
        """Vérifie si la demande est en retard par rapport à l'échéance"""
        if self.date_echeance_souhaitee and self.statut not in ['TERMINEE', 'REJETEE']:
            return timezone.now().date() > self.date_echeance_souhaitee
        return False
    
    def peut_etre_validee(self):
        """Vérifie si la demande peut être validée"""
        return self.statut == 'EN_ATTENTE'
    
    def peut_etre_commencee(self):
        """Vérifie si la réparation peut commencer"""
        return self.statut == 'VALIDEE'

# ==============================================================================
# MODÈLE POUR L'HISTORIQUE DES CHANGEMENTS
# ==============================================================================

class HistoriqueModification(models.Model):
    """
    Trace toutes les modifications importantes dans le système
    """
    
    TYPE_OBJET_CHOIX = [
        ('ORDRE_TRAVAIL', 'Ordre de Travail'),
        ('DEMANDE_REPARATION', 'Demande de Réparation'),
        ('ASSET', 'Asset'),
        ('INTERVENTION', 'Intervention'),
        ('RAPPORT', 'Rapport d\'exécution'),
    ]
    
    TYPE_ACTION_CHOIX = [
        ('CREATION', 'Création'),
        ('MODIFICATION', 'Modification'),
        ('SUPPRESSION', 'Suppression'),
        ('VALIDATION', 'Validation'),
        ('ASSIGNATION', 'Assignation'),
        ('CHANGEMENT_STATUT', 'Changement de statut'),
    ]
    
    # Références
    type_objet = models.CharField(max_length=50, choices=TYPE_OBJET_CHOIX)
    objet_id = models.PositiveIntegerField(help_text="ID de l'objet modifié")
    
    # Action effectuée
    type_action = models.CharField(max_length=50, choices=TYPE_ACTION_CHOIX)
    description = models.TextField(help_text="Description détaillée de la modification")
    
    # Données de changement
    ancienne_valeur = models.JSONField(
        null=True, 
        blank=True,
        help_text="Valeurs avant modification (format JSON)"
    )
    
    nouvelle_valeur = models.JSONField(
        null=True, 
        blank=True,
        help_text="Nouvelles valeurs (format JSON)"
    )
    
    # Traçabilité
    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True
    )
    
    date_modification = models.DateTimeField(default=timezone.now)
    
    # Métadonnées
    adresse_ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-date_modification']
        verbose_name = "Historique de modification"
        verbose_name_plural = "Historiques de modifications"
    
    def __str__(self):
        return f"{self.type_action} sur {self.type_objet} #{self.objet_id} par {self.utilisateur}"


















    