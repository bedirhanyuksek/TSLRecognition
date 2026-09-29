import React from 'react';
import {StyleSheet, Text} from 'react-native';
import {palette} from '../theme/palette';

type Props = {
  children: string;
  active?: boolean;
};

export function GlossChip({children, active}: Props) {
  return (
    <Text style={[styles.chip, active && styles.active]}>
      {children.replace('_', ' ')}
    </Text>
  );
}

const styles = StyleSheet.create({
  chip: {
    backgroundColor: palette.accentSoft,
    borderRadius: 6,
    color: palette.accent,
    fontSize: 14,
    fontWeight: '700',
    overflow: 'hidden',
    paddingHorizontal: 10,
    paddingVertical: 6,
  },
  active: {
    borderColor: palette.accent,
    borderWidth: 1,
  },
});
