# Fichier : core/forms.py - Version Corrigée et Complète

from django import forms
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.forms import PasswordChangeForm

from .models import (
    Intervention, Operation, PointDeControle, ProfilUtilisateur, 
    OrdreDeTravail, Asset, Equipe, StatutWorkflow, RapportExecution, 
    Reponse, ActionCorrective, CommentaireOT
)

# ==============================================================================
# FORMULAIRES POUR L'ARCHITECTURE DES INTERVENTIONS
# ==============================================================================

class InterventionForm(forms.ModelForm):
    class Meta:
        model = Intervention
        fields = ['nom', 'description', 'statut', 'duree_estimee_heures', 'techniciens_requis']
        
        labels = {
            'nom': _('Name'),
            'description': _('Description'),
            'statut': _('Status'),
            'duree_estimee_heures': _('Estimated duration (hours)'),
            'techniciens_requis': _('Required technicians'),
        }
        
        help_texts = {
            'description': _('Describe the general purpose of this intervention.'),
            'duree_estimee_heures': _('Estimated duration of the intervention in hours.'),
            'techniciens_requis': _('Number of technicians required.'),
        }
        
        widgets = {
            'nom': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Ex: Maintenance préventive pompe'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'rows': 3,
                'placeholder': 'Décrivez l\'objectif de cette intervention...'
            }),
            'statut': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'duree_estimee_heures': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'min': '1'
            }),
            'techniciens_requis': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'min': '1'
            }),
        }

class OperationForm(forms.ModelForm):
    class Meta:
        model = Operation
        fields = ['nom']
        labels = {
            'nom': _('Step Name'),
        }
        widgets = {
            'nom': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Ex: Vérification visuelle'
            }),
        }

class PointDeControleForm(forms.ModelForm):
    class Meta:
        model = PointDeControle
        fields = [
            'label', 'type_champ', 'aide', 'options', 'est_obligatoire',
            'permettre_photo', 'permettre_audio', 'permettre_video'
        ]
        labels = {
            'label': _('Label'),
            'type_champ': _('Field Type'),
            'aide': _('Help Text'),
            'options': _('Options'),
            'est_obligatoire': _('Required'),
            'permettre_photo': _('Allow Photos'),
            'permettre_audio': _('Allow Audio Comments'),
            'permettre_video': _('Allow Video Recording'),
        }
        help_texts = {
            'options': _('For lists, separate options with a semicolon (;).'),
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
        }

# ==============================================================================
# FORMULAIRES POUR LA GESTION DES UTILISATEURS
# ==============================================================================

class UserUpdateForm(forms.ModelForm):
    """Formulaire pour que l'utilisateur modifie ses informations de base."""
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        labels = {
            'first_name': _('First Name'),
            'last_name': _('Last Name'),
            'email': _('Email Address'),
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

class ProfilUtilisateurUpdateForm(forms.ModelForm):
    """Formulaire pour que l'utilisateur modifie les informations de son profil GMAO."""
    class Meta:
        model = ProfilUtilisateur
        fields = ['telephone']
        labels = {
            'telephone': _('Phone Number'),
        }
        widgets = {
            'telephone': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': '+33 1 23 45 67 89'
            }),
        }

