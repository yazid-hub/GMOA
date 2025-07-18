// src/screens/auth/LoginScreen.tsx
import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  StatusBar,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  Image,
  Animated,
  Dimensions,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import { useAppDispatch, useAppSelector } from '../../store/store';
import { loginUser, selectAuthLoading, selectAuthError } from '../../store/slices/authSlice';
import { Button, Input, Card } from '../../components/common';
import { theme } from '../../styles/theme';

const { width, height } = Dimensions.get('window');

const LoginScreen: React.FC = () => {
  const dispatch = useAppDispatch();
  const loading = useAppSelector(selectAuthLoading);
  const error = useAppSelector(selectAuthError);

  const [credentials, setCredentials] = useState({
    username: '',
    password: '',
  });
  const [showPassword, setShowPassword] = useState(false);
  const [fadeAnim] = useState(new Animated.Value(0));
  const [slideAnim] = useState(new Animated.Value(height));

  useEffect(() => {
    // Animation d'entrée
    Animated.parallel([
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 1000,
        useNativeDriver: true,
      }),
      Animated.spring(slideAnim, {
        toValue: 0,
        tension: 50,
        friction: 8,
        useNativeDriver: true,
      }),
    ]).start();
  }, []);

  const handleLogin = async () => {
    if (!credentials.username.trim() || !credentials.password.trim()) {
      return;
    }

    const result = await dispatch(loginUser({
      username: credentials.username.trim(),
      password: credentials.password,
      device_id: 'mobile_app_v1', // TODO: Générer un ID unique par appareil
    }));

    // La navigation se fera automatiquement grâce au state management
  };

  const isFormValid = credentials.username.trim() && credentials.password.trim();

  return (
    <View style={styles.container}>
      <StatusBar
        barStyle="light-content"
        backgroundColor={theme.colors.primary[600]}
        translucent
      />
      
      {/* Background avec gradient effet */}
      <View style={styles.backgroundGradient}>
        <View style={styles.circleDecoration1} />
        <View style={styles.circleDecoration2} />
      </View>

      <KeyboardAvoidingView
        style={styles.keyboardContainer}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        keyboardVerticalOffset={Platform.OS === 'ios' ? 0 : 20}
      >
        <ScrollView
          contentContainerStyle={styles.scrollContent}
          showsVerticalScrollIndicator={false}
          keyboardShouldPersistTaps="handled"
        >
          {/* Header avec logo */}
          <Animated.View 
            style={[styles.header, { opacity: fadeAnim }]}
          >
            <View style={styles.logoContainer}>
              <View style={styles.logoCircle}>
                <Icon name="settings" size={40} color={theme.colors.white} />
              </View>
            </View>
            <Text style={styles.appTitle}>GMAO Mobile</Text>
            <Text style={styles.subtitle}>
              Gestion de Maintenance Assistée par Ordinateur
            </Text>
          </Animated.View>

          {/* Formulaire de connexion */}
          <Animated.View
            style={[
              styles.formContainer,
              { transform: [{ translateY: slideAnim }] }
            ]}
          >
            <Card variant="elevated" style={styles.loginCard}>
              <View style={styles.cardHeader}>
                <Icon name="log-in" size={24} color={theme.colors.primary[500]} />
                <Text style={styles.cardTitle}>Connexion</Text>
              </View>

              {error && (
                <View style={styles.errorContainer}>
                  <Icon name="alert-circle" size={20} color={theme.colors.error[500]} />
                  <Text style={styles.errorText}>{error}</Text>
                </View>
              )}

              <View style={styles.formFields}>
                <Input
                  label="Nom d'utilisateur"
                  placeholder="Entrez votre nom d'utilisateur"
                  value={credentials.username}
                  onChangeText={(text) => setCredentials(prev => ({ ...prev, username: text }))}
                  leftIcon={<Icon name="user" size={20} color={theme.colors.gray[400]} />}
                  autoCapitalize="none"
                  autoCorrect={false}
                  returnKeyType="next"
                />

                <Input
                  label="Mot de passe"
                  placeholder="Entrez votre mot de passe"
                  value={credentials.password}
                  onChangeText={(text) => setCredentials(prev => ({ ...prev, password: text }))}
                  secureTextEntry={!showPassword}
                  leftIcon={<Icon name="lock" size={20} color={theme.colors.gray[400]} />}
                  rightIcon={
                    <Icon 
                      name={showPassword ? "eye-off" : "eye"} 
                      size={20} 
                      color={theme.colors.gray[400]}
                      onPress={() => setShowPassword(!showPassword)}
                    />
                  }
                  returnKeyType="done"
                  onSubmitEditing={handleLogin}
                />
              </View>

              <Button
                variant="primary"
                size="lg"
                fullWidth
                loading={loading}
                disabled={!isFormValid}
                onPress={handleLogin}
                style={styles.loginButton}
              >
                Se connecter
              </Button>

              {/* Informations supplémentaires */}
              <View style={styles.loginInfo}>
                <View style={styles.infoRow}>
                  <Icon name="wifi" size={16} color={theme.colors.success[500]} />
                  <Text style={styles.infoText}>Fonctionne hors ligne</Text>
                </View>
                <View style={styles.infoRow}>
                  <Icon name="shield" size={16} color={theme.colors.primary[500]} />
                  <Text style={styles.infoText}>Connexion sécurisée</Text>
                </View>
                <View style={styles.infoRow}>
                  <Icon name="sync" size={16} color={theme.colors.secondary[500]} />
                  <Text style={styles.infoText}>Synchronisation automatique</Text>
                </View>
              </View>
            </Card>
          </Animated.View>

          {/* Footer */}
          <Animated.View 
            style={[styles.footer, { opacity: fadeAnim }]}
          >
            <Text style={styles.footerText}>
              Version 1.0.0 • Développé pour les techniciens terrain
            </Text>
          </Animated.View>
        </ScrollView>
      </KeyboardAvoidingView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.colors.primary[500],
  },
  backgroundGradient: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: theme.colors.primary[600],
  },
  circleDecoration1: {
    position: 'absolute',
    top: -100,
    right: -100,
    width: 300,
    height: 300,
    borderRadius: 150,
    backgroundColor: theme.colors.primary[400],
    opacity: 0.3,
  },
  circleDecoration2: {
    position: 'absolute',
    bottom: -150,
    left: -150,
    width: 400,
    height: 400,
    borderRadius: 200,
    backgroundColor: theme.colors.primary[700],
    opacity: 0.2,
  },
  keyboardContainer: {
    flex: 1,
  },
  scrollContent: {
    flexGrow: 1,
    paddingHorizontal: theme.spacing[4],
    paddingTop: Platform.OS === 'ios' ? 60 : 40,
    paddingBottom: theme.spacing[6],
  },
  header: {
    alignItems: 'center',
    marginBottom: theme.spacing[8],
  },
  logoContainer: {
    marginBottom: theme.spacing[4],
  },
  logoCircle: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: theme.colors.white,
    opacity: 0.9,
    justifyContent: 'center',
    alignItems: 'center',
    ...theme.shadows.lg,
  },
  appTitle: {
    fontSize: theme.typography.sizes['4xl'],
    fontFamily: theme.typography.fonts.bold,
    color: theme.colors.white,
    textAlign: 'center',
    marginBottom: theme.spacing[2],
  },
  subtitle: {
    fontSize: theme.typography.sizes.base,
    fontFamily: theme.typography.fonts.regular,
    color: theme.colors.white,
    textAlign: 'center',
    opacity: 0.9,
    lineHeight: 22,
  },
  formContainer: {
    flex: 1,
    justifyContent: 'center',
  },
  loginCard: {
    padding: theme.spacing[6],
    backgroundColor: theme.colors.white,
    borderRadius: theme.borderRadius['2xl'],
    ...theme.shadows.xl,
  },
  cardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: theme.spacing[6],
  },
  cardTitle: {
    fontSize: theme.typography.sizes['2xl'],
    fontFamily: theme.typography.fonts.semiBold,
    color: theme.colors.text.primary,
    marginLeft: theme.spacing[2],
  },
  errorContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: theme.colors.error[50],
    padding: theme.spacing[3],
    borderRadius: theme.borderRadius.md,
    marginBottom: theme.spacing[4],
    borderWidth: 1,
    borderColor: theme.colors.error[200],
  },
  errorText: {
    fontSize: theme.typography.sizes.sm,
    color: theme.colors.error[700],
    fontFamily: theme.typography.fonts.medium,
    marginLeft: theme.spacing[2],
    flex: 1,
  },
  formFields: {
    marginBottom: theme.spacing[6],
    gap: theme.spacing[4],
  },
  loginButton: {
    marginBottom: theme.spacing[6],
    ...theme.shadows.md,
  },
  loginInfo: {
    gap: theme.spacing[3],
  },
  infoRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  infoText: {
    fontSize: theme.typography.sizes.sm,
    color: theme.colors.text.secondary,
    fontFamily: theme.typography.fonts.regular,
    marginLeft: theme.spacing[2],
  },
  footer: {
    alignItems: 'center',
    marginTop: theme.spacing[8],
  },
  footerText: {
    fontSize: theme.typography.sizes.sm,
    color: theme.colors.white,
    fontFamily: theme.typography.fonts.regular,
    textAlign: 'center',
    opacity: 0.8,
  },
});

export default LoginScreen;