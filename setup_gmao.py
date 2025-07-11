#!/usr/bin/env python3
"""
Script de configuration pour GMOA - Système de Gestion de Maintenance

Ce script configure automatiquement votre base de données avec des données de test
pour démarrer rapidement avec l'application GMOA.

UTILISATION:
    python setup_gmoa.py

PRÉREQUIS:
    - Django installé
    - Être dans le répertoire du projet (même niveau que manage.py)
"""

import os
import sys
import django
from django.core.management import execute_from_command_line

def setup_django():
    """Configure l'environnement Django"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gmao_project.settings')
    django.setup()

def create_superuser():
    """Crée un superutilisateur par défaut"""
    from django.contrib.auth.models import User
    from core.models import ProfilUtilisateur
    
    if not User.objects.filter(username='admin').exists():
        user = User.objects.create_superuser(
            username='admin',
            email='admin@gmao.local',
            password='admin123',
            first_name='Administrateur',
            last_name='GMOA'
        )
        ProfilUtilisateur.objects.create(
            user=user,
            role='ADMIN',
            telephone='+33 1 23 45 67 89'
        )
        print("✓ Superutilisateur créé (admin/admin123)")
    else:
        print("✓ Superutilisateur existe déjà")

def create_test_users():
    """Crée des utilisateurs de test"""
    from django.contrib.auth.models import User
    from core.models import ProfilUtilisateur
    
    users_data = [
        {
            'username': 'technicien1',
            'email': 'technicien1@gmao.local',
            'password': 'tech123',
            'first_name': 'Jean',
            'last_name': 'Dupont',
            'role': 'TECHNICIEN',
            'telephone': '+33 1 23 45 67 90'
        },
        {
            'username': 'manager1',
            'email': 'manager1@gmao.local',
            'password': 'manager123',
            'first_name': 'Marie',
            'last_name': 'Martin',
            'role': 'MANAGER',
            'telephone': '+33 1 23 45 67 91'
        },
        {
            'username': 'operateur1',
            'email': 'operateur1@gmao.local',
            'password': 'oper123',
            'first_name': 'Pierre',
            'last_name': 'Bernard',
            'role': 'OPERATEUR',
            'telephone': '+33 1 23 45 67 92'
        }
    ]
    
    for user_data in users_data:
        if not User.objects.filter(username=user_data['username']).exists():
            user = User.objects.create_user(
                username=user_data['username'],
                email=user_data['email'],
                password=user_data['password'],
                first_name=user_data['first_name'],
                last_name=user_data['last_name']
            )
            ProfilUtilisateur.objects.create(
                user=user,
                role=user_data['role'],
                telephone=user_data['telephone']
            )
            print(f"✓ Utilisateur {user_data['username']} créé")

def create_basic_data():
    """Crée les données de base"""
    from core.models import (
        StatutWorkflow, CategorieAsset, Asset, Competence, 
        Equipe, PieceDetachee
    )
    from django.contrib.auth.models import User
    
    # Statuts workflow
    statuts = [
        {'nom': 'NOUVEAU', 'description': 'Ordre de travail créé', 'couleur_html': '#3B82F6', 'est_statut_final': False},
        {'nom': 'EN_COURS', 'description': 'Intervention en cours', 'couleur_html': '#F59E0B', 'est_statut_final': False},
        {'nom': 'EN_ATTENTE', 'description': 'En attente de pièces', 'couleur_html': '#6B7280', 'est_statut_final': False},
        {'nom': 'TERMINE', 'description': 'Intervention terminée', 'couleur_html': '#10B981', 'est_statut_final': True},
        {'nom': 'ANNULE', 'description': 'Ordre de travail annulé', 'couleur_html': '#EF4444', 'est_statut_final': True},
    ]
    
    for statut_data in statuts:
        StatutWorkflow.objects.get_or_create(nom=statut_data['nom'], defaults=statut_data)
    print("✓ Statuts de workflow créés")
    
    # Catégories d'assets
    categories = ['Pompes', 'Moteurs', 'Convoyeurs', 'Compresseurs', 'Échangeurs', 'Vannes']
    for cat_name in categories:
        CategorieAsset.objects.get_or_create(nom=cat_name)
    print("✓ Catégories d'assets créées")
    
    # Compétences
    competences = [
        'Maintenance mécanique', 'Maintenance électrique', 'Maintenance hydraulique',
        'Soudure', 'Usinage', 'Instrumentation', 'Automatismes'
    ]
    for comp_name in competences:
        Competence.objects.get_or_create(nom=comp_name)
    print("✓ Compétences créées")
    
    # Équipe de test
    if not Equipe.objects.filter(nom='Équipe Maintenance').exists():
        chef = User.objects.filter(profil__role='MANAGER').first()
        equipe = Equipe.objects.create(nom='Équipe Maintenance', chef_equipe=chef)
        techniciens = User.objects.filter(profil__role='TECHNICIEN')
        equipe.membres.set(techniciens)
        print("✓ Équipe de maintenance créée")
    
    # Pièces détachées
    pieces = [
        {'reference': 'JOINT-001', 'nom': 'Joint torique 20mm', 'stock_actuel': 50, 'seuil_alerte_stock': 10, 'cout_unitaire': 2.50},
        {'reference': 'ROUL-001', 'nom': 'Roulement 6208', 'stock_actuel': 25, 'seuil_alerte_stock': 5, 'cout_unitaire': 15.80},
        {'reference': 'FILTRE-001', 'nom': 'Filtre à huile hydraulique', 'stock_actuel': 12, 'seuil_alerte_stock': 3, 'cout_unitaire': 45.00},
        {'reference': 'COURR-001', 'nom': 'Courroie trapézoïdale A85', 'stock_actuel': 8, 'seuil_alerte_stock': 2, 'cout_unitaire': 28.90},
    ]
    
    for piece_data in pieces:
        PieceDetachee.objects.get_or_create(reference=piece_data['reference'], defaults=piece_data)
    print("✓ Pièces détachées créées")
    
    # Assets de test
    pompe_cat = CategorieAsset.objects.get(nom='Pompes')
    moteur_cat = CategorieAsset.objects.get(nom='Moteurs')
    
    assets = [
        {
            'nom': 'Pompe centrifuge P-101',
            'reference': 'P-101',
            'categorie': pompe_cat,
            'marque': 'Grundfos',
            'modele': 'CR 32-4',
            'statut': 'EN_SERVICE',
            'criticite': 3,
            'localisation_texte': 'Bâtiment A - Niveau 1'
        },
        {
            'nom': 'Moteur électrique M-201',
            'reference': 'M-201',
            'categorie': moteur_cat,
            'marque': 'ABB',
            'modele': 'M3BP 112M',
            'statut': 'EN_SERVICE',
            'criticite': 2,
            'localisation_texte': 'Bâtiment B - Niveau 2'
        },
        {
            'nom': 'Pompe doseuse P-301',
            'reference': 'P-301',
            'categorie': pompe_cat,
            'marque': 'Prominent',
            'modele': 'CONC0213',
            'statut': 'EN_MAINTENANCE',
            'criticite': 4,
            'localisation_texte': 'Atelier de production'
        }
    ]
    
    for asset_data in assets:
        Asset.objects.get_or_create(reference=asset_data['reference'], defaults=asset_data)
    print("✓ Assets de test créés")

def create_sample_intervention():
    """Crée une intervention d'exemple complète"""
    from core.models import Intervention, Operation, PointDeControle
    
    # Intervention de maintenance préventive
    intervention, created = Intervention.objects.get_or_create(
        nom='Maintenance préventive pompe centrifuge',
        defaults={
            'description': 'Contrôle et maintenance préventive standard pour pompes centrifuges',
            'statut': 'VALIDATED',
            'duree_estimee_heures': 2,
            'techniciens_requis': 1
        }
    )
    
    if created:
        # Opération 1: Contrôles visuels
        op1 = Operation.objects.create(
            intervention=intervention,
            nom='Contrôles visuels et préparatifs',
            ordre=1
        )
        
        points_op1 = [
            {
                'label': 'Arrêt et consignation effectués',
                'type_champ': 'BOOLEAN',
                'aide': 'Vérifier que la pompe est bien arrêtée et consignée selon les procédures',
                'est_obligatoire': True,
                'ordre': 1
            },
            {
                'label': 'État général de la pompe',
                'type_champ': 'SELECT',
                'options': 'Excellent;Bon;Correct;Dégradé;Mauvais',
                'aide': 'Évaluer l\'état visuel général de la pompe',
                'est_obligatoire': True,
                'ordre': 2,
                'permettre_photo': True
            },
            {
                'label': 'Présence de fuites',
                'type_champ': 'BOOLEAN',
                'aide': 'Vérifier la présence de fuites d\'huile ou d\'eau',
                'est_obligatoire': True,
                'ordre': 3,
                'permettre_photo': True
            }
        ]
        
        for point_data in points_op1:
            PointDeControle.objects.create(operation=op1, **point_data)
        
        # Opération 2: Contrôles mécaniques
        op2 = Operation.objects.create(
            intervention=intervention,
            nom='Contrôles mécaniques',
            ordre=2
        )
        
        points_op2 = [
            {
                'label': 'Niveau d\'huile du réducteur',
                'type_champ': 'SELECT',
                'options': 'Correct;Insuffisant;Excessif',
                'aide': 'Contrôler le niveau d\'huile via le voyant',
                'est_obligatoire': True,
                'ordre': 1
            },
            {
                'label': 'Température des paliers (°C)',
                'type_champ': 'NUMBER',
                'aide': 'Mesurer la température avec un thermomètre infrarouge',
                'est_obligatoire': True,
                'ordre': 2
            },
            {
                'label': 'Jeu de l\'accouplement (mm)',
                'type_champ': 'NUMBER',
                'aide': 'Mesurer le jeu axial de l\'accouplement avec un comparateur',
                'est_obligatoire': False,
                'ordre': 3
            },
            {
                'label': 'Observations complémentaires',
                'type_champ': 'TEXTAREA',
                'aide': 'Noter toute observation particulière',
                'est_obligatoire': False,
                'ordre': 4,
                'permettre_audio': True
            }
        ]
        
        for point_data in points_op2:
            PointDeControle.objects.create(operation=op2, **point_data)
        
        # Opération 3: Finalisation
        op3 = Operation.objects.create(
            intervention=intervention,
            nom='Nettoyage et remise en service',
            ordre=3
        )
        
        points_op3 = [
            {
                'label': 'Nettoyage effectué',
                'type_champ': 'BOOLEAN',
                'aide': 'Nettoyer la pompe et son environnement',
                'est_obligatoire': True,
                'ordre': 1
            },
            {
                'label': 'Test de fonctionnement',
                'type_champ': 'SELECT',
                'options': 'Réussi;Échec;Non effectué',
                'aide': 'Tester le fonctionnement après maintenance',
                'est_obligatoire': True,
                'ordre': 2
            },
            {
                'label': 'Date de prochaine maintenance',
                'type_champ': 'DATE',
                'aide': 'Programmer la prochaine maintenance préventive',
                'est_obligatoire': False,
                'ordre': 3
            }
        ]
        
        for point_data in points_op3:
            PointDeControle.objects.create(operation=op3, **point_data)
        
        print("✓ Intervention d'exemple créée avec 3 opérations et 10 points de contrôle")
    else:
        print("✓ Intervention d'exemple existe déjà")

