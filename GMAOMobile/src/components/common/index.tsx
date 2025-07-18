import React from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  TextInput,
  StyleSheet,
  ActivityIndicator,
  ViewStyle,
  TextStyle,
  TextInputProps,
} from 'react-native';
import { theme } from '../../styles/theme'; // Assure-toi que ce chemin est correct

// ==============================================================================
// CARD COMPONENT
// ==============================================================================
interface CardProps {
  children: React.ReactNode;
  style?: ViewStyle;
}

export const Card: React.FC<CardProps> = ({ children, style }) => (
  <View style={[styles.card, style]}>
    {children}
  </View>
);

// ==============================================================================
// INPUT COMPONENT
// ==============================================================================
interface InputProps extends TextInputProps {
  label?: string;
  error?: string;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

export const Input: React.FC<InputProps> = ({
  label,
  error,
  leftIcon,
  rightIcon,
  style,
  ...props
}) => (
  <View style={styles.inputContainer}>
    {label && <Text style={styles.inputLabel}>{label}</Text>}
    <View style={[styles.inputWrapper, error && styles.inputError]}>
      {leftIcon && <View style={styles.inputLeftIcon}>{leftIcon}</View>}
      <TextInput
        style={[styles.input, leftIcon && styles.inputWithLeftIcon, style]}
        placeholderTextColor={theme.colors.slate[400]}
        {...props}
      />
      {rightIcon && <View style={styles.inputRightIcon}>{rightIcon}</View>}
    </View>
    {error && <Text style={styles.inputErrorText}>{error}</Text>}
  </View>
);

// ==============================================================================
// BUTTON COMPONENT
// ==============================================================================
interface ButtonProps {
  title?: string;
  children?: React.ReactNode;
  onPress: () => void;
  variant?: 'primary' | 'secondary' | 'outline';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
  disabled?: boolean;
  fullWidth?: boolean;
  style?: ViewStyle;
  titleStyle?: TextStyle;
}

export const Button: React.FC<ButtonProps> = ({
  title,
  children,
  onPress,
  variant = 'primary',
  size = 'md',
  loading = false,
  disabled = false,
  fullWidth = false,
  style,
  titleStyle,
}) => {
  const buttonStyle = [
    styles.button,
    styles[`button${capitalize(variant)}`],
    styles[`button${capitalize(size)}`],
    fullWidth && styles.buttonFullWidth,
    disabled && styles.buttonDisabled,
    style,
  ];

  const textStyle = [
    styles.buttonText,
    styles[`buttonText${capitalize(variant)}`],
    disabled && styles.buttonTextDisabled,
    titleStyle,
  ];

  const content = children || title;

  return (
    <TouchableOpacity
      style={buttonStyle}
      onPress={onPress}
      disabled={disabled || loading}
      activeOpacity={0.8}
    >
      {loading ? (
        <ActivityIndicator
          color={variant === 'primary' ? theme.colors.text.inverse : theme.colors.primary[500]}
          size="small"
        />
      ) : (
        <Text style={textStyle}>{content}</Text>
      )}
    </TouchableOpacity>
  );
};

// ==============================================================================
// BADGE COMPONENT
// ==============================================================================
interface BadgeProps {
  label: string;
  variant?: 'success' | 'warning' | 'error' | 'info' | 'default';
  size?: 'sm' | 'md';
}

export const Badge: React.FC<BadgeProps> = ({
  label,
  variant = 'default',
  size = 'md',
}) => (
  <View style={[
    styles.badge,
    styles[`badge${capitalize(variant)}`],
    styles[`badge${capitalize(size)}`],
  ]}>
    <Text style={[
      styles.badgeText,
      styles[`badgeText${capitalize(variant)}`],
    ]}>
      {label}
    </Text>
  </View>
);

// ==============================================================================
// LOADER COMPONENT
// ==============================================================================
interface LoaderProps {
  size?: 'small' | 'large';
  color?: string;
}

export const Loader: React.FC<LoaderProps> = ({
  size = 'large',
  color = theme.colors.primary[500],
}) => (
  <View style={styles.loader}>
    <ActivityIndicator size={size} color={color} />
  </View>
);

// ==============================================================================
// STYLES
// ==============================================================================
const styles = StyleSheet.create({
  // Card
  card: {
    backgroundColor: theme.colors.background.card,
    borderRadius: theme.borderRadius.lg,
    padding: theme.spacing['4'],
    ...theme.shadows.md,
  },

  // Input
  inputContainer: {
    marginBottom: theme.spacing['4'],
  },
  inputLabel: {
    fontSize: theme.typography.sizes.sm,
    fontWeight: theme.typography.weights.semibold as any,
    color: theme.colors.text.primary,
    marginBottom: theme.spacing['1'],
  },
  inputWrapper: {
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: theme.colors.slate[300],
    borderRadius: theme.borderRadius.md,
    backgroundColor: theme.colors.background.primary,
    minHeight: 48,
  },
  inputError: {
    borderColor: theme.colors.error[500],
  },
  input: {
    flex: 1,
    fontSize: theme.typography.sizes.md,
    color: theme.colors.text.primary,
    paddingVertical: theme.spacing['3'],
    paddingHorizontal: theme.spacing['3'],
  },
  inputWithLeftIcon: {
    paddingLeft: 0,
  },
  inputLeftIcon: {
    paddingLeft: theme.spacing['3'],
  },
  inputRightIcon: {
    paddingRight: theme.spacing['3'],
  },
  inputErrorText: {
    fontSize: theme.typography.sizes.xs,
    color: theme.colors.error[500],
    marginTop: theme.spacing['1'],
  },

  // Button
  button: {
    borderRadius: theme.borderRadius.md,
    justifyContent: 'center',
    alignItems: 'center',
    flexDirection: 'row',
    minHeight: 48,
  },
  buttonPrimary: {
    backgroundColor: theme.colors.primary[500],
  },
  buttonSecondary: {
    backgroundColor: theme.colors.slate[200],
  },
  buttonOutline: {
    backgroundColor: 'transparent',
    borderWidth: 1,
    borderColor: theme.colors.primary[500],
  },
  buttonDisabled: {
    opacity: 0.5,
  },
  buttonSm: {
    paddingVertical: theme.spacing['2'],
    paddingHorizontal: theme.spacing['3'],
    minHeight: 36,
  },
  buttonMd: {
    paddingVertical: theme.spacing['3'],
    paddingHorizontal: theme.spacing['4'],
    minHeight: 48,
  },
  buttonLg: {
    paddingVertical: theme.spacing['4'],
    paddingHorizontal: theme.spacing['5'],
    minHeight: 56,
  },
  buttonFullWidth: {
    width: '100%',
  },
  buttonText: {
    fontWeight: theme.typography.weights.semibold as any,
    fontSize: theme.typography.sizes.md,
  },
  buttonTextPrimary: {
    color: theme.colors.text.inverse,
  },
  buttonTextSecondary: {
    color: theme.colors.text.primary,
  },
  buttonTextOutline: {
    color: theme.colors.primary[500],
  },
  buttonTextDisabled: {
    opacity: 0.7,
  },

  // Badge
  badge: {
    borderRadius: theme.borderRadius.full,
  },
  badgeDefault: {
    backgroundColor: theme.colors.slate[200],
  },
  badgeSuccess: {
    backgroundColor: theme.colors.success[100],
  },
  badgeWarning: {
    backgroundColor: theme.colors.warning[100],
  },
  badgeError: {
    backgroundColor: theme.colors.error[100],
  },
  badgeInfo: {
    backgroundColor: theme.colors.info[100],
  },
  badgeSm: {
    paddingHorizontal: theme.spacing['2'],
    paddingVertical: theme.spacing['1'],
  },
  badgeMd: {
    paddingHorizontal: theme.spacing['3'],
    paddingVertical: theme.spacing['1'],
  },
  badgeText: {
    fontSize: theme.typography.sizes.xs,
    fontWeight: theme.typography.weights.semibold as any,
  },
  badgeTextDefault: {
    color: theme.colors.text.secondary,
  },
  badgeTextSuccess: {
    color: theme.colors.success[700],
  },
  badgeTextWarning: {
    color: theme.colors.warning[700],
  },
  badgeTextError: {
    color: theme.colors.error[700],
  },
  badgeTextInfo: {
    color: theme.colors.info[700],
  },

  // Loader
  loader: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
});

// Utilitaire
const capitalize = (s: string) => s.charAt(0).toUpperCase() + s.slice(1);
