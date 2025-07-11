# core/management/commands/init_gmao.py

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import (
    ProfilUtilisateur, StatutWorkflow, CategorieAsset,
    Competence, ParametreGlobal
)

class Command(BaseCommand):
    help = 'Initialise les données de base pour GMAO'
    
    def handle(self, *args, **options):
        self.stdout.write('Initialisation de GMAO...')
        
        # Créer les statuts de workflow par défaut
        statuts = [
            ('NOUVEAU', 'Nouveau', '#3B82F6', False),
            ('EN_COURS', 'En cours', '#F59E0B', False),
            ('EN_ATTENTE', 'En attente', '#EF4444', False),
            ('TERMINE', 'Terminé', '#10B981', True),
            ('ANNULE', 'Annulé', '#6B7280', True),
        ]
        
        for nom, description, couleur, final in statuts:
            StatutWorkflow.objects.get_or_create(
                nom=nom,
                defaults={
                    'description': description,
                    'couleur_html': couleur,
                    'est_statut_final': final
                }
            )
        
        # Créer les catégories d'assets par défaut
        categories = [
            'Équipements de production',
            'Véhicules',
            'Infrastructures',
            'Équipements informatiques',
            'Équipements de sécurité',
        ]
        
        for cat in categories:
            CategorieAsset.objects.get_or_create(nom=cat)
        
        # Créer les compétences par défaut
        competences = [
            ('Maintenance mécanique', 'Réparation et maintenance des équipements mécaniques'),
            ('Maintenance électrique', 'Interventions sur les systèmes électriques'),
            ('Maintenance hydraulique', 'Systèmes hydrauliques et pneumatiques'),
            ('Maintenance informatique', 'Équipements et systèmes informatiques'),
            ('Conduite d\'équipements', 'Utilisation et conduite d\'équipements spécialisés'),
        ]
        
        for nom, desc in competences:
            Competence.objects.get_or_create(
                nom=nom,
                defaults={'description': desc}
            )
        
        # Créer les paramètres globaux
        parametres = [
            ('MAINTENANCE_PREVENTIVE_ACTIVE', 'true', 'Active la maintenance préventive automatique'),
            ('NOTIFICATION_EMAIL_ACTIVE', 'true', 'Active les notifications par email'),
            ('EXPORT_PDF_LOGO_URL', '', 'URL du logo pour les exports PDF'),
            ('DUREE_RETENTION_RAPPORTS_JOURS', '365', 'Durée de rétention des rapports en jours'),
        ]
        
        for cle, valeur, desc in parametres:
            ParametreGlobal.objects.get_or_create(
                cle=cle,
                defaults={
                    'valeur': valeur,
                    'description': desc
                }
            )
        
        self.stdout.write(
            self.style.SUCCESS('Initialisation GMAO terminée avec succès!')
        )