def main():
    """Fonction principale"""
    print("🔧 Configuration de GMOA - Système de Gestion de Maintenance")
    print("=" * 60)
    
    # Vérification de l'emplacement
    if not os.path.exists('manage.py'):
        print("❌ ERREUR: manage.py non trouvé !")
        print("📁 Assurez-vous d'être dans le répertoire racine du projet GMOA")
        print("📁 (même niveau que manage.py)")
        sys.exit(1)
    
    # Configuration Django
    setup_django()
    
    # Migrations
    print("\n📋 Application des migrations...")
    try:
        execute_from_command_line(['manage.py', 'makemigrations', 'core'])
        execute_from_command_line(['manage.py', 'migrate'])
        print("✓ Migrations appliquées")
    except Exception as e:
        print(f"❌ Erreur lors des migrations: {e}")
        sys.exit(1)
    
    # Création des données
    print("\n👥 Création des utilisateurs...")
    create_superuser()
    create_test_users()
    
    print("\n🏗️ Création des données de base...")
    create_basic_data()
    
    print("\n🔧 Création de l'intervention d'exemple...")
    create_sample_intervention()
    
    print("\n" + "=" * 60)
    print("✅ Configuration terminée avec succès !")
    print("\n📋 Récapitulatif des comptes créés :")
    print("   • admin/admin123 (Administrateur)")
    print("   • technicien1/tech123 (Technicien)")
    print("   • manager1/manager123 (Manager)")
    print("   • operateur1/oper123 (Opérateur)")
    print("\n🚀 Vous pouvez maintenant démarrer le serveur avec :")
    print("   python manage.py runserver")
    print("\n🌐 Puis accéder à l'application sur :")
    print("   http://127.0.0.1:8000")

if __name__ == '__main__':
    main()