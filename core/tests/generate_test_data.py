#!/usr/bin/env python3
"""
Script de génération de données de test pour GMOA

UTILISATION:
    python manage.py shell
    >>> exec(open('generate_test_data.py').read())
    >>> generate_test_data(5000)

Ou directement :
    python generate_test_data.py
"""

import os
import sys
import django
import random
from datetime import datetime, timedelta
from django.utils import timezone
from django.contrib.auth.models import User
from faker import Faker

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gmao_project.settings')
django.setup()

from core.models import (
    OrdreDeTravail, Asset, Intervention, StatutWorkflow, CategorieAsset,
    ProfilUtilisateur, Equipe, RapportExecution, Reponse, PointDeControle,
    Operation, CommentaireOT, FichierMedia, ActionCorrective
)

# Initialiser Faker pour données réalistes
fake = Faker('fr_FR')

def create_basic_data():
    """Créer les données de base nécessaires"""
    print("📋 Création des données de base...")
    
    # Créer des utilisateurs si pas assez
    users_count = User.objects.count()
    if users_count < 20:
        print(f"   Création de {20 - users_count} utilisateurs...")
        for i in range(20 - users_count):
            username = f"user_{i+users_count}"
            user = User.objects.create_user(
                username=username,
                email=f"{username}@gmao.local",
                password="test123",
                first_name=fake.first_name(),
                last_name=fake.last_name()
            )
            
            # Créer profil
            role = random.choice(['TECHNICIEN', 'MANAGER', 'OPERATEUR', 'ADMIN'])
            ProfilUtilisateur.objects.get_or_create(
                user=user,
                defaults={
                    'role': role,
                    'telephone': fake.phone_number()
                }
            )
    
    # Créer des catégories d'assets
    categories_data = [
        'Pompes', 'Moteurs', 'Compresseurs', 'Vannes', 'Capteurs',
        'Convoyeurs', 'Chaudières', 'Climatisation', 'Électrique', 'Hydraulique'
    ]
    
    for cat_name in categories_data:
        CategorieAsset.objects.get_or_create(nom=cat_name)
    
    # Créer des assets si pas assez
    assets_count = Asset.objects.count()
    if assets_count < 100:
        print(f"   Création de {100 - assets_count} assets...")
        categories = list(CategorieAsset.objects.all())
        
        for i in range(100 - assets_count):
            Asset.objects.create(
                nom=f"{fake.company()} {random.choice(['Pompe', 'Moteur', 'Compresseur'])} {i+assets_count}",
                reference=f"AST-{i+assets_count:04d}",
                categorie=random.choice(categories),
                marque=random.choice(['Siemens', 'ABB', 'Schneider', 'Bosch', 'Grundfos']),
                modele=f"Model-{fake.bothify('##??##')}",
                statut=random.choice(['EN_SERVICE', 'EN_MAINTENANCE', 'ARRETE', 'EN_PANNE']),
                criticite=random.choice([1, 2, 3, 4]),
                localisation_texte=f"Bâtiment {random.choice(['A', 'B', 'C'])} - Niveau {random.randint(1, 5)}",
                latitude=fake.latitude(),
                longitude=fake.longitude()
            )
    
    # Créer des interventions si pas assez
    interventions_count = Intervention.objects.filter(statut='VALIDATED').count()
    if interventions_count < 20:
        print(f"   Création de {20 - interventions_count} interventions...")
        for i in range(20 - interventions_count):
            intervention = Intervention.objects.create(
                nom=f"Maintenance {random.choice(['Préventive', 'Corrective', 'Prédictive'])} {i+interventions_count}",
                description=fake.text(max_nb_chars=200),
                statut='VALIDATED',
                duree_estimee_heures=random.randint(1, 8),
                techniciens_requis=random.randint(1, 3)
            )
            
            # Créer des opérations pour chaque intervention
            for j in range(random.randint(2, 5)):
                operation = Operation.objects.create(
                    intervention=intervention,
                    nom=f"Opération {j+1}: {random.choice(['Contrôle', 'Nettoyage', 'Réglage', 'Test'])}",
                    ordre=j+1
                )
                
                # Créer des points de contrôle
                for k in range(random.randint(1, 4)):
                    PointDeControle.objects.create(
                        operation=operation,
                        label=f"Point {k+1}: {fake.sentence(nb_words=4)}",
                        type_champ=random.choice(['TEXT', 'NUMBER', 'BOOLEAN', 'SELECT']),
                        aide=fake.sentence(nb_words=8),
                        est_obligatoire=random.choice([True, False]),
                        ordre=k+1,
                        permettre_photo=random.choice([True, False])
                    )
    
    # Créer des statuts workflow
    statuts_data = [
        ('NOUVEAU', 'Nouveau', '#gray'),
        ('ASSIGNE', 'Assigné', '#blue'),
        ('EN_COURS', 'En cours', '#yellow'),
        ('EN_ATTENTE', 'En attente', '#orange'),
        ('TERMINE', 'Terminé', '#green'),
        ('ANNULE', 'Annulé', '#red')
    ]
    
    for nom, desc, couleur in statuts_data:
        StatutWorkflow.objects.get_or_create(
            nom=nom,
            defaults={
                'description': desc,
                'couleur_html': couleur,
                'est_statut_final': nom in ['TERMINE', 'ANNULE']
            }
        )
    
    print("   ✅ Données de base créées")

