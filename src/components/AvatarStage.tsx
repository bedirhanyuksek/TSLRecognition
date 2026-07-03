import React from 'react';
import {StyleSheet, Text, View} from 'react-native';
import {palette} from '../theme/palette';
import {UnityAvatarView} from './UnityAvatarView';

type Props = {
  activeGloss: string;
};

export function AvatarStage({activeGloss}: Props) {
  return (
    <View style={styles.avatarStage}>
      <UnityAvatarView style={StyleSheet.absoluteFill} />
      <View pointerEvents="none" style={styles.avatarOverlay}>
        <Text style={styles.avatarOverlayMuted}>Şu an</Text>
        <Text style={styles.avatarOverlayText}>{activeGloss}</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  avatarStage: {
    backgroundColor: '#E0DDD8',
    borderRadius: 12,
    height: 318,
    overflow: 'hidden',
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
