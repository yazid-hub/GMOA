# core/forms.py - Version finale corrigée

from django import forms
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordChangeForm
from django.utils import timezone
from datetime import timedelta

from .models import (
    Intervention, Operation, PointDeControle, ProfilUtilisateur, 
    OrdreDeTravail, Asset, Equipe, StatutWorkflow, RapportExecution, 
    Reponse, ActionCorrective, CommentaireOT, CategorieAsset,
    PieceDetachee, Competence
)

# ==============================================================================
# FORMULAIRES POUR L'ARCHITECTURE DES INTERVENTIONS
# ==============================================================================

class InterventionForm(forms.ModelForm):
    """Formulaire pour créer/modifier une intervention."""
    
    class Meta:
        model = Intervention
        fields = ['nom', 'description', 'statut', 'duree_estimee_heures', 'techniciens_requis']
        
        labels = {
            'nom': 'Nom de l\'intervention',
            'description': 'Description',
            'statut': 'Statut',
            'duree_estimee_heures': 'Durée estimée (heures)',
            'techniciens_requis': 'Techniciens requis',
        }
        
        widgets = {
            'nom': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Ex: Maintenance pompe centrifuge'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'rows': 3,
                'placeholder': 'Description détaillée de l\'intervention...'
            }),
            'statut': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'duree_estimee_heures': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'min': '0',
                'step': '0.5',
                'placeholder': '2.5'
            }),
            'techniciens_requis': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'min': '1',
                'placeholder': '1'
            }),
        }

class OperationForm(forms.ModelForm):
    """Formulaire pour créer/modifier une opération."""
    
    class Meta:
        model = Operation
        fields = ['nom', 'ordre']  # SEULEMENT ces champs existent dans le modèle
        
        labels = {
            'nom': 'Nom de l\'opération',
            'ordre': 'Ordre d\'exécution',
        }
        
        widgets = {
            'nom': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Ex: Contrôle visuel'
            }),
            'ordre': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'min': '1',
                'placeholder': '1'
            }),
        }

class PointDeControleForm(forms.ModelForm):
    """Formulaire pour créer/modifier un point de contrôle."""
    
    class Meta:
        model = PointDeControle
        fields = [
            'label', 'type_champ', 'aide', 'options', 'est_obligatoire',
            'ordre', 'permettre_photo', 'permettre_audio', 'permettre_video',
            'permettre_fichiers', 'depend_de', 'condition_affichage'
        ]
        
        labels = {
            'label': 'Libellé du point de contrôle',
            'type_champ': 'Type de champ',
            'aide': 'Aide/Instructions',
            'options': 'Options (séparées par ;)',
            'est_obligatoire': 'Obligatoire',
            'ordre': 'Ordre',
            'permettre_photo': 'Autoriser photos',
            'permettre_audio': 'Autoriser audio',
            'permettre_video': 'Autoriser vidéo',
            'permettre_fichiers': 'Autoriser fichiers',
            'depend_de': 'Dépend du point',
            'condition_affichage': 'Condition d\'affichage',
        }
        
        widgets = {
            'label': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Ex: Niveau d\'huile conforme'
            }),
            'type_champ': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'aide': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'rows': 2,
                'placeholder': 'Instructions pour l\'utilisateur...'
            }),
            'options': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'rows': 2,
                'placeholder': 'Ex: Conforme;Non conforme;À vérifier'
            }),
            'ordre': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'min': '1'
            }),
            'depend_de': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'condition_affichage': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Ex: OUI, > 5, CONFORME'
            }),
            'est_obligatoire': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'
            }),
            'permettre_photo': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'
            }),
            'permettre_audio': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'
            }),
            'permettre_video': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'
            }),
            'permettre_fichiers': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'
            }),
        }

# ==============================================================================
# FORMULAIRES POUR LES ORDRES DE TRAVAIL
# ==============================================================================

