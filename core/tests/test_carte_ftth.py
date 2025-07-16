# Fichier: core/tests/test_carte_ftth.py

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.conf import settings
from decimal import Decimal
import json

from core.models import Asset, CategorieAsset
from core.views import validate_coordinates, calculate_map_center, prepare_asset_geojson


class ValidateCoordinatesTest(TestCase):
    """
    Tests pour la fonction validate_coordinates
    """
    
    def test_valid_coordinates(self):
        """Test des coordonnées valides"""
        # Coordonnées Paris
        self.assertTrue(validate_coordinates(48.8566, 2.3522))
        
        # Coordonnées Lyon
        self.assertTrue(validate_coordinates(45.7640, 4.8357))
        
        # Coordonnées avec Decimal
        self.assertTrue(validate_coordinates(Decimal('48.8566'), Decimal('2.3522')))
        
        # Limites GPS
        self.assertTrue(validate_coordinates(90.0, 180.0))
        self.assertTrue(validate_coordinates(-90.0, -180.0))

    def test_invalid_coordinates(self):
        """Test des coordonnées invalides"""
        # Coordonnées None
        self.assertFalse(validate_coordinates(None, None))
        self.assertFalse(validate_coordinates(48.8566, None))
        self.assertFalse(validate_coordinates(None, 2.3522))
        
        # Coordonnées (0,0)
        self.assertFalse(validate_coordinates(0, 0))
        
        # Hors limites GPS
        self.assertFalse(validate_coordinates(91.0, 2.3522))
        self.assertFalse(validate_coordinates(-91.0, 2.3522))
        self.assertFalse(validate_coordinates(48.8566, 181.0))
        self.assertFalse(validate_coordinates(48.8566, -181.0))
        
        # Types invalides
        self.assertFalse(validate_coordinates("invalid", "invalid"))
        self.assertFalse(validate_coordinates([], {}))
        
        # NaN values
        self.assertFalse(validate_coordinates(float('nan'), 2.3522))
        self.assertFalse(validate_coordinates(48.8566, float('nan')))


class CalculateMapCenterTest(TestCase):
    """
    Tests pour la fonction calculate_map_center
    """
    
    def setUp(self):
        """Création des données de test"""
        self.category = CategorieAsset.objects.create(nom='Test Category')
        
        # Assets avec coordonnées valides
        self.asset1 = Asset.objects.create(
            nom='Asset 1',
            latitude=48.8566,
            longitude=2.3522,
            categorie=self.category
        )
        
        self.asset2 = Asset.objects.create(
            nom='Asset 2',
            latitude=45.7640,
            longitude=4.8357,
            categorie=self.category
        )
        
        # Asset avec coordonnées invalides
        self.asset3 = Asset.objects.create(
            nom='Asset 3',
            latitude=0,
            longitude=0,
            categorie=self.category
        )

    def test_calculate_center_with_valid_assets(self):
        """Test du calcul de centre avec des assets valides"""
        assets = Asset.objects.filter(id__in=[self.asset1.id, self.asset2.id])
        
        center_lat, center_lng = calculate_map_center(assets)
        
        # Le centre devrait être entre Paris et Lyon
        self.assertAlmostEqual(center_lat, 47.31, places=1)
        self.assertAlmostEqual(center_lng, 3.59, places=1)

    def test_calculate_center_with_invalid_assets(self):
        """Test du calcul de centre avec des assets invalides"""
        assets = Asset.objects.filter(id=self.asset3.id)
        
        center_lat, center_lng = calculate_map_center(assets)
        
        # Devrait retourner les coordonnées par défaut
        default_center = {'lat': 46.603354, 'lng': 1.888334}
        self.assertEqual(center_lat, default_center['lat'])
        self.assertEqual(center_lng, default_center['lng'])

    def test_calculate_center_with_no_assets(self):
        """Test du calcul de centre sans assets"""
        assets = Asset.objects.none()
        
        center_lat, center_lng = calculate_map_center(assets)
        
        # Devrait retourner les coordonnées par défaut
        default_center = {'lat': 46.603354, 'lng': 1.888334}
        self.assertEqual(center_lat, default_center['lat'])
        self.assertEqual(center_lng, default_center['lng'])


