# Fichier : core/templatetags/custom_filters.py

from django import template
import os
register = template.Library()

@register.filter
def split(value, delimiter):
    """Divise une chaîne par un délimiteur"""
    if value:
        return value.split(delimiter)
    return []

@register.filter
def get_item(dictionary, key):
    """Récupère un élément d'un dictionnaire par sa clé"""
    if dictionary and key is not None:
        # Convertir la clé en entier si nécessaire
        try:
            if isinstance(key, str):
                key = int(key)
            return dictionary.get(key, '')
        except (ValueError, TypeError):
            return dictionary.get(key, '') if hasattr(dictionary, 'get') else ''
    return ''

@register.filter
def range_filter(value):
    """Crée une liste d'entiers de 0 à value-1"""
    try:
        return range(int(value))
    except (ValueError, TypeError):
        return []

@register.filter
def priority_class(priority):
    """Retourne une classe CSS selon la priorité"""
    classes = {
        1: 'bg-green-100 text-green-800',
        2: 'bg-yellow-100 text-yellow-800', 
        3: 'bg-orange-100 text-orange-800',
        4: 'bg-red-100 text-red-800'
    }
    return classes.get(priority, 'bg-gray-100 text-gray-800')

@register.filter
def priority_text(priority):
    """Retourne le texte de priorité"""
    texts = {
        1: 'Basse',
        2: 'Normale',
        3: 'Haute', 
        4: 'Urgente'
    }
    return texts.get(priority, 'Inconnue')

@register.filter
def mul(value, arg):
    """Multiplie deux valeurs"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def div(value, arg):
    """Divise deux valeurs"""
    try:
        return float(value) / float(arg)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0

@register.filter
def sub(value, arg):
    """Soustrait deux valeurs"""
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return 0
    
@register.filter
def replace(value, arg):
    """Remplace des caractères dans une chaîne"""
    if value and arg:
        try:
            old, new = arg.split(',')
            return value.replace(old, new)
        except ValueError:
            return value
    return value


@register.filter
def options_list(point):
    """
    Convertit les options d'un point de contrôle en liste
    Les options sont stockées sous forme de texte séparé par des points-virgules
    """
    if not point or not hasattr(point, 'options') or not point.options:
        return []
    
    # Séparer par point-virgule et nettoyer les espaces
    options = [option.strip() for option in point.options.split(';') if option.strip()]
    return options

@register.filter  
def truncatechars(value, length):
    """Tronque un texte à un nombre de caractères donné"""
    if not value:
        return ""
    
    length = int(length)
    if len(value) <= length:
        return value
    
    return value[:length-3] + "..."

@register.filter
def is_image(media):
    """Vérifie si un média est une image"""
    if not media:
        return False
    
    # Vérifier par type de fichier
    if hasattr(media, 'type_fichier') and media.type_fichier == 'PHOTO':
        return True
        
    # Vérifier par extension
    if hasattr(media, 'nom_original') and media.nom_original:
        extensions_images = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']
        ext = os.path.splitext(media.nom_original)[1].lower()
        return ext in extensions_images
    
    return False

@register.filter
def is_video(media):
    """Vérifie si un média est une vidéo"""
    if not media:
        return False
    
    # Vérifier par type de fichier
    if hasattr(media, 'type_fichier') and media.type_fichier == 'VIDEO':
        return True
        
    # Vérifier par extension
    if hasattr(media, 'nom_original') and media.nom_original:
        extensions_videos = ['.mp4', '.avi', '.mov', '.wmv', '.webm', '.mkv']
        ext = os.path.splitext(media.nom_original)[1].lower()
        return ext in extensions_videos
    
    return False

@register.filter
def is_audio(media):
    """Vérifie si un média est un audio"""
    if not media:
        return False
    
    # Vérifier par type de fichier
    if hasattr(media, 'type_fichier') and media.type_fichier == 'AUDIO':
        return True
        
    # Vérifier par extension
    if hasattr(media, 'nom_original') and media.nom_original:
        extensions_audios = ['.mp3', '.wav', '.aac', '.m4a', '.ogg', '.flac']
        ext = os.path.splitext(media.nom_original)[1].lower()
        return ext in extensions_audios
    
    return False

@register.filter
def format_file_size(size_bytes):
    """Formate la taille d'un fichier en unités lisibles"""
    if not size_bytes:
        return "0 B"
    
    try:
        size_bytes = int(size_bytes)
    except (ValueError, TypeError):
        return "N/A"
    
    if size_bytes == 0:
        return "0 B"
    
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    unit_index = 0
    size = float(size_bytes)
    
    while size >= 1024.0 and unit_index < len(units) - 1:
        size /= 1024.0
        unit_index += 1
    
    return f"{size:.1f} {units[unit_index]}"

@register.filter
def get_file_extension(filename):
    """Récupère l'extension d'un fichier"""
    if not filename:
        return ""
    return os.path.splitext(filename)[1][1:].upper()

@register.filter
def pluralize(value):
    """Ajoute un 's' si la valeur est supérieure à 1"""
    try:
        return "s" if int(value) > 1 else ""
    except (ValueError, TypeError):
        return ""

@register.filter
def default_if_none(value, default):
    """Retourne une valeur par défaut si la valeur est None"""
    return default if value is None else value