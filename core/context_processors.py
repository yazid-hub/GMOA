from .views import get_user_role  # Importez votre fonction existante

def user_role_context(request):
    """
    Context processor pour ajouter user_role dans tous les templates
    Cette fonction sera appelée automatiquement pour chaque requête
    """
    context = {}
    
    if request.user.is_authenticated:
        try:
            context['user_role'] = get_user_role(request.user)
        except Exception as e:
            # En cas d'erreur, on définit un rôle par défaut
            context['user_role'] = 'VIEWER'
    else:
        context['user_role'] = None
    
    return context