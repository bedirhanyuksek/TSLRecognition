import React, {useEffect, useState} from 'react';
import {Pressable, StyleSheet, Text, View} from 'react-native';
import {
  Camera,
  useCameraDevice,
  useCameraPermission,
} from 'react-native-vision-camera';
import {palette} from '../theme/palette';
import type {CameraPosition, Prediction} from '../types/translation';
import {percent} from '../utils/format';

type Props = {
  height: number;
  prediction: Prediction | null;
  cameraPosition: CameraPosition;
  onCameraPositionChange: (position: CameraPosition) => void;
};

export function CameraPanel({
  height,
  prediction,
  cameraPosition,
  onCameraPositionChange,
}: Props) {
  const device = useCameraDevice(cameraPosition);
  const {canRequestPermission, hasPermission, requestPermission} =
    useCameraPermission();
  const [permissionChecked, setPermissionChecked] = useState(false);

  useEffect(() => {
    let mounted = true;

    async function ensurePermission() {
      if (hasPermission) {
        if (mounted) {
          setPermissionChecked(true);
        }
        return;
      }

      if (canRequestPermission) {
        await requestPermission();
      }

      if (mounted) {
        setPermissionChecked(true);
      }
    }

    ensurePermission().catch(error => {
      console.warn('Camera permission error', error);
      if (mounted) {
        setPermissionChecked(true);
      }
    });

    return () => {
      mounted = false;
    };
  }, [canRequestPermission, hasPermission, requestPermission]);

  const canShowCamera = hasPermission && device != null;
  const cameraLabel = cameraPosition === 'front' ? 'Ön kamera' : 'Arka kamera';

  function toggleCamera() {
    onCameraPositionChange(cameraPosition === 'front' ? 'back' : 'front');
  }

  return (
    <View style={[styles.cameraBox, {height}]}>
      {canShowCamera && (
        <Camera
          device={device}
          isActive
          resizeMode="cover"
          style={StyleSheet.absoluteFill}
        />
      )}

      <View style={styles.cameraGrid} pointerEvents="none" />
      <View style={styles.cameraTopBar} pointerEvents="box-none">
        <Pressable
          accessibilityRole="button"
          accessibilityLabel={`${cameraLabel}. Kamerayı değiştir`}
          onPress={toggleCamera}
          style={({pressed}) => [
            styles.cameraPillButton,
            pressed && styles.cameraPillPressed,
          ]}>
          <Text style={styles.cameraPillText}>{cameraLabel}</Text>
        </Pressable>
        <Text style={styles.cameraPill}>
          Güven {prediction ? percent(prediction.confidence) : '-'}
        </Text>
      </View>

      {!canShowCamera && (
        <View style={styles.cameraCenter}>
          <Text style={styles.cameraIcon}>⌁</Text>
          <Text style={styles.cameraHint}>
            {!permissionChecked
              ? 'Kamera izni kontrol ediliyor'
              : hasPermission
                ? 'Ön kamera bulunamadı'
                : 'Kamera izni bekleniyor'}
          </Text>
        </View>
      )}

      <Text style={styles.debugText} pointerEvents="none">
        {hasPermission ? 'VisionCamera aktif' : 'Kamera izni yok'}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  cameraBox: {
    backgroundColor: palette.camera,
    borderRadius: 14,
    marginBottom: 8,
    overflow: 'hidden',
  },
  cameraGrid: {
    borderColor: 'rgba(255,255,255,0.08)',
    borderWidth: 1,
    bottom: 0,
    left: 0,
    position: 'absolute',
    right: 0,
    top: 0,
  },
  cameraTopBar: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    padding: 12,
  },
  cameraPill: {
    backgroundColor: 'rgba(255,255,255,0.14)',
    borderRadius: 10,
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: '700',
    overflow: 'hidden',
    paddingHorizontal: 10,
    paddingVertical: 6,
  },
  cameraPillButton: {
    backgroundColor: 'rgba(255,255,255,0.18)',
    borderColor: 'rgba(255,255,255,0.2)',
    borderRadius: 10,
    borderWidth: 1,
    paddingHorizontal: 10,
    paddingVertical: 6,
  },
  cameraPillPressed: {
    opacity: 0.7,
  },
  cameraPillText: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: '800',
  },
  cameraCenter: {
    alignItems: 'center',
    flex: 1,
    justifyContent: 'center',
    marginTop: -26,
  },
  cameraIcon: {
    color: palette.accent,
    fontSize: 64,
    fontWeight: '300',
  },
  cameraHint: {
    color: 'rgba(255,255,255,0.76)',
    fontSize: 14,
    marginTop: 8,
  },
  debugText: {
    bottom: 12,
    color: 'rgba(255,255,255,0.74)',
    fontSize: 11,
    left: 12,
    position: 'absolute',
  },
});
