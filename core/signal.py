from django.db.models.signals import post_save
from django.dispatch import receiver
import qrcode
from io import BytesIO
from django.core.files import File

@receiver(post_save, sender='core.Asset')
def generer_qr_code_asset(sender, instance, created, **kwargs):
    """
    Génère automatiquement un QR code pour chaque Asset créé
    """
    if created and not hasattr(instance, 'qr_code_image'):
        # Créer le QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        
        # URL ou données à encoder dans le QR code
        qr_data = f"ASSET-{instance.qr_code_identifier}"
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        # Créer l'image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Sauvegarder dans un buffer
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        # Créer le fichier Django
        filename = f"qr_asset_{instance.id}.png"
        if hasattr(instance, 'qr_code_image'):
            instance.qr_code_image.save(
                filename,
                File(buffer),
                save=False
            )
            instance.save(update_fields=['qr_code_image'])

# ==============================================================================
# MIGRATIONS À EXÉCUTER
# ==============================================================================

"""
Pour appliquer ces modifications, exécutez :

1. python manage.py makemigrations core --name "add_reparation_features"
2. python manage.py migrate

Les champs à ajouter aux modèles existants :

Dans PointDeControle :
- types_fichiers_autorises = models.CharField(max_length=255, blank=True, null=True)
- peut_demander_reparation = models.BooleanField(default=False)
- taille_max_fichier_mb = models.PositiveIntegerField(default=10)

Dans Asset :
- adresse_complete = models.TextField(blank=True, null=True)
- qr_code_image = models.ImageField(upload_to='qr_codes/', null=True, blank=True)
- manuel_technique = models.FileField(upload_to='manuels_techniques/', null=True, blank=True)
- derniere_maintenance = models.DateTimeField(null=True, blank=True)
- prochaine_maintenance = models.DateTimeField(null=True, blank=True)

Dans OrdreDeTravail :
- description_detaillee = models.TextField(blank=True, null=True)
- bloque_par_reparation = models.BooleanField(default=False)
"""