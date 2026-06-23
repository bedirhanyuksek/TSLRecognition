import React from 'react';
import {ScrollView, StyleSheet, Switch, Text, View} from 'react-native';
import {CameraPanel} from '../components/CameraPanel';
import {Card} from '../components/Card';
import {GlossChip} from '../components/GlossChip';
import {PrimaryButton} from '../components/PrimaryButton';
import {SectionLabel} from '../components/SectionLabel';
import {palette} from '../theme/palette';
import type {BackendStatus, CameraPosition, Prediction} from '../types/translation';
import {percent} from '../utils/format';

type Props = {
  cameraHeight: number;
  currentPrediction: Prediction | null;
  cameraPosition: CameraPosition;
  committedWords: string[];
  naturalSentence: string;
  autoSpeak: boolean;
  backendStatus: BackendStatus;
  onCameraPositionChange: (position: CameraPosition) => void;
  onAutoSpeakChange: (value: boolean) => void;
  onMock: () => void;
  onSpeak: () => void;
  onClear: () => void;
  onUndo: () => void;
};

export function LiveScreen({
  cameraHeight,
  currentPrediction,
  cameraPosition,
  committedWords,
  naturalSentence,
  autoSpeak,
  backendStatus,
  onCameraPositionChange,
  onAutoSpeakChange,
  onMock,
  onSpeak,
  onClear,
  onUndo,
}: Props) {
  return (
    <ScrollView
      showsVerticalScrollIndicator={false}
      contentContainerStyle={styles.scrollContent}>
      <View style={styles.headerRow}>
        <Text style={styles.title}>Canlı Çeviri</Text>
        <View style={styles.readyChip}>
          <View style={styles.readyDot} />
          <Text style={styles.readyText}>Model hazır</Text>
        </View>
      </View>

      <CameraPanel
        height={cameraHeight}
        prediction={currentPrediction}
        cameraPosition={cameraPosition}
        onCameraPositionChange={onCameraPositionChange}
      />

      <Card>
        <View style={styles.backendRow}>
          <Text style={styles.backendLabel}>Backend</Text>
          <Text style={[styles.backendValue, styles[backendStatus.state]]}>
            {backendStatus.message}
          </Text>
        </View>
      </Card>

      <Card>
        <View style={styles.predictionRow}>
          <Text style={styles.bigPrediction}>
            {currentPrediction?.display ?? 'işaret yok'}
          </Text>
          <Text style={styles.confidence}>
            Güven: {currentPrediction ? percent(currentPrediction.confidence) : '-'}
          </Text>
        </View>
        <View style={styles.altRow}>
          <Text style={styles.smallMuted}>alternatif</Text>
          {['okul', 'dakika', 'yardım'].map(item => (
            <Text key={item} style={styles.neutralChip}>
              {item}
            </Text>
          ))}
        </View>
      </Card>

      <Card>
        <SectionLabel>Çeviri Akışı</SectionLabel>
        {committedWords.length === 0 ? (
          <Text style={styles.emptyText}>Kabul edilen işaretler burada birikecek.</Text>
        ) : (
          <View style={styles.chipWrap}>
            {committedWords.map((word, index) => (
              <GlossChip
                key={`${word}-${index}`}
                active={index === committedWords.length - 1}>
                {word}
              </GlossChip>
            ))}
          </View>
        )}
        <Text style={styles.sentence}>
          {naturalSentence || 'Doğal Türkçe çıktı bekleniyor.'}
        </Text>
      </Card>

      <View style={styles.actionRow}>
        <PrimaryButton label="Backend Test" onPress={onMock} style={styles.flexButton} />
        <PrimaryButton label="Seslendir" variant="secondary" onPress={onSpeak} />
      </View>

      <View style={styles.actionRow}>
        <PrimaryButton label="Geri Al" variant="secondary" onPress={onUndo} />
        <PrimaryButton label="Temizle" variant="danger" onPress={onClear} />
      </View>

      <View style={styles.switchRow}>
        <Text style={styles.switchLabel}>Otomatik ses</Text>
        <Switch
          value={autoSpeak}
          onValueChange={onAutoSpeakChange}
          thumbColor="#FFFFFF"
          trackColor={{false: palette.stroke, true: palette.accent}}
        />
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  scrollContent: {
    paddingBottom: 8,
  },
  headerRow: {
    alignItems: 'center',
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  title: {
    color: palette.text,
    fontSize: 22,
    fontWeight: '700',
  },
  readyChip: {
    alignItems: 'center',
    backgroundColor: '#DFF3EA',
    borderRadius: 12,
    flexDirection: 'row',
    gap: 6,
    paddingHorizontal: 10,
    paddingVertical: 6,
  },
  readyDot: {
    backgroundColor: palette.success,
    borderRadius: 4,
    height: 7,
    width: 7,
  },
  readyText: {
    color: palette.success,
    fontSize: 12,
    fontWeight: '700',
  },
  predictionRow: {
    alignItems: 'baseline',
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  backendRow: {
    alignItems: 'center',
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  backendLabel: {
    color: palette.secondary,
    fontSize: 13,
    fontWeight: '800',
  },
  backendValue: {
    flex: 1,
    fontSize: 13,
    fontWeight: '800',
    marginLeft: 10,
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
  bigPrediction: {
    color: palette.text,
    flex: 1,
    fontSize: 30,
    fontWeight: '800',
  },
  confidence: {
    color: palette.secondary,
    fontSize: 13,
  },
  altRow: {
    alignItems: 'center',
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
    marginTop: 8,
  },
  smallMuted: {
    color: palette.tertiary,
    fontSize: 12,
  },
  neutralChip: {
    backgroundColor: palette.panel,
    borderRadius: 6,
    color: palette.secondary,
    fontSize: 13,
    fontWeight: '600',
    overflow: 'hidden',
    paddingHorizontal: 9,
    paddingVertical: 5,
  },
  emptyText: {
    color: palette.secondary,
    fontSize: 14,
    lineHeight: 20,
  },
  chipWrap: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
  },
  sentence: {
    color: palette.text,
    fontSize: 16,
    fontWeight: '700',
    lineHeight: 22,
    marginTop: 12,
  },
  actionRow: {
    flexDirection: 'row',
    gap: 7,
    marginBottom: 10,
  },
  flexButton: {
    flex: 1,
  },
  switchRow: {
    alignItems: 'center',
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 6,
  },
  switchLabel: {
    color: palette.secondary,
    fontSize: 15,
    fontWeight: '600',
  },
});
