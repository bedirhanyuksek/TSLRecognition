import React from 'react';
import {StyleSheet, Text} from 'react-native';
import {palette} from '../theme/palette';

type Props = {
  children: string;
};

export function SectionLabel({children}: Props) {
  return <Text style={styles.label}>{children}</Text>;
}

const styles = StyleSheet.create({
  label: {
    color: palette.tertiary,
    fontSize: 12,
    fontWeight: '800',
    letterSpacing: 0.8,
    marginBottom: 10,
    textTransform: 'uppercase',
  },
});
