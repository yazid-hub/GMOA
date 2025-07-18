// src/navigation/AppNavigator.tsx - Version simplifiée temporaire
import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';
import { View, Text, StyleSheet } from 'react-native';

import { useAppSelector } from '../store/store';
import { selectIsAuthenticated } from '../store/slices/authSlice';
import { theme } from '../styles/theme';

// Écrans temporaires simples
const LoginScreen = () => (
  <View style={styles.center}>
    <Text style={styles.text}>Écran de Connexion</Text>
  </View>
);

const DashboardScreen = () => (
  <View style={styles.center}>
    <Text style={styles.text}>Dashboard GMAO</Text>
  </View>
);

// Types pour la navigation
export type AuthStackParamList = {
  Login: undefined;
};

export type MainStackParamList = {
  Dashboard: undefined;
};

const AuthStack = createStackNavigator<AuthStackParamList>();
const MainStack = createStackNavigator<MainStackParamList>();

// Navigateurs
const AuthNavigator: React.FC = () => (
  <AuthStack.Navigator screenOptions={{ headerShown: false }}>
    <AuthStack.Screen name="Login" component={LoginScreen} />
  </AuthStack.Navigator>
);

const MainNavigator: React.FC = () => (
  <MainStack.Navigator>
    <MainStack.Screen name="Dashboard" component={DashboardScreen} />
  </MainStack.Navigator>
);

// App Navigator principal
const AppNavigator: React.FC = () => {
  const isAuthenticated = useAppSelector(selectIsAuthenticated);

  return (
    <NavigationContainer>
      {isAuthenticated ? <MainNavigator /> : <AuthNavigator />}
    </NavigationContainer>
  );
};

const styles = StyleSheet.create({
  center: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: theme.colors.background.primary,
  },
  text: {
    fontSize: theme.typography.sizes.lg,
    color: theme.colors.text.primary,
  },
});

export default AppNavigator;