class OrdreDeTravailForm(forms.ModelForm):
    """Formulaire pour créer un ordre de travail."""
    
    class Meta:
        model = OrdreDeTravail
        fields = [
            'titre', 'description_detaillee', 'asset', 'intervention', 'type_OT', 
            'priorite', 'date_prevue_debut', 'assigne_a_technicien', 'assigne_a_equipe'
        ]
        
        labels = {
            'titre': 'Titre',
            'description_detaillee': 'Description détaillée',
            'asset': 'Asset concerné',
            'intervention': 'Intervention',
            'type_OT': 'Type d\'ordre de travail',
            'priorite': 'Priorité',
            'date_prevue_debut': 'Date prévue de début',
            'assigne_a_technicien': 'Technicien assigné',
            'assigne_a_equipe': 'Équipe assignée',
        }
        
        widgets = {
            'titre': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Ex: Maintenance pompe P-101'
            }),
            'description_detaillee': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'rows': 3,
                'placeholder': 'Description détaillée de l\'ordre de travail...'
            }),
            'asset': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'intervention': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'type_OT': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'priorite': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'date_prevue_debut': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'assigne_a_technicien': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'assigne_a_equipe': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
        }

class OrdreDeTravailEditForm(forms.ModelForm):
    """Formulaire pour modifier un ordre de travail existant."""
    
    class Meta:
        model = OrdreDeTravail
        fields = [
            'titre', 'description_detaillee', 'type_OT', 'priorite', 
            'date_prevue_debut', 'assigne_a_technicien', 'assigne_a_equipe', 'statut'
        ]
        
        labels = {
            'titre': 'Titre',
            'description_detaillee': 'Description détaillée',
            'type_OT': 'Type d\'ordre de travail',
            'priorite': 'Priorité',
            'date_prevue_debut': 'Date prévue de début',
            'assigne_a_technicien': 'Technicien assigné',
            'assigne_a_equipe': 'Équipe assignée',
            'statut': 'Statut',
        }
        
        widgets = {
            'titre': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'description_detaillee': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'rows': 3,
                'placeholder': 'Description détaillée...'
            }),
            'type_OT': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'priorite': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'date_prevue_debut': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'assigne_a_technicien': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'assigne_a_equipe': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'statut': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Formater la date pour le champ datetime-local
        if self.instance and self.instance.date_prevue_debut:
            # Convertir au format requis par datetime-local : YYYY-MM-DDTHH:MM
            self.initial['date_prevue_debut'] = self.instance.date_prevue_debut.strftime('%Y-%m-%dT%H:%M')
# ==============================================================================
# FORMULAIRES POUR LES ASSETS
# ==============================================================================

class AssetForm(forms.ModelForm):
    """Formulaire pour créer/modifier un asset."""
    
    class Meta:
        model = Asset
        fields = [
            'nom', 'reference', 'categorie', 'marque', 'modele', 'statut',
            'criticite', 'localisation_texte', 'latitude', 'longitude',
            'adresse_complete', 'nb_fibres_total', 'nb_fibres_utilisees',
            'niveau_hierarchique', 'type_connecteur'
        ]
        
        labels = {
            'nom': 'Nom',
            'reference': 'Référence',
            'categorie': 'Catégorie',
            'marque': 'Marque',
            'modele': 'Modèle',
            'statut': 'Statut',
            'criticite': 'Criticité',
            'localisation_texte': 'Localisation',
            'latitude': 'Latitude',
            'longitude': 'Longitude',
            'adresse_complete': 'Adresse complète',
            'nb_fibres_total': 'Nb fibres total',
            'nb_fibres_utilisees': 'Nb fibres utilisées',
            'niveau_hierarchique': 'Niveau hiérarchique',
            'type_connecteur': 'Type de connecteur',
        }
        
        widgets = {
            'nom': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Ex: Pompe centrifuge P-101'
            }),
            'reference': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Ex: P-101'
            }),
            'categorie': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'marque': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'modele': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'statut': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'criticite': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'localisation_texte': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Ex: Bâtiment A - Niveau 1'
            }),
            'latitude': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'step': 'any',
                'placeholder': '48.8566'
            }),
            'longitude': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'step': 'any',
                'placeholder': '2.3522'
            }),
            'adresse_complete': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'rows': 2,
                'placeholder': 'Adresse complète...'
            }),
            'nb_fibres_total': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'min': '0'
            }),
            'nb_fibres_utilisees': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'min': '0'
            }),
            'niveau_hierarchique': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'min': '1',
                'max': '4'
            }),
            'type_connecteur': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
        }

