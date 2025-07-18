// src/navigation/AppNavigator.tsx - Version corrigée étape par étape
import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Platform, View, Text } from 'react-native';
import Icon from 'react-native-vector-icons/Feather';

import { useAppSelector } from '../store/store';
import { selectIsAuthenticated } from '../store/slices/authSlice';
import { theme } from '../styles/theme';

// Import des écrans - SEULEMENT LES EXISTANTS
import LoginScreen from '../screens/auth/LoginScreen';
import DashboardScreen from '../screens/dashboard/DashboardScreen';

// Écrans temporaires pour éviter les erreurs
const WorkOrderListScreen = () => (
  <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
    <Text>Liste des Ordres de Travail - À venir</Text>
  </View>
);

const QRScannerScreen = () => (
  <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
    <Text>Scanner QR - À venir</Text>
  </View>
);

const SettingsScreen = () => (
  <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
    <Text>Paramètres - À venir</Text>
  </View>
);

// Types de navigation
export type AuthStackParamList = {
  Login: undefined;
};

export type MainTabParamList = {
  Dashboard: undefined;
  WorkOrders: undefined;
  Scanner: undefined;
  Settings: undefined;
};

export type RootStackParamList = {
  MainTabs: undefined;
  // On ajoute les détails plus tard
};

// Stack navigateurs
const AuthStack = createStackNavigator<AuthStackParamList>();
const MainTab = createBottomTabNavigator<MainTabParamList>();
const RootStack = createStackNavigator<RootStackParamList>();

// Navigateur d'authentification
const AuthNavigator: React.FC = () => (
  <AuthStack.Navigator screenOptions={{ headerShown: false }}>
    <AuthStack.Screen name="Login" component={LoginScreen} />
  </AuthStack.Navigator>
);

// Navigation par onglets principale
const MainTabNavigator: React.FC = () => (
  <MainTab.Navigator
    screenOptions={{
      headerShown: false,
      tabBarActiveTintColor: theme.colors.primary[500],
      tabBarInactiveTintColor: theme.colors.gray[500],
      tabBarStyle: {
        backgroundColor: theme.colors.background.primary,
        borderTopColor: theme.colors.gray[200],
        paddingBottom: Platform.OS === 'ios' ? 20 : 10,
        height: Platform.OS === 'ios' ? 85 : 65,
      },
      tabBarLabelStyle: {
        fontSize: theme.typography.sizes.xs,
        fontWeight: '600',
      },
    }}
  >
    <MainTab.Screen
      name="Dashboard"
      component={DashboardScreen}
      options={{
        title: 'Tableau de bord',
        tabBarIcon: ({ color, size }) => (
          <Icon name="home" size={size} color={color} />
        ),
      }}
    />
    <MainTab.Screen
      name="WorkOrders"
      component={WorkOrderListScreen}
      options={{
        title: 'Mes tâches',
        tabBarIcon: ({ color, size }) => (
          <Icon name="clipboard" size={size} color={color} />
        ),
      }}
    />
    <MainTab.Screen
      name="Scanner"
      component={QRScannerScreen}
      options={{
        title: 'Scanner',
        tabBarIcon: ({ color, size }) => (
          <Icon name="camera" size={size} color={color} />
        ),
      }}
    />
    <MainTab.Screen
      name="Settings"
      component={SettingsScreen}
      options={{
        title: 'Paramètres',
        tabBarIcon: ({ color, size }) => (
          <Icon name="settings" size={size} color={color} />
        ),
      }}
    />
  </MainTab.Navigator>
);

// Navigateur principal SIMPLIFIÉ
const MainNavigator: React.FC = () => (
  <RootStack.Navigator
    screenOptions={{
      headerStyle: {
        backgroundColor: theme.colors.primary[500],
      },
      headerTintColor: theme.colors.background.primary,
      headerTitleStyle: {
        fontWeight: 'bold',
      },
    }}
  >
    <RootStack.Screen
      name="MainTabs"
      component={MainTabNavigator}
      options={{ headerShown: false }}
    />
  </RootStack.Navigator>
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

export default AppNavigator;