#!/usr/bin/env python3
"""
Script de migration pour appliquer le nouveau workflow Manager/Technicien
à votre projet GMOA existant.

UTILISATION:
    python migration_workflow.py
"""

import os
import sys
import django
from django.core.management import execute_from_command_line

def setup_django():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gmao_project.settings')
    django.setup()

def update_permissions():
    from django.contrib.auth.models import User
    from core.models import ProfilUtilisateur

    print("\n🔐 Mise à jour des permissions utilisateurs...")
    users_without_profile = User.objects.filter(profil__isnull=True)
    for user in users_without_profile:
        if user.is_superuser:
            role = 'ADMIN'
        elif user.is_staff:
            role = 'MANAGER'
        else:
            role = 'TECHNICIEN'
        ProfilUtilisateur.objects.create(user=user, role=role)
        print(f"✓ Profil créé pour {user.username} avec le rôle {role}")

def create_demo_intervention():
    from core.models import Intervention, Operation, PointDeControle

    print("\n🔧 Création d'une intervention de démonstration complète...")
    intervention, created = Intervention.objects.get_or_create(
        nom='Maintenance complète pompe industrielle',
        defaults={
            'description': 'Intervention complète de maintenance préventive avec contrôles approfondis comme dans Kezeo',
            'statut': 'VALIDATED',
            'duree_estimee_heures': 4,
            'techniciens_requis': 2
        }
    )

    if created:
        # Opération 1
        op1 = Operation.objects.create(intervention=intervention, nom='Préparation et mise en sécurité', ordre=1)
        points_op1 = [
            {
                'label': 'Vérifier que l\'équipement est bien consigné électriquement',
                'type_champ': 'BOOLEAN',
                'aide': 'Consignation confirmée par l\'opérateur',
                'est_obligatoire': True,
                'ordre': 1
            },
            {
                'label': 'EPI complets portés',
                'type_champ': 'BOOLEAN',
                'aide': 'Casque, gants, chaussures de sécurité, lunettes',
                'est_obligatoire': True,
                'ordre': 2
            },
            {
                'label': 'Zone de travail balisée',
                'type_champ': 'SELECT',
                'options': 'Conforme;Non conforme;Non applicable',
                'aide': 'Vérifier le balisage de la zone d\'intervention',
                'est_obligatoire': True,
                'ordre': 3,
                'permettre_photo': True
            },
            {
                'label': 'Outillage vérifié',
                'type_champ': 'TEXTAREA',
                'aide': 'Lister les outils utilisés et leur état',
                'est_obligatoire': False,
                'ordre': 4
            }
        ]
        for point_data in points_op1:
            PointDeControle.objects.create(operation=op1, **point_data)

        # Opération 2
        op2 = Operation.objects.create(intervention=intervention, nom='Contrôles visuels et inspection', ordre=2)
        points_op2 = [
            {
                'label': 'État général de la pompe',
                'type_champ': 'SELECT',
                'options': 'Excellent;Bon;Correct;Dégradé;Mauvais',
                'aide': 'Évaluation visuelle globale',
                'est_obligatoire': True,
                'ordre': 1,
                'permettre_photo': True
            },
            {
                'label': 'Présence de fuites',
                'type_champ': 'SELECT',
                'options': 'Aucune fuite;Fuite mineure;Fuite importante;Fuite critique',
                'aide': 'Contrôle des étanchéités',
                'est_obligatoire': True,
                'ordre': 2,
                'permettre_photo': True
            },
            {
                'label': 'État des raccords et boulonnerie',
                'type_champ': 'SELECT',
                'options': 'Conforme;Non conforme;À surveiller',
                'aide': 'Vérification du serrage et de l\'état',
                'est_obligatoire': True,
                'ordre': 3
            },
            {
                'label': 'Observations particulières',
                'type_champ': 'TEXTAREA',
                'aide': 'Noter toute anomalie observée',
                'est_obligatoire': False,
                'ordre': 4,
                'permettre_audio': True,
                'permettre_photo': True
            }
        ]
        for point_data in points_op2:
            PointDeControle.objects.create(operation=op2, **point_data)

        # Opération 3
        op3 = Operation.objects.create(intervention=intervention, nom='Mesures et contrôles techniques', ordre=3)
        points_op3 = [
            {
                'label': 'Température des paliers (°C)',
                'type_champ': 'NUMBER',
                'aide': 'Mesure au thermomètre infrarouge - Limite: 60°C',
                'est_obligatoire': True,
                'ordre': 1
            },
            {
                'label': 'Vibrations (mm/s)',
                'type_champ': 'NUMBER',
                'aide': 'Mesure vibratoire - Limite: 4.5 mm/s',
                'est_obligatoire': True,
                'ordre': 2
            },
            {
                'label': 'Niveau d\'huile réducteur',
                'type_champ': 'SELECT',
                'options': 'Correct;Insuffisant;Excessif;À remplacer',
                'aide': 'Contrôle visuel par voyant',
                'est_obligatoire': True,
                'ordre': 3
            },
            {
                'label': 'Qualité de l\'huile',
                'type_champ': 'SELECT',
                'options': 'Excellente;Bonne;Correcte;Dégradée;À changer',
                'aide': 'Aspect visuel et consistance',
                'est_obligatoire': True,
                'ordre': 4
            },
            {
                'label': 'Pression de service (bar)',
                'type_champ': 'NUMBER',
                'aide': 'Relevé manomètre - Pression nominale: 6 bar',
                'est_obligatoire': True,
                'ordre': 5
            },
            {
                'label': 'Intensité moteur (A)',
                'type_champ': 'NUMBER',
                'aide': 'Mesure à la pince ampèremétrique',
                'est_obligatoire': False,
                'ordre': 6
            }
        ]
        for point_data in points_op3:
            PointDeControle.objects.create(operation=op3, **point_data)

        # Opération 4
        op4 = Operation.objects.create(intervention=intervention, nom='Actions de maintenance', ordre=4)
        points_op4 = [
            {
                'label': 'Graissage des roulements effectué',
                'type_champ': 'BOOLEAN',
                'aide': 'Selon plan de lubrification',
                'est_obligatoire': True,
                'ordre': 1
            },
            {
                'label': 'Type de graisse utilisée',
                'type_champ': 'TEXT',
                'aide': 'Référence du lubrifiant utilisé',
                'est_obligatoire': False,
                'ordre': 2
            },
            {
                'label': 'Resserrage boulonnerie',
                'type_champ': 'SELECT',
                'options': 'Effectué;Non nécessaire;Reporté',
                'aide': 'Selon couple de serrage',
                'est_obligatoire': True,
                'ordre': 3
            },
            {
                'label': 'Pièces remplacées',
                'type_champ': 'TEXTAREA',
                'aide': 'Lister les pièces changées avec références',
                'est_obligatoire': False,
                'ordre': 4
            },
            {
                'label': 'Nettoyage effectué',
                'type_champ': 'SELECT',
                'options': 'Complet;Partiel;Non effectué',
                'aide': 'Nettoyage de l\'équipement et de son environnement',
                'est_obligatoire': True,
                'ordre': 5
            }
        ]
        for point_data in points_op4:
            PointDeControle.objects.create(operation=op4, **point_data)

        # Opération 5
        op5 = Operation.objects.create(intervention=intervention, nom='Tests et remise en service', ordre=5)
        points_op5 = [
            {
                'label': 'Test de fonctionnement à vide',
                'type_champ': 'SELECT',
                'options': 'Réussi;Échec;Anomalie détectée',
                'aide': 'Test sans charge pendant 5 minutes',
                'est_obligatoire': True,
                'ordre': 1
            },
            {
                'label': 'Test en charge normale',
                'type_champ': 'SELECT',
                'options': 'Réussi;Échec;Anomalie détectée',
                'aide': 'Test avec charge nominale pendant 10 minutes',
                'est_obligatoire': True,
                'ordre': 2
            },
            {
                'label': 'Vibrations après remise en service (mm/s)',
                'type_champ': 'NUMBER',
                'aide': 'Nouvelle mesure après maintenance',
                'est_obligatoire': True,
                'ordre': 3
            },
            {
                'label': 'Date de prochaine intervention',
                'type_champ': 'DATE',
                'aide': 'Programmer la prochaine maintenance préventive',
                'est_obligatoire': True,
                'ordre': 4
            },
            {
                'label': 'Équipement remis en service',
                'type_champ': 'BOOLEAN',
                'aide': 'Confirmer la remise en service opérationnelle',
                'est_obligatoire': True,
                'ordre': 5
            },
            {
                'label': 'Commentaires finaux',
                'type_champ': 'TEXTAREA',
                'aide': 'Bilan global de l\'intervention, recommandations',
                'est_obligatoire': False,
                'ordre': 6,
                'permettre_audio': True
            }
        ]
        for point_data in points_op5:
            PointDeControle.objects.create(operation=op5, **point_data)

        print(f"✓ Intervention complète créée : '{intervention.nom}'")
    else:
        print("✓ Intervention de démonstration existe déjà")

