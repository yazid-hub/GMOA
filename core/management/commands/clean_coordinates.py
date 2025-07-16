# Fichier: core/management/commands/clean_coordinates.py

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.conf import settings
from core.models import Asset
from core.views import validate_coordinates
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Nettoie les coordonnées invalides des assets'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Affiche les assets à nettoyer sans les modifier',
        )
        
        parser.add_argument(
            '--set-null',
            action='store_true',
            help='Met les coordonnées invalides à NULL (par défaut)',
        )
        
        parser.add_argument(
            '--delete',
            action='store_true',
            help='Supprime les assets avec coordonnées invalides (DANGEREUX)',
        )
        
        parser.add_argument(
            '--report',
            action='store_true',
            help='Génère un rapport détaillé sans modification',
        )
        
        parser.add_argument(
            '--export',
            type=str,
            help='Exporte les assets invalides vers un fichier CSV',
        )

    def handle(self, *args, **options):
        """
        Traite le nettoyage des coordonnées invalides
        """
        try:
            self.stdout.write(self.style.SUCCESS('🧹 Début du nettoyage des coordonnées invalides'))
            
            # Récupérer tous les assets avec coordonnées
            assets = Asset.objects.filter(
                latitude__isnull=False,
                longitude__isnull=False
            )
            
            total_assets = assets.count()
            self.stdout.write(f"📊 {total_assets} assets avec coordonnées trouvés")
            
            # Analyser les coordonnées
            valid_assets = []
            invalid_assets = []
            
            for asset in assets:
                if validate_coordinates(asset.latitude, asset.longitude):
                    valid_assets.append(asset)
                else:
                    invalid_assets.append(asset)
            
            # Afficher les statistiques
            self.display_statistics(valid_assets, invalid_assets)
            
            # Générer un rapport si demandé
            if options['report']:
                self.generate_report(invalid_assets)
                return
            
            # Exporter si demandé
            if options['export']:
                self.export_invalid_assets(invalid_assets, options['export'])
                return
            
            # Traiter les assets invalides
            if invalid_assets:
                if options['dry_run']:
                    self.dry_run_preview(invalid_assets)
                elif options['delete']:
                    self.delete_invalid_assets(invalid_assets)
                else:
                    # Par défaut: mettre à NULL
                    self.set_coordinates_null(invalid_assets)
            else:
                self.stdout.write(self.style.SUCCESS('✅ Aucun asset avec coordonnées invalides trouvé'))
                
        except Exception as e:
            logger.error(f"Erreur lors du nettoyage des coordonnées: {e}")
            raise CommandError(f'Erreur lors du nettoyage: {e}')

    def display_statistics(self, valid_assets, invalid_assets):
        """
        Affiche les statistiques des coordonnées
        """
        total = len(valid_assets) + len(invalid_assets)
        
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('📊 STATISTIQUES DES COORDONNÉES'))
        self.stdout.write('='*50)
        
        self.stdout.write(f"Total des assets: {total}")
        self.stdout.write(self.style.SUCCESS(f"✅ Coordonnées valides: {len(valid_assets)} ({len(valid_assets)/total*100:.1f}%)"))
        self.stdout.write(self.style.ERROR(f"❌ Coordonnées invalides: {len(invalid_assets)} ({len(invalid_assets)/total*100:.1f}%)"))
        
        if invalid_assets:
            # Analyser les types d'erreurs
            null_coords = sum(1 for asset in invalid_assets if asset.latitude is None or asset.longitude is None)
            zero_coords = sum(1 for asset in invalid_assets if (asset.latitude == 0 and asset.longitude == 0))
            out_of_range = sum(1 for asset in invalid_assets if not (asset.latitude is None or asset.longitude is None or (asset.latitude == 0 and asset.longitude == 0)))
            
            self.stdout.write('\n📋 Détail des erreurs:')
            self.stdout.write(f"  - Coordonnées NULL: {null_coords}")
            self.stdout.write(f"  - Coordonnées (0,0): {zero_coords}")
            self.stdout.write(f"  - Hors limites GPS: {out_of_range}")

    def generate_report(self, invalid_assets):
        """
        Génère un rapport détaillé des coordonnées invalides
        """
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.WARNING('📋 RAPPORT DÉTAILLÉ DES COORDONNÉES INVALIDES'))
        self.stdout.write('='*60)
        
        if not invalid_assets:
            self.stdout.write(self.style.SUCCESS('✅ Aucun asset avec coordonnées invalides'))
            return
        
        for asset in invalid_assets:
            self.stdout.write(f"\n🔍 Asset ID: {asset.id}")
            self.stdout.write(f"   Nom: {asset.nom or 'N/A'}")
            self.stdout.write(f"   Référence: {asset.reference or 'N/A'}")
            self.stdout.write(f"   Catégorie: {asset.categorie.nom if asset.categorie else 'N/A'}")
            self.stdout.write(f"   Latitude: {asset.latitude}")
            self.stdout.write(f"   Longitude: {asset.longitude}")
            
            # Déterminer le type d'erreur
            if asset.latitude is None or asset.longitude is None:
                self.stdout.write(self.style.ERROR("   ❌ Erreur: Coordonnées NULL"))
            elif asset.latitude == 0 and asset.longitude == 0:
                self.stdout.write(self.style.ERROR("   ❌ Erreur: Coordonnées (0,0)"))
            elif not (-90 <= asset.latitude <= 90) or not (-180 <= asset.longitude <= 180):
                self.stdout.write(self.style.ERROR("   ❌ Erreur: Hors limites GPS"))
            else:
                self.stdout.write(self.style.ERROR("   ❌ Erreur: Autre (NaN, type invalide, etc.)"))

    def export_invalid_assets(self, invalid_assets, filename):
        """
        Exporte les assets invalides vers un fichier CSV
        """
        try:
            import csv
            
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['id', 'nom', 'reference', 'categorie', 'latitude', 'longitude', 'erreur']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                
                for asset in invalid_assets:
                    # Déterminer le type d'erreur
                    if asset.latitude is None or asset.longitude is None:
                        erreur = "Coordonnées NULL"
                    elif asset.latitude == 0 and asset.longitude == 0:
                        erreur = "Coordonnées (0,0)"
                    elif not (-90 <= asset.latitude <= 90) or not (-180 <= asset.longitude <= 180):
                        erreur = "Hors limites GPS"
                    else:
                        erreur = "Autre (NaN, type invalide)"
                    
                    writer.writerow({
                        'id': asset.id,
                        'nom': asset.nom or '',
                        'reference': asset.reference or '',
                        'categorie': asset.categorie.nom if asset.categorie else '',
                        'latitude': asset.latitude,
                        'longitude': asset.longitude,
                        'erreur': erreur
                    })
            
            self.stdout.write(self.style.SUCCESS(f'✅ Export terminé: {filename}'))
            self.stdout.write(f"📄 {len(invalid_assets)} assets exportés")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Erreur lors de l\'export: {e}'))

    def dry_run_preview(self, invalid_assets):
        """
        Affiche un aperçu des modifications qui seraient effectuées
        """
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.WARNING('🔍 APERÇU DES MODIFICATIONS (DRY RUN)'))
        self.stdout.write('='*50)
        
        self.stdout.write(f"📊 {len(invalid_assets)} assets seraient modifiés:")
        
        for asset in invalid_assets[:10]:  # Limiter à 10 pour l'aperçu
            self.stdout.write(f"  - Asset {asset.id} ({asset.nom or 'Sans nom'}): {asset.latitude}, {asset.longitude} → NULL, NULL")
        
        if len(invalid_assets) > 10:
            self.stdout.write(f"  ... et {len(invalid_assets) - 10} autres assets")
        
        self.stdout.write(f"\n💡 Pour effectuer les modifications, relancez sans --dry-run")

    def set_coordinates_null(self, invalid_assets):
        """
        Met les coordonnées invalides à NULL
        """
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.WARNING('🔧 NETTOYAGE DES COORDONNÉES'))
        self.stdout.write('='*50)
        
        if not invalid_assets:
            return
        
        # Demander confirmation
        confirm = input(f"⚠️  Voulez-vous vraiment mettre à NULL les coordonnées de {len(invalid_assets)} assets ? (oui/non): ")
        
        if confirm.lower() not in ['oui', 'yes', 'y', 'o']:
            self.stdout.write(self.style.WARNING('❌ Opération annulée'))
            return
        
        try:
            with transaction.atomic():
                updated_count = 0
                
                for asset in invalid_assets:
                    asset.latitude = None
                    asset.longitude = None
                    asset.save()
                    updated_count += 1
                    
                    if updated_count % 100 == 0:
                        self.stdout.write(f"📊 {updated_count}/{len(invalid_assets)} assets traités...")
                
                self.stdout.write(self.style.SUCCESS(f'✅ {updated_count} assets nettoyés avec succès'))
                logger.info(f"Nettoyage terminé: {updated_count} assets mis à jour")
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Erreur lors du nettoyage: {e}'))
            logger.error(f"Erreur lors du nettoyage: {e}")
            raise

    def delete_invalid_assets(self, invalid_assets):
        """
        Supprime les assets avec coordonnées invalides (DANGEREUX)
        """
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.ERROR('💀 SUPPRESSION DES ASSETS INVALIDES'))
        self.stdout.write('='*50)
        
        if not invalid_assets:
            return
        
        self.stdout.write(self.style.ERROR('⚠️  ATTENTION: Cette opération est IRRÉVERSIBLE !'))
        self.stdout.write(self.style.ERROR(f'⚠️  {len(invalid_assets)} assets seront DÉFINITIVEMENT supprimés'))
        
        # Double confirmation
        confirm1 = input("⚠️  Tapez 'SUPPRIMER' pour confirmer: ")
        if confirm1 != 'SUPPRIMER':
            self.stdout.write(self.style.WARNING('❌ Opération annulée'))
            return
        
        confirm2 = input("⚠️  Êtes-vous ABSOLUMENT sûr ? (oui/non): ")
        if confirm2.lower() not in ['oui', 'yes', 'y', 'o']:
            self.stdout.write(self.style.WARNING('❌ Opération annulée'))
            return
        
        try:
            with transaction.atomic():
                deleted_count = 0
                
                for asset in invalid_assets:
                    asset_id = asset.id
                    asset_nom = asset.nom or 'Sans nom'
                    asset.delete()
                    deleted_count += 1
                    
                    self.stdout.write(f"🗑️  Asset {asset_id} ({asset_nom}) supprimé")
                    
                    if deleted_count % 10 == 0:
                        self.stdout.write(f"📊 {deleted_count}/{len(invalid_assets)} assets supprimés...")
                
                self.stdout.write(self.style.ERROR(f'💀 {deleted_count} assets supprimés définitivement'))
                logger.warning(f"Suppression terminée: {deleted_count} assets supprimés")
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Erreur lors de la suppression: {e}'))
            logger.error(f"Erreur lors de la suppression: {e}")
            raise