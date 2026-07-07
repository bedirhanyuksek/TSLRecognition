import React from 'react';
import {
  Pressable,
  ScrollView,
  StyleSheet,
  Switch,
  Text,
  TextInput,
  View,
} from 'react-native';
import { Card } from '../components/Card';
import { PrimaryButton } from '../components/PrimaryButton';
import { SectionLabel } from '../components/SectionLabel';
import { palette } from '../theme/palette';
import type { BackendStatus, CameraPosition } from '../types/translation';

type Props = {
  autoSpeak: boolean;
  cameraPosition: CameraPosition;
  confidenceThreshold: number;
  backendUrl: string;
  backendStatus: BackendStatus;
  modelMode: 'server' | 'device';
  onAutoSpeakChange: (value: boolean) => void;
  onCameraPositionChange: (position: CameraPosition) => void;
  onConfidenceThresholdChange: (value: number) => void;
  onBackendUrlChange: (value: string) => void;
  onBackendDiscover: () => void;
  onModelModeChange: (mode: 'server' | 'device') => void;
};

export function SettingsScreen({
  autoSpeak,
  cameraPosition,
  confidenceThreshold,
  backendUrl,
  backendStatus,
  modelMode,
  onAutoSpeakChange,
  onCameraPositionChange,
  onConfidenceThresholdChange,
  onBackendUrlChange,
  onBackendDiscover,
  onModelModeChange,
}: Props) {
  return (
    <ScrollView
      showsVerticalScrollIndicator={false}
      contentContainerStyle={styles.scrollContent}
    >
      <View style={styles.headerRow}>
        <Text style={styles.title}>Ayarlar</Text>
        <Text style={styles.caption}>Prototip kontrol merkezi</Text>
      </View>

      <Card>
        <SectionLabel>Ses</SectionLabel>
        <View style={styles.settingRow}>
          <View style={styles.settingCopy}>
            <Text style={styles.settingTitle}>
              Anlamlı cümleyi otomatik oku
            </Text>
            <Text style={styles.settingText}>
              Kelimeler doğal cümleye dönüşünce seslendirme yapılır.
            </Text>
          </View>
          <Switch
            value={autoSpeak}
            onValueChange={onAutoSpeakChange}
            thumbColor="#FFFFFF"
            trackColor={{ false: palette.stroke, true: palette.accent }}
          />
        </View>
      </Card>

      <Card>
        <SectionLabel>Kamera</SectionLabel>
        <View style={styles.segment}>
          <SegmentButton
            active={cameraPosition === 'front'}
            label="Ön"
            onPress={() => onCameraPositionChange('front')}
          />
          <SegmentButton
            active={cameraPosition === 'back'}
            label="Arka"
            onPress={() => onCameraPositionChange('back')}
          />
        </View>
        <Text style={styles.settingText}>
          Canlı çeviri ekranındaki kamera rozeti de aynı ayarı değiştirir.
        </Text>
      </Card>

      <Card>
        <SectionLabel>Model</SectionLabel>
        <View style={styles.segment}>
          <SegmentButton
            active={modelMode === 'server'}
            label="Sunucu"
            onPress={() => onModelModeChange('server')}
          />
          <SegmentButton
            active={modelMode === 'device'}
            label="Cihaz"
            onPress={() => onModelModeChange('device')}
          />
        </View>
        <View style={styles.thresholdRow}>
          <Text style={styles.settingTitle}>Güven eşiği</Text>
          <Text style={styles.thresholdValue}>
            {Math.round(confidenceThreshold * 100)}%
          </Text>
        </View>
        <View style={styles.stepRow}>
          <Pressable
            onPress={() =>
              onConfidenceThresholdChange(
                Math.max(0.7, confidenceThreshold - 0.05),
              )
            }
            style={styles.stepButton}
          >
            <Text style={styles.stepText}>-</Text>
          </Pressable>
          <View style={styles.track}>
            <View
              style={[
                styles.trackFill,
                { width: `${Math.round(confidenceThreshold * 100)}%` },
              ]}
            />
          </View>
          <Pressable
            onPress={() =>
              onConfidenceThresholdChange(
                Math.min(0.95, confidenceThreshold + 0.05),
              )
            }
            style={styles.stepButton}
          >
            <Text style={styles.stepText}>+</Text>
          </Pressable>
        </View>
        <Text style={[styles.settingTitle, styles.backendTitle]}>
          Backend adresi
        </Text>
        <TextInput
          autoCapitalize="none"
          autoCorrect={false}
          keyboardType="url"
          onChangeText={onBackendUrlChange}
          placeholder="http://10.177.14.24:8000"
          placeholderTextColor={palette.tertiary}
          style={styles.input}
          value={backendUrl}
        />
        <View style={styles.backendActions}>
          <PrimaryButton
            label="Otomatik Bul"
            onPress={onBackendDiscover}
            style={styles.backendButton}
            variant="secondary"
          />
          <Text style={[styles.backendStatus, styles[backendStatus.state]]}>
            {backendStatus.message}
          </Text>
        </View>
      </Card>
    </ScrollView>
  );
}