def generate_test_data(nb_ordres=5000, batch_size=100):
    """
    Génère des ordres de travail de test en masse
    
    Args:
        nb_ordres (int): Nombre d'ordres de travail à créer
        batch_size (int): Taille des lots pour l'insertion
    """
    print(f"🚀 Génération de {nb_ordres} ordres de travail de test...")
    print(f"📦 Traitement par lots de {batch_size}")
    
    # Créer les données de base si nécessaire
    create_basic_data()
    
    # Récupérer les données existantes
    users = list(User.objects.filter(is_active=True))
    assets = list(Asset.objects.all())
    interventions = list(Intervention.objects.filter(statut='VALIDATED'))
    statuts = list(StatutWorkflow.objects.all())
    equipes = list(Equipe.objects.all())
    
    if not users or not assets or not interventions:
        print("❌ Erreur: Pas assez de données de base")
        return
    
    print(f"📊 Données disponibles:")
    print(f"   - {len(users)} utilisateurs")
    print(f"   - {len(assets)} assets")  
    print(f"   - {len(interventions)} interventions")
    print(f"   - {len(statuts)} statuts")
    
    # Générer par lots
    ordres_crees = 0
    
    for batch_start in range(0, nb_ordres, batch_size):
        batch_end = min(batch_start + batch_size, nb_ordres)
        batch_ordres = []
        
        print(f"   📦 Lot {batch_start//batch_size + 1}: {batch_start+1} à {batch_end}")
        
        for i in range(batch_start, batch_end):
            # Générer dates réalistes
            date_creation = fake.date_time_between(start_date='-6M', end_date='now', tzinfo=timezone.get_current_timezone())
            date_prevue = date_creation + timedelta(days=random.randint(1, 30))
            
            # Status workflow réaliste
            age_days = (timezone.now() - date_creation).days
            if age_days > 30:
                statut = random.choice([s for s in statuts if s.est_statut_final])
            elif age_days > 7:
                statut = random.choice(statuts)
            else:
                statut = random.choice([s for s in statuts if not s.est_statut_final])
            
            # Créer l'ordre de travail
            ordre = OrdreDeTravail(
                titre=f"OT-{i+1:05d} - {fake.catch_phrase()}",
                description_detaillee=fake.text(max_nb_chars=300),
                type_OT=random.choice(['PREVENTIVE', 'CORRECTIVE', 'PREDICTIVE', 'INSPECTION']),
                intervention=random.choice(interventions),
                asset=random.choice(assets),
                cree_par=random.choice(users),
                assigne_a_technicien=random.choice(users) if random.random() > 0.3 else None,
                assigne_a_equipe=random.choice(equipes) if equipes and random.random() > 0.7 else None,
                statut=statut,
                priorite=random.choices([1, 2, 3, 4], weights=[20, 50, 25, 5])[0],
                date_creation=date_creation,
                date_prevue_debut=date_prevue,
                cout_main_oeuvre_reel=round(random.uniform(50, 500), 2),
                cout_pieces_reel=round(random.uniform(0, 200), 2)
            )
            
            # Ajouter dates réelles si terminé
            if statut.est_statut_final and random.random() > 0.2:
                ordre.date_debut_reel = date_prevue + timedelta(hours=random.randint(-24, 48))
                ordre.date_fin_reelle = ordre.date_debut_reel + timedelta(hours=random.randint(1, 12))
            
            batch_ordres.append(ordre)
        
        # Insertion en lot
        try:
            OrdreDeTravail.objects.bulk_create(batch_ordres, batch_size=batch_size)
            ordres_crees += len(batch_ordres)
            print(f"      ✅ {len(batch_ordres)} ordres créés")
        except Exception as e:
            print(f"      ❌ Erreur lot: {e}")
            continue
    
    print(f"\n🎉 Génération terminée !")
    print(f"📊 {ordres_crees} ordres de travail créés au total")
    
    # Statistiques finales
    print_statistics()

