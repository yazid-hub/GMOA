import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
  Image,
  KeyboardAvoidingView,
  Platform,
  TouchableWithoutFeedback,
  Keyboard,
  StatusBar,
  Animated,
  Dimensions
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useNavigation } from '@react-navigation/native';
import Svg, { Path } from 'react-native-svg';

// Types pour la navigation
interface NavigationProp {
  replace: (screen: string) => void;
}

// Icônes SVG
const UserIcon = () => (
  <Svg width="20" height="20" viewBox="0 0 20 20" fill="none">
    <Path d="M10 10C12.7614 10 15 7.76142 15 5C15 2.23858 12.7614 0 10 0C7.23858 0 5 2.23858 5 5C5 7.76142 7.23858 10 10 10Z" fill="#64748B"/>
    <Path d="M10 12C4.47715 12 0 16.4772 0 22H20C20 16.4772 15.5228 12 10 12Z" fill="#64748B"/>
  </Svg>
);

const LockIcon = () => (
  <Svg width="20" height="20" viewBox="0 0 20 20" fill="none">
    <Path d="M15.8333 9.16667H4.16667C3.24619 9.16667 2.5 9.91286 2.5 10.8333V16.6667C2.5 17.5871 3.24619 18.3333 4.16667 18.3333H15.8333C16.7538 18.3333 17.5 17.5871 17.5 16.6667V10.8333C17.5 9.91286 16.7538 9.16667 15.8333 9.16667Z" fill="#64748B"/>
    <Path d="M5.83333 9.16667V5.83333C5.83333 4.72827 6.27232 3.66846 7.05372 2.88706C7.83512 2.10565 8.89493 1.66667 10 1.66667C11.1051 1.66667 12.1649 2.10565 12.9463 2.88706C13.7277 3.66846 14.1667 4.72827 14.1667 5.83333V9.16667" stroke="#64748B" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
  </Svg>
);

const EyeIcon = ({ visible }: { visible: boolean }) => (
  <Svg width="20" height="20" viewBox="0 0 20 20" fill="none">
    {visible ? (
      <>
        <Path d="M10 4.16667C3.33333 4.16667 1.66667 10 1.66667 10C1.66667 10 3.33333 15.8333 10 15.8333C16.6667 15.8333 18.3333 10 18.3333 10C18.3333 10 16.6667 4.16667 10 4.16667Z" stroke="#64748B" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
        <Path d="M10 12.5C11.3807 12.5 12.5 11.3807 12.5 10C12.5 8.61929 11.3807 7.5 10 7.5C8.61929 7.5 7.5 8.61929 7.5 10C7.5 11.3807 8.61929 12.5 10 12.5Z" stroke="#64748B" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
      </>
    ) : (
      <>
        <Path d="M2.5 2.5L17.5 17.5" stroke="#64748B" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
        <Path d="M8.36667 8.36667C8.12779 8.60554 8 8.92971 8 9.26667C8 9.60362 8.12779 9.92779 8.36667 10.1667C8.60554 10.4055 8.92971 10.5333 9.26667 10.5333C9.60362 10.5333 9.92779 10.4055 10.1667 10.1667" stroke="#64748B" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
        <Path d="M15.4667 15.4667C13.9067 16.6133 12.0333 17.2667 10 17.2667C5.16667 17.2667 1.66667 10 1.66667 10C2.76667 7.85333 4.34667 5.99333 6.26667 4.86" stroke="#64748B" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
        <Path d="M11.7667 6.76667C12.7583 7.11114 13.5583 7.91114 14.0333 8.9" stroke="#64748B" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
        <Path d="M6.26667 12.1C6.74333 13.3333 7.76667 14.3567 9.26667 14.3567C9.8 14.3567 10.3 14.2333 10.7333 14.0333" stroke="#64748B" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
        <Path d="M18.3333 10C18.3333 10 17.2 12.3333 15.4667 14.1333" stroke="#64748B" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
      </>
    )}
  </Svg>
);

interface LoginScreenProps {
  navigation?: NavigationProp;
}

const APP_VERSION = '1.0.0';
const LOGO_URI = 'https://via.placeholder.com/150x80?text=GMOA';

