import React from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  ActivityIndicator,
  StyleSheet,
  ViewStyle,
  TextStyle,
} from 'react-native';

// Types
interface ButtonProps {
  title: string;
  onPress: () => void;
  loading?: boolean;
  disabled?: boolean;
}

interface CardProps {
  children: React.ReactNode;
  style?: ViewStyle;
}

interface LoaderProps {
  text?: string;
}

// Composants
export const Button: React.FC<ButtonProps> = ({
  title,
  onPress,
  loading = false,
  disabled = false,
}) => (
  <TouchableOpacity
    style={[styles.button, disabled && styles.disabled]}
    onPress={onPress}
    disabled={disabled || loading}
  >
    {loading ? (
      <ActivityIndicator color="white" />
    ) : (
      <Text style={styles.buttonText}>{title}</Text>
    )}
  </TouchableOpacity>
);

export const Card: React.FC<CardProps> = ({ children, style = {} }) => (
  <View style={[styles.card, style]}>
    {children}
  </View>
);

export const Loader: React.FC<LoaderProps> = ({ text }) => (
  <View style={styles.loader}>
    <ActivityIndicator size="large" color="#3b82f6" />
    {text ? <Text style={styles.loaderText}>{text}</Text> : null}
  </View>
);

const styles = StyleSheet.create({
  button: {
    backgroundColor: '#3b82f6',
    padding: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  buttonText: {
    color: 'white',
    fontWeight: 'bold',
  },
  disabled: {
    opacity: 0.5,
  },
  card: {
    backgroundColor: 'white',
    borderRadius: 8,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
  },
  loader: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loaderText: {
    marginTop: 10,
    color: '#666',
  },
});
