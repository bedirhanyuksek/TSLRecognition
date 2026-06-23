import React from 'react';
import {Pressable, StyleSheet, Text, ViewStyle} from 'react-native';
import {palette} from '../theme/palette';

type Variant = 'primary' | 'secondary' | 'danger';

type Props = {
  label: string;
  variant?: Variant;
  style?: ViewStyle;
  onPress: () => void;
};

export function PrimaryButton({label, variant = 'primary', style, onPress}: Props) {
  return (
    <Pressable
      style={[styles.button, styles[variant], style]}
      onPress={onPress}>
      <Text style={[styles.text, styles[`${variant}Text`]]}>{label}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  button: {
    alignItems: 'center',
    borderRadius: 10,
    justifyContent: 'center',
    minHeight: 44,
    paddingHorizontal: 12,
  },
  primary: {
    backgroundColor: palette.accent,
  },
  secondary: {
    backgroundColor: palette.panel,
  },
  danger: {
    backgroundColor: palette.dangerSoft,
  },
  text: {
    fontSize: 14,
    fontWeight: '800',
  },
  primaryText: {
    color: '#FFFFFF',
  },
  secondaryText: {
    color: palette.text,
    fontSize: 13,
  },
  dangerText: {
    color: palette.danger,
    fontSize: 13,
  },
});