const LoginScreen: React.FC<LoginScreenProps> = ({ navigation }) => {
  // États
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);
  
  // Références pour les champs de saisie
  const passwordInputRef = useRef<TextInput>(null);
  
  // Animations
  const logoOpacity = useRef(new Animated.Value(0)).current;
  const formTranslateY = useRef(new Animated.Value(50)).current;
  
  // Hook de navigation
  const nav = useNavigation<NavigationProp>();
  const navigationToUse = navigation || nav;
  
  useEffect(() => {
    // Animation d'entrée
    Animated.parallel([
      Animated.timing(logoOpacity, {
        toValue: 1,
        duration: 1000,
        useNativeDriver: true
      }),
      Animated.timing(formTranslateY, {
        toValue: 0,
        duration: 800,
        useNativeDriver: true
      })
    ]).start();
    
    // Vérifier si des identifiants sont sauvegardés
    loadSavedCredentials();
  }, [logoOpacity, formTranslateY]);
  
  const loadSavedCredentials = async () => {
    try {
      // Exemple d'implémentation avec AsyncStorage
      // const savedUsername = await AsyncStorage.getItem('username');
      // const savedPassword = await AsyncStorage.getItem('password');
      // const savedRememberMe = await AsyncStorage.getItem('rememberMe');
      
      // if (savedUsername && savedPassword && savedRememberMe === 'true') {
      //   setUsername(savedUsername);
      //   setPassword(savedPassword);
      //   setRememberMe(true);
      // }
      
      console.log('Chargement des identifiants sauvegardés...');
    } catch (error) {
      console.error('Erreur lors du chargement des identifiants:', error);
    }
  };
  
  const saveCredentials = async () => {
    try {
      if (rememberMe) {
        // await AsyncStorage.setItem('username', username);
        // await AsyncStorage.setItem('password', password);
        // await AsyncStorage.setItem('rememberMe', 'true');
        console.log('Identifiants sauvegardés');
      } else {
        // await AsyncStorage.removeItem('username');
        // await AsyncStorage.removeItem('password');
        // await AsyncStorage.removeItem('rememberMe');
        console.log('Identifiants supprimés');
      }
    } catch (error) {
      console.error('Erreur lors de la sauvegarde:', error);
    }
  };
  
  const validateInputs = (): boolean => {
    if (!username.trim()) {
      setErrorMessage("Veuillez saisir votre nom d'utilisateur");
      return false;
    }
    
    if (!password.trim()) {
      setErrorMessage('Veuillez saisir votre mot de passe');
      return false;
    }
    
    if (username.length < 3) {
      setErrorMessage("Le nom d'utilisateur doit contenir au moins 3 caractères");
      return false;
    }
    
    if (password.length < 6) {
      setErrorMessage('Le mot de passe doit contenir au moins 6 caractères');
      return false;
    }
    
    setErrorMessage('');
    return true;
  };

  const handleLogin = async () => {
    if (!validateInputs()) {
      return;
    }
    
    setIsLoading(true);
    setErrorMessage('');
    
    try {
      // Simuler un appel API
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      // Exemple d'appel API réel
      // const response = await fetch('https://api.example.com/login', {
      //   method: 'POST',
      //   headers: {
      //     'Content-Type': 'application/json',
      //   },
      //   body: JSON.stringify({ 
      //     username: username.trim(), 
      //     password: password.trim() 
      //   }),
      // });
      
      // if (!response.ok) {
      //   throw new Error('Erreur de connexion');
      // }
      
      // const data = await response.json();
      
      // Sauvegarder les identifiants si nécessaire
      await saveCredentials();
      
      // Naviguer vers l'écran principal
      if (navigationToUse) {
        navigationToUse.replace('MainApp');
      } else {
        console.log('Connexion réussie pour:', username);
        Alert.alert('Succès', 'Connexion réussie!');
      }
      
    } catch (error) {
      console.error('Erreur de connexion:', error);
      setErrorMessage('Identifiants incorrects. Veuillez réessayer.');
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleForgotPassword = () => {
    Alert.alert(
      'Mot de passe oublié',
      'Veuillez contacter votre administrateur système pour réinitialiser votre mot de passe.',
      [
        { text: 'OK', style: 'default' }
      ]
    );
  };

  const focusPasswordInput = () => {
    passwordInputRef.current?.focus();
  };

  const clearError = () => {
    if (errorMessage) {
      setErrorMessage('');
    }
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <StatusBar barStyle="light-content" backgroundColor="#3b82f6" />
      
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.container}
      >
        <TouchableWithoutFeedback onPress={Keyboard.dismiss}>
          <View style={styles.innerContainer}>
            <Animated.View 
              style={[styles.logoContainer, { opacity: logoOpacity }]}
            >
              <Image
                source={{ uri: LOGO_URI }}
                style={styles.logo}
                resizeMode="contain"
              />
              <Text style={styles.subtitle}>Gestion de Maintenance et d'Opérations</Text>
            </Animated.View>
            
            <Animated.View 
              style={[
                styles.formContainer, 
                { transform: [{ translateY: formTranslateY }] }
              ]}
            >
              <Text style={styles.formTitle}>Connexion</Text>
              
              {errorMessage ? (
                <View style={styles.errorContainer}>
                  <Text style={styles.errorText}>{errorMessage}</Text>
                </View>
              ) : null}
              
              <View style={styles.inputContainer}>
                <View style={styles.iconContainer}>
                  <UserIcon />
                </View>
                <TextInput
                  style={styles.input}
                  placeholder="Nom d'utilisateur"
                  value={username}
                  onChangeText={(text) => {
                    setUsername(text);
                    clearError();
                  }}
                  autoCapitalize="none"
                  autoCorrect={false}
                  returnKeyType="next"
                  blurOnSubmit={false}
                  onSubmitEditing={focusPasswordInput}
                  editable={!isLoading}
                />
              </View>
              
              <View style={styles.inputContainer}>
                <View style={styles.iconContainer}>
                  <LockIcon />
                </View>
                <TextInput
                  ref={passwordInputRef}
                  style={styles.input}
                  placeholder="Mot de passe"
                  value={password}
                  onChangeText={(text) => {
                    setPassword(text);
                    clearError();
                  }}
                  secureTextEntry={!showPassword}
                  autoCapitalize="none"
                  autoCorrect={false}
                  returnKeyType="done"
                  onSubmitEditing={handleLogin}
                  editable={!isLoading}
                />
                <TouchableOpacity 
                  style={styles.eyeIconContainer}
                  onPress={() => setShowPassword(prev => !prev)}
                  disabled={isLoading}
                >
                  <EyeIcon visible={showPassword} />
                </TouchableOpacity>
              </View>
              
              <View style={styles.optionsContainer}>
                <TouchableOpacity 
                  style={styles.rememberMeContainer}
                  onPress={() => setRememberMe(prev => !prev)}
                  disabled={isLoading}
                >
                  <View style={[styles.checkbox, rememberMe && styles.checkboxChecked]}>
                    {rememberMe && (
                      <Text style={styles.checkmark}>✓</Text>
                    )}
                  </View>
                  <Text style={styles.rememberMeText}>Se souvenir de moi</Text>
                </TouchableOpacity>
                
                <TouchableOpacity 
                  onPress={handleForgotPassword}
                  disabled={isLoading}
                >
                  <Text style={styles.forgotPasswordText}>Mot de passe oublié ?</Text>
                </TouchableOpacity>
              </View>
              
              <TouchableOpacity
                style={[styles.loginButton, isLoading && styles.loginButtonDisabled]}
                onPress={handleLogin}
                disabled={isLoading}
              >
                {isLoading ? (
                  <ActivityIndicator size="small" color="#ffffff" />
                ) : (
                  <Text style={styles.loginButtonText}>Se connecter</Text>
                )}
              </TouchableOpacity>
            </Animated.View>
            
            <Text style={styles.versionText}>Version {APP_VERSION}</Text>
          </View>
        </TouchableWithoutFeedback>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: '#3b82f6',
  },
  container: {
    flex: 1,
    backgroundColor: '#3b82f6',
  },
  innerContainer: {
    flex: 1,
    justifyContent: 'center',
    padding: 20,
  },
  logoContainer: {
    alignItems: 'center',
    marginBottom: 30,
  },
  logo: {
    width: 150,
    height: 80,
    marginBottom: 10,
  },
  subtitle: {
    fontSize: 16,
    color: '#ffffff',
    textAlign: 'center',
    opacity: 0.9,
    paddingHorizontal: 20,
  },
  formContainer: {
    backgroundColor: '#ffffff',
    borderRadius: 12,
    padding: 24,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.2,
    shadowRadius: 8,
    elevation: 5,
  },
  formTitle: {
    fontSize: 22,
    fontWeight: '700',
    color: '#1e293b',
    marginBottom: 20,
    textAlign: 'center',
  },
  errorContainer: {
    backgroundColor: '#fef2f2',
    borderRadius: 8,
    padding: 12,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#fee2e2',
  },
  errorText: {
    color: '#dc2626',
    fontSize: 14,
    textAlign: 'center',
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#f8fafc',
    borderWidth: 1,
    borderColor: '#e2e8f0',
    borderRadius: 8,
    marginBottom: 16,
  },
  iconContainer: {
    paddingHorizontal: 12,
  },
  input: {
    flex: 1,
    paddingVertical: 14,
    fontSize: 16,
    color: '#1e293b',
  },
  eyeIconContainer: {
    paddingHorizontal: 12,
  },
  optionsContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
  },
  rememberMeContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  checkbox: {
    width: 20,
    height: 20,
    borderWidth: 1,
    borderColor: '#cbd5e1',
    borderRadius: 4,
    marginRight: 8,
    justifyContent: 'center',
    alignItems: 'center',
  },
  checkboxChecked: {
    backgroundColor: '#3b82f6',
    borderColor: '#3b82f6',
  },
  checkmark: {
    color: '#ffffff',
    fontSize: 14,
    fontWeight: 'bold',
  },
  rememberMeText: {
    fontSize: 14,
    color: '#64748b',
  },
  forgotPasswordText: {
    fontSize: 14,
    color: '#3b82f6',
    fontWeight: '500',
  },
  loginButton: {
    backgroundColor: '#3b82f6',
    borderRadius: 8,
    paddingVertical: 14,
    alignItems: 'center',
    shadowColor: '#1e40af',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.3,
    shadowRadius: 4,
    elevation: 3,
  },
  loginButtonDisabled: {
    backgroundColor: '#93c5fd',
    shadowOpacity: 0,
    elevation: 0,
  },
  loginButtonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '600',
  },
  versionText: {
    textAlign: 'center',
    color: 'rgba(255, 255, 255, 0.7)',
    fontSize: 12,
    marginTop: 16,
  },
});

export default LoginScreen;