class PrepareAssetGeoJsonTest(TestCase):
    """
    Tests pour la fonction prepare_asset_geojson
    """
    
    def setUp(self):
        """Création des données de test"""
        self.category = CategorieAsset.objects.create(nom='NRO')
        
        self.asset = Asset.objects.create(
            nom='Asset Test',
            reference='REF-001',
            latitude=48.8566,
            longitude=2.3522,
            categorie=self.category,
            statut='en_service',
            criticite=2
        )

    def test_prepare_valid_asset_geojson(self):
        """Test de préparation GeoJSON pour un asset valide"""
        feature = prepare_asset_geojson(self.asset)
        
        self.assertIsNotNone(feature)
        self.assertEqual(feature['type'], 'Feature')
        self.assertEqual(feature['geometry']['type'], 'Point')
        self.assertEqual(feature['geometry']['coordinates'], [2.3522, 48.8566])
        
        props = feature['properties']
        self.assertEqual(props['id'], self.asset.id)
        self.assertEqual(props['nom'], 'Asset Test')
        self.assertEqual(props['reference'], 'REF-001')
        self.assertEqual(props['categorie'], 'NRO')
        self.assertEqual(props['icon_type'], 'nro')

    def test_prepare_invalid_asset_geojson(self):
        """Test de préparation GeoJSON pour un asset invalide"""
        # Asset avec coordonnées invalides
        invalid_asset = Asset.objects.create(
            nom='Invalid Asset',
            latitude=0,
            longitude=0,
            categorie=self.category
        )
        
        feature = prepare_asset_geojson(invalid_asset)
        
        self.assertIsNone(feature)