class CustomPasswordChangeForm(PasswordChangeForm):
    """Formulaire personnalisé pour le changement de mot de passe."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Traduction des champs
        self.fields['old_password'].label = _("Ancien mot de passe")
        self.fields['new_password1'].label = _("Nouveau mot de passe")
        self.fields['new_password2'].label = _("Confirmation du nouveau mot de passe")
        
        # Ajout des classes CSS Tailwind
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            })

# ==============================================================================
# FORMULAIRES POUR LES ORDRES DE TRAVAIL
# ==============================================================================

class OrdreDeTravailForm(forms.ModelForm):
    """Formulaire pour la création d'ordres de travail."""
    
    class Meta:
        model = OrdreDeTravail
        fields = [
            'titre', 'description_detaillee', 'type_OT', 'intervention', 'asset', 'priorite',
            'date_prevue_debut', 'assigne_a_technicien', 'assigne_a_equipe'
        ]
        widgets = {
            'titre': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Ex: Maintenance préventive pompe A1'
            }),
            'description_detaillee': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Ex: la pompe ne fonctinne pas à cause de ...'
            }),
            'type_OT': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'intervention': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'asset': forms.Select(attrs={
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
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filtrer les interventions validées uniquement
        self.fields['intervention'].queryset = Intervention.objects.filter(
            statut='VALIDATED'
        ).order_by('nom')
        
        # Filtrer les assets en service ou en maintenance
        self.fields['asset'].queryset = Asset.objects.filter(
            statut__in=['EN_SERVICE', 'EN_MAINTENANCE']
        ).order_by('nom')
        
        # Filtrer les techniciens actifs
        self.fields['assigne_a_technicien'].queryset = User.objects.filter(
            profil__role='TECHNICIEN',
            is_active=True
        ).order_by('first_name', 'last_name')
        
        # Améliorer les labels
        self.fields['titre'].label = "Titre de l'intervention"
        self.fields['description_detaillee'].label = "Description detaillee"
        self.fields['type_OT'].label = "Type d'ordre de travail"
        self.fields['intervention'].label = "Intervention à réaliser"
        self.fields['asset'].label = "Équipement concerné"
        self.fields['priorite'].label = "Niveau de priorité"
        self.fields['date_prevue_debut'].label = "Date et heure prévues"
        self.fields['assigne_a_technicien'].label = "Technicien assigné"
        self.fields['assigne_a_equipe'].label = "Équipe assignée"
        
        # Ajouter des textes d'aide
        self.fields['titre'].help_text = "Donnez un titre descriptif et précis à votre ordre de travail"
        self.fields['intervention'].help_text = "Choisissez le type d'intervention selon la procédure définie"
        self.fields['asset'].help_text = "Sélectionnez l'équipement sur lequel intervenir"
        self.fields['date_prevue_debut'].help_text = "Planifiez quand cette intervention doit avoir lieu"
        self.fields['assigne_a_technicien'].help_text = "Optionnel: assignez un technicien spécifique"
        self.fields['assigne_a_equipe'].help_text = "Optionnel: assignez une équipe complète"
        
        # Rendre certains champs obligatoires
        self.fields['titre'].required = True
        self.fields['intervention'].required = True
        self.fields['asset'].required = True
        self.fields['date_prevue_debut'].required = True
        
        # Rendre l'assignation optionnelle
        self.fields['assigne_a_technicien'].required = False
        self.fields['assigne_a_equipe'].required = False
    
    def clean(self):
        """Validation personnalisée du formulaire."""
        cleaned_data = super().clean()
        
        # Vérifier qu'au moins un technicien ou une équipe est assignée
        technicien = cleaned_data.get('assigne_a_technicien')
        equipe = cleaned_data.get('assigne_a_equipe')
        
        if not technicien and not equipe:
            raise forms.ValidationError(
                "Vous devez assigner soit un technicien, soit une équipe à cet ordre de travail."
            )
        
        # Vérifier que la date n'est pas trop dans le passé
        date_prevue = cleaned_data.get('date_prevue_debut')
        if date_prevue and date_prevue < timezone.now() - timedelta(hours=1):
            raise forms.ValidationError(
                "La date prévue ne peut pas être antérieure à une heure."
            )
        
        return cleaned_data
    
    def save(self, commit=True):
        """Sauvegarde personnalisée avec calculs automatiques."""
        instance = super().save(commit=False)
        
        if commit:
            instance.save()
        
        return instance

class OrdreDeTravailEditForm(forms.ModelForm):
    """Formulaire pour la modification d'un Ordre de Travail existant."""
    
    class Meta:
        model = OrdreDeTravail
        fields = [
            'titre','description_detaillee', 'type_OT', 'priorite', 'date_prevue_debut',
            'assigne_a_technicien', 'assigne_a_equipe', 'statut'
        ]
        widgets = {
            'titre': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'description_detaillee': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Ex: Maintenance préventive pompe A1'
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
        labels = {
            'titre': _("Titre de l'Ordre de Travail"),
            'description_detaillee': _("Description detaillee l'Ordre de Travail"),
            'type_OT': _("Type d'Ordre de Travail"),
            'priorite': _('Priorité'),
            'date_prevue_debut': _('Date et heure prévues'),
            'assigne_a_technicien': _('Assigner à un technicien'),
            'assigne_a_equipe': _('Assigner à une équipe'),
            'statut': _("Statut de l'Ordre de Travail"),
        }

# ==============================================================================
# FORMULAIRES POUR L'EXÉCUTION DES INTERVENTIONS
# ==============================================================================

class ReponseForm(forms.ModelForm):
    """Formulaire pour saisir une réponse à un point de contrôle."""
    
    class Meta:
        model = Reponse
        fields = ['valeur']
        widgets = {
            'valeur': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
        }
    
    def __init__(self, *args, point_de_controle=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        if point_de_controle:
            self.point_de_controle = point_de_controle
            
            # Adapter le widget selon le type de champ
            if point_de_controle.type_champ == 'BOOLEAN':
                self.fields['valeur'].widget = forms.Select(
                    choices=[('', '-- Sélectionner --'), ('OUI', 'Oui'), ('NON', 'Non')],
                    attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'}
                )
            elif point_de_controle.type_champ == 'SELECT' and point_de_controle.options:
                choices = [('', '-- Sélectionner --')]
                for option in point_de_controle.options.split(';'):
                    if option.strip():
                        choices.append((option.strip(), option.strip()))
                self.fields['valeur'].widget = forms.Select(
                    choices=choices,
                    attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'}
                )
            elif point_de_controle.type_champ == 'NUMBER':
                self.fields['valeur'].widget = forms.NumberInput(attrs={
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
                })
            elif point_de_controle.type_champ == 'TEXTAREA':
                self.fields['valeur'].widget = forms.Textarea(attrs={
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                    'rows': 3
                })
            elif point_de_controle.type_champ == 'DATE':
                self.fields['valeur'].widget = forms.DateInput(attrs={
                    'type': 'date',
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
                })
            elif point_de_controle.type_champ == 'TIME':
                self.fields['valeur'].widget = forms.TimeInput(attrs={
                    'type': 'time',
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
                })
            elif point_de_controle.type_champ == 'DATETIME':
                self.fields['valeur'].widget = forms.DateTimeInput(attrs={
                    'type': 'datetime-local',
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
                })
            
            # Définir si le champ est obligatoire
            self.fields['valeur'].required = point_de_controle.est_obligatoire
            
            # Ajouter l'aide si disponible
            if point_de_controle.aide:
                self.fields['valeur'].help_text = point_de_controle.aide

class RapportExecutionForm(forms.ModelForm):
    """Formulaire pour créer/modifier un rapport d'exécution."""
    
    class Meta:
        model = RapportExecution
        fields = ['statut_rapport', 'date_execution_debut', 'date_execution_fin', 'commentaire_global']
        widgets = {
            'statut_rapport': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'date_execution_debut': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'date_execution_fin': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'commentaire_global': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'rows': 4,
                'placeholder': 'Commentaire général sur l\'intervention...'
            }),
        }
        labels = {
            'statut_rapport': 'Statut du rapport',
            'date_execution_debut': 'Date et heure de début',
            'date_execution_fin': 'Date et heure de fin',
            'commentaire_global': 'Commentaire général',
        }

class ActionCorrectiveForm(forms.ModelForm):
    """Formulaire pour créer une action corrective."""
    
    class Meta:
        model = ActionCorrective
        fields = ['titre', 'description', 'priorite', 'assigne_a', 'date_echeance']
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
        labels = {
            'titre': 'Titre',
            'description': 'Description',
            'priorite': 'Priorité',
            'assigne_a': 'Assigné à',
            'date_echeance': 'Date d\'échéance',
        }

class CommentaireOTForm(forms.ModelForm):
    """Formulaire pour ajouter un commentaire à un ordre de travail."""
    
    class Meta:
        model = CommentaireOT
        fields = ['contenu']
        widgets = {
            'contenu': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'rows': 3,
                'placeholder': 'Ajouter un commentaire...'
            }),
        }
        labels = {
            'contenu': 'Commentaire',
        }