def generate_rich_data(nb_ordres=1000):
    """
    Génère des données enrichies avec rapports, commentaires, etc.
    """
    print(f"✨ Génération de données enrichies pour {nb_ordres} ordres...")
    
    # Récupérer les ordres récents
    ordres = OrdreDeTravail.objects.order_by('-id')[:nb_ordres]
    users = list(User.objects.filter(is_active=True))
    
    for i, ordre in enumerate(ordres):
        if i % 100 == 0:
            print(f"   📦 Traitement ordre {i+1}/{len(ordres)}")
        
        # Créer rapport d'exécution
        rapport, created = RapportExecution.objects.get_or_create(
            ordre_de_travail=ordre,
            defaults={
                'cree_par': ordre.cree_par or random.choice(users),
                'statut_rapport': random.choice(['BROUILLON', 'EN_COURS', 'FINALISE']),
                'date_creation': ordre.date_creation,
                'commentaire_global': fake.text(max_nb_chars=200) if random.random() > 0.5 else ""
            }
        )
        
        # Ajouter des commentaires
        if random.random() > 0.6:
            for _ in range(random.randint(1, 3)):
                CommentaireOT.objects.create(
                    ordre_de_travail=ordre,
                    auteur=random.choice(users),
                    contenu=fake.sentence(nb_words=random.randint(5, 15)),
                    date_creation=fake.date_time_between(
                        start_date=ordre.date_creation,
                        end_date='now',
                        tzinfo=timezone.get_current_timezone()
                    )
                )
        
        # Ajouter des réponses aux points de contrôle
        if random.random() > 0.4:
            operations = ordre.intervention.operations.all()
            for operation in operations:
                points = operation.points_de_controle.all()
                for point in points:
                    if random.random() > 0.3:  # 70% des points remplis
                        valeur = generate_realistic_response(point.type_champ)
                        Reponse.objects.create(
                            rapport_execution=rapport,
                            point_de_controle=point,
                            valeur=valeur,
                            saisi_par=ordre.assigne_a_technicien or random.choice(users),
                            date_reponse=fake.date_time_between(
                                start_date=ordre.date_creation,
                                end_date='now',
                                tzinfo=timezone.get_current_timezone()
                            )
                        )
    
    print("✅ Données enrichies générées")

