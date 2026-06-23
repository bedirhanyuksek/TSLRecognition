import React, {PropsWithChildren} from 'react';
import {StyleSheet, View, ViewStyle} from 'react-native';
import {palette} from '../theme/palette';

type Props = PropsWithChildren<{
  style?: ViewStyle;
}>;

export function Card({children, style}: Props) {
  return <View style={[styles.card, style]}>{children}</View>;
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: palette.surface,
    borderRadius: 8,
    marginBottom: 8,
    padding: 14,
    shadowColor: '#000000',
    shadowOffset: {width: 0, height: 1},
    shadowOpacity: 0.07,
    shadowRadius: 3,
  },
});