def create_sample_ordre_travail():
    from core.models import OrdreDeTravail, Asset, Intervention, StatutWorkflow, RapportExecution
    from django.contrib.auth.models import User

    print("\n📋 Création d'un ordre de travail d'exemple...")
    intervention = Intervention.objects.filter(statut='VALIDATED').first()
    asset = Asset.objects.first()
    manager = User.objects.filter(profil__role='MANAGER').first()
    technicien = User.objects.filter(profil__role='TECHNICIEN').first()
    statut = StatutWorkflow.objects.filter(nom='NOUVEAU').first()

    if intervention and asset and manager:
        from django.utils import timezone
        ordre, created = OrdreDeTravail.objects.get_or_create(
            titre=f'Maintenance préventive - {asset.nom}',
            defaults={
                'type_OT': 'PREVENTIVE',
                'intervention': intervention,
                'asset': asset,
                'cree_par': manager,
                'assigne_a_technicien': technicien,
                'statut': statut,
                'priorite': 2,
                'date_prevue_debut': timezone.now() + timezone.timedelta(days=1)
            }
        )
        if created:
            RapportExecution.objects.create(ordre_de_travail=ordre, cree_par=manager)
            print(f"✓ Ordre de travail créé : OT-{ordre.id}")
        else:
            print("✓ Ordre de travail d'exemple existe déjà")

def main():
    print("🔄 Migration vers le workflow Manager/Technicien")
    print("=" * 60)

    if not os.path.exists('manage.py'):
        print("❌ ERREUR: manage.py non trouvé !")
        sys.exit(1)

    setup_django()

    print("\n📋 Application des nouvelles migrations...")
    try:
        execute_from_command_line(['manage.py', 'makemigrations', 'core'])
        execute_from_command_line(['manage.py', 'migrate'])
        print("✓ Migrations appliquées")
    except Exception as e:
        print(f"❌ Erreur lors des migrations: {e}")

    update_permissions()
    create_demo_intervention()
    create_sample_ordre_travail()

    print("\n✅ Migration terminée avec succès !")

if __name__ == '__main__':
    main()