function SegmentButton({
  active,
  label,
  onPress,
}: {
  active: boolean;
  label: string;
  onPress: () => void;
}) {
  return (
    <Pressable
      onPress={onPress}
      style={[styles.segmentButton, active && styles.segmentButtonActive]}
    >
      <Text style={[styles.segmentText, active && styles.segmentTextActive]}>
        {label}
      </Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  scrollContent: {
    paddingBottom: 8,
  },
  headerRow: {
    marginBottom: 10,
  },
  title: {
    color: palette.text,
    fontSize: 22,
    fontWeight: '800',
  },
  caption: {
    color: palette.secondary,
    fontSize: 13,
    fontWeight: '600',
    marginTop: 2,
  },
  settingRow: {
    alignItems: 'center',
    flexDirection: 'row',
    gap: 12,
    justifyContent: 'space-between',
  },
  settingCopy: {
    flex: 1,
  },
  settingTitle: {
    color: palette.text,
    fontSize: 15,
    fontWeight: '800',
  },
  settingText: {
    color: palette.secondary,
    fontSize: 13,
    lineHeight: 18,
    marginTop: 6,
  },
  segment: {
    backgroundColor: palette.panel,
    borderRadius: 10,
    flexDirection: 'row',
    gap: 6,
    padding: 4,
  },
  segmentButton: {
    alignItems: 'center',
    borderRadius: 8,
    flex: 1,
    minHeight: 38,
    justifyContent: 'center',
  },
  segmentButtonActive: {
    backgroundColor: palette.surface,
  },
  segmentText: {
    color: palette.secondary,
    fontSize: 14,
    fontWeight: '800',
  },
  segmentTextActive: {
    color: palette.accent,
  },
  thresholdRow: {
    alignItems: 'center',
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 16,
  },
  thresholdValue: {
    color: palette.accent,
    fontSize: 15,
    fontWeight: '900',
  },
  stepRow: {
    alignItems: 'center',
    flexDirection: 'row',
    gap: 10,
    marginTop: 12,
  },
  stepButton: {
    alignItems: 'center',
    backgroundColor: palette.panel,
    borderRadius: 9,
    height: 38,
    justifyContent: 'center',
    width: 44,
  },
  stepText: {
    color: palette.text,
    fontSize: 22,
    fontWeight: '800',
  },
  backendTitle: {
    marginTop: 16,
  },
  input: {
    backgroundColor: palette.panel,
    borderColor: palette.stroke,
    borderRadius: 10,
    borderWidth: 1,
    color: palette.text,
    fontSize: 14,
    fontWeight: '700',
    marginTop: 8,
    minHeight: 44,
    paddingHorizontal: 12,
  },
  backendActions: {
    alignItems: 'center',
    flexDirection: 'row',
    gap: 10,
    marginTop: 10,
  },
  backendButton: {
    minWidth: 122,
  },
  backendStatus: {
    flex: 1,
    fontSize: 12,
    fontWeight: '800',
    textAlign: 'right',
  },
  idle: {
    color: palette.tertiary,
  },
  checking: {
    color: palette.secondary,
  },
  ready: {
    color: palette.success,
  },
  error: {
    color: palette.danger,
  },
  track: {
    backgroundColor: palette.panel,
    borderRadius: 6,
    flex: 1,
    height: 10,
    overflow: 'hidden',
  },
  trackFill: {
    backgroundColor: palette.accent,
    borderRadius: 6,
    height: '100%',
  },
});
