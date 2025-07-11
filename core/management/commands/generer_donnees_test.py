
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import *
from django.utils import timezone
from datetime import timedelta
import random

class Command(BaseCommand):
    help = 'Génère des données de test pour GMAO'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--nb-assets',
            type=int,
            default=20,
            help='Nombre d\'assets à créer'
        )
        
        parser.add_argument(
            '--nb-ot',
            type=int,
            default=50,
            help='Nombre d\'ordres de travail à créer'
        )
    
    def handle(self, *args, **options):
        self.stdout.write('Génération de données de test...')
        
        # Créer des utilisateurs test
        admin, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@gmao.com',
                'first_name': 'Admin',
                'last_name': 'GMAO',
                'is_staff': True,
                'is_superuser': True
            }
        )
        if created:
            admin.set_password('admin123')
            admin.save()
            ProfilUtilisateur.objects.create(user=admin, role='ADMIN', telephone='01.23.45.67.89')
        
        # Créer des techniciens
        techniciens = []
        for i in range(5):
            user, created = User.objects.get_or_create(
                username=f'technicien{i+1}',
                defaults={
                    'email': f'technicien{i+1}@gmao.com',
                    'first_name': f'Technicien{i+1}',
                    'last_name': 'Test'
                }
            )
            if created:
                user.set_password('tech123')
                user.save()
                ProfilUtilisateur.objects.create(user=user, role='TECHNICIEN', telephone=f'01.23.45.67.{90+i}')
            techniciens.append(user)
        
        # Créer des assets
        categories = CategorieAsset.objects.all()
        for i in range(options['nb_assets']):
            Asset.objects.get_or_create(
                nom=f'Équipement-{i+1:03d}',
                defaults={
                    'reference': f'EQ-{i+1:03d}',
                    'categorie': random.choice(categories) if categories else None,
                    'statut': random.choice(['EN_SERVICE', 'EN_MAINTENANCE', 'EN_PANNE']),
                    'criticite': random.randint(1, 4),
                    'localisation_texte': f'Zone {chr(65 + i % 26)}',
                    'date_mise_en_service': timezone.now() - timedelta(days=random.randint(30, 1095))
                }
            )
        
        # Créer une intervention type
        intervention, created = Intervention.objects.get_or_create(
            nom='Maintenance préventive standard',
            defaults={
                'description': 'Intervention de maintenance préventive standard',
                'statut': 'VALIDATED',
                'duree_estimee_heures': 2,
                'techniciens_requis': 1
            }
        )
        
        if created:
            # Créer des opérations pour cette intervention
            op1 = Operation.objects.create(
                intervention=intervention,
                nom='Contrôle visuel général',
                ordre=1
            )
            
            PointDeControle.objects.create(
                operation=op1,
                label='État général de l\'équipement',
                type_champ='SELECT',
                options='Bon;Moyen;Mauvais',
                est_obligatoire=True,
                ordre=1
            )
            
            PointDeControle.objects.create(
                operation=op1,
                label='Niveau de fluide',
                type_champ='SELECT',
                options='Correct;À compléter;Vide',
                est_obligatoire=True,
                ordre=2,
                permettre_photo=True
            )
        
        # Créer des ordres de travail
        assets = list(Asset.objects.all())
        statuts = list(StatutWorkflow.objects.all())
        
        for i in range(options['nb_ot']):
            date_prevue = timezone.now() + timedelta(days=random.randint(-10, 30))
            
            OrdreDeTravail.objects.get_or_create(
                titre=f'Maintenance {i+1:03d}',
                defaults={
                    'type_OT': random.choice(['PREVENTIVE', 'CORRECTIVE', 'INSPECTION']),
                    'intervention': intervention,
                    'asset': random.choice(assets),
                    'priorite': random.randint(1, 4),
                    'date_prevue_debut': date_prevue,
                    'assigne_a_technicien': random.choice(techniciens),
                    'statut': random.choice(statuts) if statuts else None,
                    'cree_par': admin
                }
            )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Données de test générées: {options["nb_assets"]} assets, {options["nb_ot"]} OT'
            )
        )