def generate_realistic_response(type_champ):
    """Génère une réponse réaliste selon le type de champ - VERSION CORRIGÉE"""
    if type_champ == 'BOOLEAN':
        return random.choice(['OUI', 'NON'])
    elif type_champ == 'NUMBER':
        return str(round(random.uniform(0, 100), 2))
    elif type_champ == 'SELECT':
        return random.choice(['Conforme', 'Non conforme', 'À vérifier'])
    elif type_champ == 'DATE':
        # CORRECTION : générer une date puis convertir en string
        from datetime import date
        fake_date = date.today() - timedelta(days=random.randint(0, 365))
        return fake_date.isoformat()  # Maintenant ça marche !
    elif type_champ == 'DATETIME':
        # Pour les datetime aussi
        fake_datetime = timezone.now() - timedelta(days=random.randint(0, 365))
        return fake_datetime.isoformat()
    else:  # TEXT, TEXTAREA
        return f"Reponse test {random.randint(1, 1000)}"

def print_statistics():
    """Affiche les statistiques des données générées"""
    print("\n📊 STATISTIQUES DES DONNÉES:")
    print("=" * 50)
    
    # Stats ordres de travail
    total_ot = OrdreDeTravail.objects.count()
    ot_par_statut = {}
    for statut in StatutWorkflow.objects.all():
        count = OrdreDeTravail.objects.filter(statut=statut).count()
        ot_par_statut[statut.nom] = count
    
    print(f"🔧 Ordres de travail: {total_ot}")
    for statut, count in ot_par_statut.items():
        print(f"   - {statut}: {count}")
    
    # Stats assets
    print(f"🏭 Assets: {Asset.objects.count()}")
    print(f"👥 Utilisateurs: {User.objects.count()}")
    print(f"📋 Interventions: {Intervention.objects.count()}")
    print(f"💬 Commentaires: {CommentaireOT.objects.count()}")
    print(f"📝 Rapports: {RapportExecution.objects.count()}")
    print(f"✅ Réponses: {Reponse.objects.count()}")
    
    # Performance approximative
    recent_ots = OrdreDeTravail.objects.filter(
        date_creation__gte=timezone.now() - timedelta(days=30)
    ).count()
    print(f"📈 OT récents (30 jours): {recent_ots}")

def cleanup_test_data():
    """Nettoie les données de test (ATTENTION: supprime tout!)"""
    print("🧹 NETTOYAGE DES DONNÉES DE TEST")
    print("⚠️  ATTENTION: Cette action va supprimer TOUTES les données!")
    
    confirm = input("Tapez 'SUPPRIMER' pour confirmer: ")
    if confirm != 'SUPPRIMER':
        print("❌ Nettoyage annulé")
        return
    
    print("🗑️  Suppression en cours...")
    
    # Supprimer dans l'ordre inverse des dépendances
    CommentaireOT.objects.all().delete()
    Reponse.objects.all().delete()
    ActionCorrective.objects.all().delete()
    FichierMedia.objects.all().delete()
    RapportExecution.objects.all().delete()
    OrdreDeTravail.objects.all().delete()
    
    print("✅ Données de test supprimées")

if __name__ == "__main__":
    print("🚀 GÉNÉRATEUR DE DONNÉES DE TEST GMOA")
    print("====================================")
    
    choice = input("""
Choisissez une option:
1. Générer 5000 ordres de travail simples
2. Générer 1000 ordres avec données enrichies  
3. Générer un nombre personnalisé
4. Nettoyer toutes les données de test
5. Afficher les statistiques actuelles

Votre choix (1-5): """)
    
    if choice == "1":
        generate_test_data(5000)
    elif choice == "2":
        generate_test_data(1000)
        generate_rich_data(1000)
    elif choice == "3":
        try:
            nb = int(input("Nombre d'ordres à générer: "))
            generate_test_data(nb)
        except ValueError:
            print("❌ Nombre invalide")
    elif choice == "4":
        cleanup_test_data()
    elif choice == "5":
        print_statistics()
    else:
        print("❌ Choix invalide")