# ==============================================================================
# FORMULAIRES POUR LES PROFILS UTILISATEURS
# ==============================================================================

class ProfilUtilisateurForm(forms.ModelForm):
    """Formulaire pour créer/modifier un profil utilisateur."""
    
    class Meta:
        model = ProfilUtilisateur
        fields = ['role', 'telephone']  # SEULEMENT les vrais champs du modèle
        
        labels = {
            'role': 'Rôle',
            'telephone': 'Téléphone',
        }
        
        widgets = {
            'role': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'telephone': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': '+33 1 23 45 67 89'
            }),
        }

class UserUpdateForm(forms.ModelForm):
    """Formulaire pour modifier les informations utilisateur."""
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        
        labels = {
            'first_name': 'Prénom',
            'last_name': 'Nom',
            'email': 'Email',
        }
        
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
        }

class CustomPasswordChangeForm(PasswordChangeForm):
    """Formulaire personnalisé pour le changement de mot de passe."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Personnalisation des labels
        self.fields['old_password'].label = 'Ancien mot de passe'
        self.fields['new_password1'].label = 'Nouveau mot de passe'
        self.fields['new_password2'].label = 'Confirmation du nouveau mot de passe'
        
        # Ajout des classes CSS
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            })

# ==============================================================================
# FORMULAIRES POUR LES COMMENTAIRES ET ACTIONS
# ==============================================================================

class CommentaireOTForm(forms.ModelForm):
    """Formulaire pour ajouter un commentaire à un ordre de travail."""
    
    class Meta:
        model = CommentaireOT
        fields = ['contenu']
        
        labels = {
            'contenu': 'Commentaire',
        }
        
        widgets = {
            'contenu': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'rows': 3,
                'placeholder': 'Ajouter un commentaire...'
            }),
        }

class ActionCorrectiveForm(forms.ModelForm):
    """Formulaire pour créer une action corrective."""
    
    class Meta:
        model = ActionCorrective
        fields = ['titre', 'description', 'priorite', 'assigne_a', 'date_echeance']
        
        labels = {
            'titre': 'Titre',
            'description': 'Description',
            'priorite': 'Priorité',
            'assigne_a': 'Assigné à',
            'date_echeance': 'Date d\'échéance',
        }
        
        widgets = {
            'titre': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Titre de l\'action corrective'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'rows': 3,
                'placeholder': 'Description détaillée de l\'action à entreprendre...'
            }),
            'priorite': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'assigne_a': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'date_echeance': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
        }

# ==============================================================================
# FORMULAIRES POUR L'EXÉCUTION DES INTERVENTIONS
# ==============================================================================

class ReponseForm(forms.ModelForm):
    """Formulaire pour saisir une réponse à un point de contrôle."""
    
    class Meta:
        model = Reponse
        fields = ['valeur']  # Le modèle Reponse n'a qu'un champ 'valeur'
        
        labels = {
            'valeur': 'Réponse',
        }
        
        widgets = {
            'valeur': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'rows': 3,
                'placeholder': 'Saisir la réponse...'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        point_controle = kwargs.pop('point_controle', None)
        super().__init__(*args, **kwargs)
        
        if point_controle:
            # Adapter le widget selon le type de point de contrôle
            if point_controle.type_champ == 'TEXT':
                self.fields['valeur'].widget = forms.TextInput(attrs={
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
                })
            elif point_controle.type_champ == 'NUMBER':
                self.fields['valeur'].widget = forms.NumberInput(attrs={
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
                })
            elif point_controle.type_champ == 'BOOLEAN':
                self.fields['valeur'].widget = forms.Select(choices=[
                    ('', '-- Choisir --'),
                    ('OUI', 'Oui'),
                    ('NON', 'Non')
                ], attrs={
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
                })
            elif point_controle.type_champ == 'SELECT' and point_controle.options:
                choices = [('', '-- Choisir --')]
                for option in point_controle.options.split(';'):
                    choices.append((option.strip(), option.strip()))
                self.fields['valeur'].widget = forms.Select(choices=choices, attrs={
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
                })
            elif point_controle.type_champ == 'DATE':
                self.fields['valeur'].widget = forms.DateInput(attrs={
                    'type': 'date',
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
                })