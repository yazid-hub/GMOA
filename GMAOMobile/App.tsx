// App.tsx
import React, { useEffect, useState } from 'react';
import { StatusBar, Platform, AppState, AppStateStatus } from 'react-native';
import { Provider } from 'react-redux';
import { PersistGate } from 'redux-persist/integration/react';
import Toast from 'react-native-toast-message';
import NetInfo from '@react-native-community/netinfo';

import { store, persistor } from './src/store/store';
import { setNetworkState } from './src/store/slices/networkSlice';
import { checkNetworkStatus, performBackgroundSync } from './src/store/slices/syncSlice';
import AppNavigator from './src/navigation/AppNavigator';
import DatabaseManager from './src/database/DatabaseManager';
import { Loader } from './src/components/common';
import { theme } from './src/styles/theme';

// Configuration Toast
const toastConfig = {
  success: ({ text1, text2 }: any) => (
    <Toast text1={text1} text2={text2} />
  ),
  error: ({ text1, text2 }: any) => (
    <Toast text1={text1} text2={text2} />
  ),
  info: ({ text1, text2 }: any) => (
    <Toast text1={text1} text2={text2} />
  ),
};

const App: React.FC = () => {
  const [isDbReady, setIsDbReady] = useState(false);
  const [appState, setAppState] = useState(AppState.currentState);

  useEffect(() => {
    initializeApp();
    setupAppStateListener();
    setupNetworkListener();
    
    return () => {
      // Cleanup si nécessaire
    };
  }, []);

  /**
   * Initialisation de l'application
   */
  const initializeApp = async () => {
    try {
      console.log('🚀 Initialisation de l\'application...');
      
      // Initialiser la base de données
      await DatabaseManager.getInstance().initializeDatabase();
      console.log('✅ Base de données initialisée');
      
      // Marquer comme prêt
      setIsDbReady(true);
      console.log('✅ Application prête');
      
    } catch (error) {
      console.error('❌ Erreur initialisation app:', error);
      // TODO: Afficher un écran d'erreur
      setIsDbReady(true); // Pour ne pas bloquer l'app
    }
  };

  /**
   * Écoute les changements d'état de l'app
   */
  const setupAppStateListener = () => {
    const handleAppStateChange = (nextAppState: AppStateStatus) => {
      console.log(`📱 App state: ${appState} -> ${nextAppState}`);
      
      if (appState.match(/inactive|background/) && nextAppState === 'active') {
        // App revient au premier plan
        handleAppBecomeActive();
      }
      
      if (appState === 'active' && nextAppState.match(/inactive|background/)) {
        // App passe en arrière-plan
        handleAppBecomeInactive();
      }
      
      setAppState(nextAppState);
    };

    const subscription = AppState.addEventListener('change', handleAppStateChange);
    return () => subscription?.remove();
  };

  /**
   * Écoute les changements de réseau
   */
  const setupNetworkListener = () => {
    const unsubscribe = NetInfo.addEventListener(state => {
      console.log('🌐 Network state:', state);
      
      store.dispatch(setNetworkState({
        isConnected: state.isConnected || false,
        type: state.type,
        isWifiConnection: state.type === 'wifi',
        isCellularConnection: state.type === 'cellular',
        isExpensive: state.isConnectionExpensive || false,
      }));
      
      // Vérifier le statut de sync quand le réseau change
      if (state.isConnected) {
        store.dispatch(checkNetworkStatus());
      }
    });

    return unsubscribe;
  };

  /**
   * App devient active
   */
  const handleAppBecomeActive = () => {
    console.log('📱 App devient active');
    
    // Vérifier le statut réseau
    store.dispatch(checkNetworkStatus());
    
    // Sync automatique si nécessaire
    setTimeout(() => {
      store.dispatch(performBackgroundSync());
    }, 1000);
  };

  /**
   * App devient inactive
   */
  const handleAppBecomeInactive = () => {
    console.log('📱 App devient inactive');
    // Sauvegarder l'état si nécessaire
  };

  // Écran de chargement pendant l'initialisation
  if (!isDbReady) {
    return (
      <Loader 
        overlay 
        text="Initialisation de l'application..."
        size="large"
        color={theme.colors.primary[500]}
      />
    );
  }

  return (
    <Provider store={store}>
      <PersistGate 
        loading={
          <Loader 
            overlay 
            text="Chargement des données..."
            size="large" 
            color={theme.colors.primary[500]}
          />
        } 
        persistor={persistor}
      >
        <StatusBar
          barStyle={Platform.OS === 'ios' ? 'light-content' : 'light-content'}
          backgroundColor={theme.colors.primary[500]}
          translucent={Platform.OS === 'android'}
        />
        
        <AppNavigator />
        
        <Toast 
          config={toastConfig}
          position="top"
          topOffset={Platform.OS === 'ios' ? 50 : 30}
        />
      </PersistGate>
    </Provider>
  );
};

export default App;