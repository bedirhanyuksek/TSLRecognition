import React from 'react';
import {StyleSheet, Text, View} from 'react-native';
import {palette} from '../theme/palette';

type Props = {
  activeGloss: string;
};

export function AvatarStage({activeGloss}: Props) {
  return (
    <View style={styles.avatarStage}>
      <Text style={styles.avatarFigure}>╲○╱</Text>
      <Text style={styles.avatarTitle}>Unity Avatar Alanı</Text>
      <Text style={styles.avatarHint}>
        Android Unity Library burada gömülü çalışacak.
      </Text>
      <View style={styles.avatarOverlay}>
        <Text style={styles.avatarOverlayMuted}>Şu an</Text>
        <Text style={styles.avatarOverlayText}>{activeGloss}</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  avatarStage: {
    alignItems: 'center',
    backgroundColor: '#E0DDD8',
    borderRadius: 12,
    height: 318,
    justifyContent: 'center',
    overflow: 'hidden',
  },
  avatarFigure: {
    color: palette.accent,
    fontSize: 64,
    fontWeight: '200',
  },
  avatarTitle: {
    color: palette.text,
    fontSize: 20,
    fontWeight: '800',
    marginTop: 8,
  },
  avatarHint: {
    color: palette.secondary,
    fontSize: 13,
    marginTop: 4,
  },
  avatarOverlay: {
    backgroundColor: 'rgba(0,0,0,0.54)',
    bottom: 0,
    left: 0,
    padding: 12,
    position: 'absolute',
    right: 0,
  },
  avatarOverlayMuted: {
    color: 'rgba(255,255,255,0.72)',
    fontSize: 12,
  },
  avatarOverlayText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '800',
    marginTop: 2,
  },
});
