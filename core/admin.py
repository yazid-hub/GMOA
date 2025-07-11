from django.contrib import admin
from .models import (
    ProfilUtilisateur, Competence, UtilisateurCompetence, Equipe,
    CategorieAsset, Asset, AttributPersonnaliseAsset, PieceDetachee,
    Intervention, Operation, PointDeControle, StatutWorkflow,
    PlanMaintenancePreventive, OrdreDeTravail, RapportExecution,
    MouvementStock, Reponse, FichierMedia, ActionCorrective,
    CommentaireOT, Notification, ParametreGlobal, ParametreUtilisateur,
)

# Enregistrement de tous les modèles
admin.site.register(ProfilUtilisateur)
admin.site.register(Competence)
admin.site.register(UtilisateurCompetence)
admin.site.register(Equipe)
admin.site.register(CategorieAsset)
admin.site.register(Asset)
admin.site.register(AttributPersonnaliseAsset)
admin.site.register(PieceDetachee)
admin.site.register(Intervention)
admin.site.register(Operation)
admin.site.register(PointDeControle)
admin.site.register(StatutWorkflow)
admin.site.register(PlanMaintenancePreventive)
admin.site.register(OrdreDeTravail)
admin.site.register(RapportExecution)
admin.site.register(MouvementStock)
admin.site.register(Reponse)
admin.site.register(FichierMedia)
admin.site.register(ActionCorrective)
admin.site.register(CommentaireOT)
admin.site.register(Notification)
admin.site.register(ParametreGlobal)
admin.site.register(ParametreUtilisateur)