class CarteFTTHViewTest(TestCase):
    """
    Tests pour la vue carte_ftth
    """
    
    def setUp(self):
        """Création des données de test"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')
        
        self.category = CategorieAsset.objects.create(nom='Test Category')
        
        # Assets de test
        self.asset1 = Asset.objects.create(
            nom='Asset 1',
            latitude=48.8566,
            longitude=2.3522,
            categorie=self.category,
            statut='en_service'
        )
        
        self.asset2 = Asset.objects.create(
            nom='Asset 2',
            latitude=0,
            longitude=0,
            categorie=self.category,
            statut='en_panne'
        )

    def test_carte_ftth_view_success(self):
        """Test du chargement réussi de la vue carte"""
        response = self.client.get(reverse('carte_ftth'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Carte FTTH')
        self.assertContains(response, 'assets_geojson')

    def test_carte_ftth_view_with_assets(self):
        """Test de la vue carte avec des assets"""
        response = self.client.get(reverse('carte_ftth'))
        
        self.assertEqual(response.status_code, 200)
        
        # Vérifier que les statistiques sont présentes
        self.assertContains(response, 'stats')
        
        # Vérifier que les assets valides sont dans le contexte
        self.assertIn('assets_valides', response.context)
        self.assertIn('assets_ignores', response.context)
        
        # Vérifier que seuls les assets valides sont comptés
        self.assertEqual(response.context['assets_valides'], 1)
        self.assertEqual(response.context['assets_ignores'], 1)

    def test_carte_ftth_view_unauthenticated(self):
        """Test de la vue carte sans authentification"""
        self.client.logout()
        response = self.client.get(reverse('carte_ftth'))
        
        # Devrait rediriger vers la page de connexion
        self.assertEqual(response.status_code, 302)


class AssetDetailsAjaxTest(TestCase):
    """
    Tests pour la vue asset_details_ajax
    """
    
    def setUp(self):
        """Création des données de test"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')
        
        self.category = CategorieAsset.objects.create(nom='Test Category')
        
        self.asset = Asset.objects.create(
            nom='Asset Test',
            reference='REF-001',
            latitude=48.8566,
            longitude=2.3522,
            categorie=self.category,
            statut='en_service'
        )

    def test_asset_details_ajax_success(self):
        """Test de récupération des détails d'un asset"""
        url = reverse('asset_details_ajax', kwargs={'asset_id': self.asset.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(data['asset']['id'], self.asset.id)
        self.assertEqual(data['asset']['nom'], 'Asset Test')

    def test_asset_details_ajax_not_found(self):
        """Test de récupération des détails d'un asset inexistant"""
        url = reverse('asset_details_ajax', kwargs={'asset_id': 99999})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 404)

    def test_asset_details_ajax_unauthenticated(self):
        """Test de la vue détails sans authentification"""
        self.client.logout()
        url = reverse('asset_details_ajax', kwargs={'asset_id': self.asset.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 302)


class ApiAssetsSearchTest(TestCase):
    """
    Tests pour la vue api_assets_search
    """
    
    def setUp(self):
        """Création des données de test"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')
        
        self.category = CategorieAsset.objects.create(nom='Test Category')
        
        self.asset1 = Asset.objects.create(
            nom='Asset Paris',
            reference='REF-001',
            latitude=48.8566,
            longitude=2.3522,
            categorie=self.category
        )
        
        self.asset2 = Asset.objects.create(
            nom='Asset Lyon',
            reference='REF-002',
            latitude=45.7640,
            longitude=4.8357,
            categorie=self.category
        )

    def test_search_assets_success(self):
        """Test de recherche d'assets avec succès"""
        url = reverse('api_assets_search')
        response = self.client.get(url, {'q': 'Paris'})
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(len(data['results']), 1)
        self.assertEqual(data['results'][0]['nom'], 'Asset Paris')

    def test_search_assets_short_query(self):
        """Test de recherche avec requête trop courte"""
        url = reverse('api_assets_search')
        response = self.client.get(url, {'q': 'A'})
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('trop courte', data['error'])

    def test_search_assets_no_results(self):
        """Test de recherche sans résultats"""
        url = reverse('api_assets_search')
        response = self.client.get(url, {'q': 'inexistant'})
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(len(data['results']), 0)


class IntegrationTest(TestCase):
    """
    Tests d'intégration pour l'ensemble de la fonctionnalité carte
    """
    
    def setUp(self):
        """Création d'un jeu de données complet"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')
        
        # Créer plusieurs catégories
        self.cat_nro = CategorieAsset.objects.create(nom='NRO')
        self.cat_pm = CategorieAsset.objects.create(nom='PM')
        
        # Créer plusieurs assets avec différents statuts
        self.assets = []
        coordinates = [
            (48.8566, 2.3522),   # Paris
            (45.7640, 4.8357),   # Lyon
            (43.2965, 5.3698),   # Marseille
            (0, 0),              # Invalide
            (None, None),        # Invalide
        ]
        
        statuts = ['en_service', 'en_panne', 'en_maintenance', 'hors_service', 'en_service']
        
        for i, ((lat, lng), statut) in enumerate(zip(coordinates, statuts)):
            asset = Asset.objects.create(
                nom=f'Asset {i+1}',
                reference=f'REF-{i+1:03d}',
                latitude=lat,
                longitude=lng,
                categorie=self.cat_nro if i % 2 == 0 else self.cat_pm,
                statut=statut
            )
            self.assets.append(asset)

    def test_complete_workflow(self):
        """Test du workflow complet"""
        # 1. Charger la carte
        response = self.client.get(reverse('carte_ftth'))
        self.assertEqual(response.status_code, 200)
        
        # Vérifier les statistiques
        self.assertEqual(response.context['assets_valides'], 3)  # 3 assets valides
        self.assertEqual(response.context['assets_ignores'], 2)  # 2 assets invalides
        
        # 2. Rechercher un asset
        search_response = self.client.get(reverse('api_assets_search'), {'q': 'Asset 1'})
        self.assertEqual(search_response.status_code, 200)
        
        search_data = json.loads(search_response.content)
        self.assertTrue(search_data['success'])
        self.assertEqual(len(search_data['results']), 1)
        
        # 3. Récupérer les détails de l'asset trouvé
        asset_id = search_data['results'][0]['id']
        details_response = self.client.get(reverse('asset_details_ajax', kwargs={'asset_id': asset_id}))
        self.assertEqual(details_response.status_code, 200)
        
        details_data = json.loads(details_response.content)
        self.assertTrue(details_data['success'])
        self.assertEqual(details_data['asset']['nom'], 'Asset 1')

    def test_error_handling(self):
        """Test de la gestion des erreurs"""
        # Test avec un asset inexistant
        response = self.client.get(reverse('asset_details_ajax', kwargs={'asset_id': 99999}))
        self.assertEqual(response.status_code, 404)
        
        # Test de recherche avec paramètres invalides
        response = self.client.get(reverse('api_assets_search'), {'q': ''})
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertFalse(data['success'])


class PerformanceTest(TestCase):
    """
    Tests de performance pour la carte FTTH
    """
    
    def setUp(self):
        """Création d'un grand nombre d'assets pour les tests de performance"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')
        
        self.category = CategorieAsset.objects.create(nom='Test Category')
        
        # Créer 1000 assets pour tester les performances
        assets_to_create = []
        for i in range(1000):
            # Coordonnées aléatoires en France
            lat = 46.0 + (i % 100) * 0.01  # Entre 46 et 46.99
            lng = 2.0 + (i % 100) * 0.01   # Entre 2 et 2.99
            
            assets_to_create.append(Asset(
                nom=f'Asset {i+1}',
                reference=f'REF-{i+1:04d}',
                latitude=lat,
                longitude=lng,
                categorie=self.category,
                statut='en_service'
            ))
        
        Asset.objects.bulk_create(assets_to_create)

    def test_carte_performance_with_many_assets(self):
        """Test de performance avec beaucoup d'assets"""
        import time
        
        start_time = time.time()
        response = self.client.get(reverse('carte_ftth'))
        end_time = time.time()
        
        self.assertEqual(response.status_code, 200)
        
        # Le chargement devrait prendre moins de 5 secondes
        self.assertLess(end_time - start_time, 5.0)

    def test_search_performance(self):
        """Test de performance de la recherche"""
        import time
        
        start_time = time.time()
        response = self.client.get(reverse('api_assets_search'), {'q': 'Asset'})
        end_time = time.time()
        
        self.assertEqual(response.status_code, 200)
        
        # La recherche devrait prendre moins de 2 secondes
        self.assertLess(end_time - start_time, 2.0)
        
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        # Vérifier que la pagination fonctionne (max 20 résultats)
        self.assertLessEqual(len(data['results']), 20)


class SecurityTest(TestCase):
    """
    Tests de sécurité pour la carte FTTH
    """
    
    def setUp(self):
        """Création des données de test pour la sécurité"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.category = CategorieAsset.objects.create(nom='Test Category')
        
        self.asset = Asset.objects.create(
            nom='Asset Test',
            latitude=48.8566,
            longitude=2.3522,
            categorie=self.category
        )

    def test_unauthenticated_access(self):
        """Test d'accès non authentifié"""
        client = Client()
        
        # Toutes les vues doivent rediriger vers la page de connexion
        response = client.get(reverse('carte_ftth'))
        self.assertEqual(response.status_code, 302)
        
        response = client.get(reverse('asset_details_ajax', kwargs={'asset_id': self.asset.id}))
        self.assertEqual(response.status_code, 302)
        
        response = client.get(reverse('api_assets_search'))
        self.assertEqual(response.status_code, 302)

    def test_sql_injection_protection(self):
        """Test de protection contre l'injection SQL"""
        client = Client()
        client.login(username='testuser', password='testpass123')
        
        # Tentative d'injection SQL dans la recherche
        malicious_query = "'; DROP TABLE core_asset; --"
        response = client.get(reverse('api_assets_search'), {'q': malicious_query})
        
        self.assertEqual(response.status_code, 200)
        
        # Vérifier que la table existe toujours
        self.assertTrue(Asset.objects.exists())

    def test_xss_protection(self):
        """Test de protection contre les attaques XSS"""
        client = Client()
        client.login(username='testuser', password='testpass123')
        
        # Créer un asset avec du contenu potentiellement malveillant
        malicious_asset = Asset.objects.create(
            nom='<script>alert("XSS")</script>',
            reference='<img src="x" onerror="alert(1)">',
            latitude=48.8566,
            longitude=2.3522,
            categorie=self.category
        )
        
        # Tester la recherche
        response = client.get(reverse('api_assets_search'), {'q': 'script'})
        self.assertEqual(response.status_code, 200)
        
        # Tester les détails
        response = client.get(reverse('asset_details_ajax', kwargs={'asset_id': malicious_asset.id}))
        self.assertEqual(response.status_code, 200)
        
        # Le contenu ne devrait pas contenir de script exécutable
        data = json.loads(response.content)
        self.assertNotIn('<script>', data['asset']['nom'])


# Utilitaires pour les tests
class TestHelpers:
    """
    Fonctions utilitaires pour les tests
    """
    
    @staticmethod
    def create_test_assets(count=10):
        """
        Crée un nombre donné d'assets de test
        """
        category = CategorieAsset.objects.create(nom='Test Category')
        assets = []
        
        for i in range(count):
            asset = Asset.objects.create(
                nom=f'Asset {i+1}',
                reference=f'REF-{i+1:03d}',
                latitude=46.0 + i * 0.1,
                longitude=2.0 + i * 0.1,
                categorie=category,
                statut='en_service'
            )
            assets.append(asset)
        
        return assets
    
    @staticmethod
    def create_invalid_assets(count=5):
        """
        Crée des assets avec coordonnées invalides
        """
        category = CategorieAsset.objects.create(nom='Invalid Category')
        assets = []
        
        invalid_coords = [
            (None, None),
            (0, 0),
            (91.0, 2.0),  # Latitude > 90
            (45.0, 181.0),  # Longitude > 180
            (float('nan'), 2.0),  # NaN
        ]
        
        for i, (lat, lng) in enumerate(invalid_coords[:count]):
            asset = Asset.objects.create(
                nom=f'Invalid Asset {i+1}',
                reference=f'INV-{i+1:03d}',
                latitude=lat,
                longitude=lng,
                categorie=category,
                statut='hors_service'
            )
            assets.append(asset)
        
        return assets


# Tests d'intégration avec Selenium (optionnel)
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from django.contrib.staticfiles.testing import StaticLiveServerTestCase
    
    class SeleniumTest(StaticLiveServerTestCase):
        """
        Tests d'intégration avec Selenium pour tester l'interface utilisateur
        """
        
        @classmethod
        def setUpClass(cls):
            super().setUpClass()
            # Utiliser Chrome en mode headless pour les tests
            options = webdriver.ChromeOptions()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            
            try:
                cls.driver = webdriver.Chrome(options=options)
                cls.driver.implicitly_wait(10)
            except Exception as e:
                cls.driver = None
                print(f"Selenium non disponible: {e}")
        
        @classmethod
        def tearDownClass(cls):
            if cls.driver:
                cls.driver.quit()
            super().tearDownClass()
        
        def setUp(self):
            if not self.driver:
                self.skipTest("Selenium non disponible")
                
            self.user = User.objects.create_user(
                username='testuser',
                password='testpass123'
            )
            
            self.category = CategorieAsset.objects.create(nom='Test Category')
            self.asset = Asset.objects.create(
                nom='Asset Test',
                reference='REF-001',
                latitude=48.8566,
                longitude=2.3522,
                categorie=self.category
            )
        
        def test_carte_loads_correctly(self):
            """Test que la carte se charge correctement"""
            # Connexion
            self.driver.get(f'{self.live_server_url}/accounts/login/')
            self.driver.find_element(By.NAME, 'username').send_keys('testuser')
            self.driver.find_element(By.NAME, 'password').send_keys('testpass123')
            self.driver.find_element(By.XPATH, '//button[@type="submit"]').click()
            
            # Naviguer vers la carte
            self.driver.get(f'{self.live_server_url}/carte/')
            
            # Vérifier que la carte est chargée
            map_element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, 'map'))
            )
            self.assertIsNotNone(map_element)
            
            # Vérifier que les statistiques sont affichées
            stats_element = self.driver.find_element(By.ID, 'stat-total')
            self.assertIsNotNone(stats_element)
        
        def test_search_functionality(self):
            """Test de la fonctionnalité de recherche"""
            # Connexion et navigation
            self.driver.get(f'{self.live_server_url}/accounts/login/')
            self.driver.find_element(By.NAME, 'username').send_keys('testuser')
            self.driver.find_element(By.NAME, 'password').send_keys('testpass123')
            self.driver.find_element(By.XPATH, '//button[@type="submit"]').click()
            
            self.driver.get(f'{self.live_server_url}/carte/')
            
            # Attendre le chargement de la carte
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, 'map'))
            )
            
            # Utiliser la recherche
            search_input = self.driver.find_element(By.ID, 'search-input')
            search_input.send_keys('Asset Test')
            
            # Attendre les résultats
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.ID, 'search-results'))
            )
            
            # Vérifier qu'il y a des résultats
            results = self.driver.find_element(By.ID, 'search-results')
            self.assertFalse('hidden' in results.get_attribute('class'))

except ImportError:
    print("Selenium non installé, tests d'intégration ignorés")


# Configuration pour les tests
class CarteFTTHTestConfig:
    """
    Configuration spécifique pour les tests de la carte FTTH
    """
    
    # Données de test
    VALID_COORDINATES = [
        (48.8566, 2.3522),   # Paris
        (45.7640, 4.8357),   # Lyon
        (43.2965, 5.3698),   # Marseille
        (50.6292, 3.0573),   # Lille
        (47.2184, -1.5536),  # Nantes
    ]
    
    INVALID_COORDINATES = [
        (None, None),
        (0, 0),
        (91.0, 2.0),
        (45.0, 181.0),
        (float('nan'), 2.0),
        ("invalid", "invalid"),
    ]
    
    STATUSES = ['en_service', 'en_panne', 'en_maintenance', 'hors_service']
    
    CATEGORIES = ['NRO', 'PM', 'PB', 'PTO', 'Cable']


if __name__ == '__main__':
    # Exécuter les tests
    import unittest
    unittest.main()