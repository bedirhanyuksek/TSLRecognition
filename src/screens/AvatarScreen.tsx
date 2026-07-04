import React from 'react';
import {Pressable, ScrollView, StyleSheet, Text, TextInput, View} from 'react-native';
import {AvatarStage} from '../components/AvatarStage';
import {Card} from '../components/Card';
import {GlossChip} from '../components/GlossChip';
import {PrimaryButton} from '../components/PrimaryButton';
import {SectionLabel} from '../components/SectionLabel';
import {palette} from '../theme/palette';

type Props = {
  text: string;
  glosses: string[];
  activeGloss: string;
  activeIndex: number;
  isPlaying: boolean;
  status: string;
  onTextChange: (value: string) => void;
  onConvert: () => void;
  onPrevious: () => void;
  onNext: () => void;
  onPlayToggle: () => void;
};

export function AvatarScreen({
  text,
  glosses,
  activeGloss,
  activeIndex,
  isPlaying,
  status,
  onTextChange,
  onConvert,
  onPrevious,
  onNext,
  onPlayToggle,
}: Props) {
  const hasGlosses = glosses.length > 0;

  return (
    <ScrollView showsVerticalScrollIndicator={false}>
      <View style={styles.headerColumn}>
        <Text style={styles.title}>Avatar</Text>
        <Text style={styles.subtitle}>Yazıyı işaret animasyonuna dönüştür</Text>
      </View>

      <Card>
        <AvatarStage activeGloss={activeGloss} />

        <View style={styles.playbackRow}>
          <Pressable style={styles.iconButton} onPress={onPrevious}>
            <Text style={styles.iconButtonText}>‹</Text>
          </Pressable>
          <Pressable style={styles.playButton} onPress={onPlayToggle}>
            <Text style={styles.playButtonText}>{isPlaying ? 'Duraklat' : 'Oynat'}</Text>
          </Pressable>
          <Pressable style={styles.iconButton} onPress={onNext}>
            <Text style={styles.iconButtonText}>›</Text>
          </Pressable>
          <Text style={styles.progressText}>
            {hasGlosses ? `${Math.min(activeIndex + 1, glosses.length)} / ${glosses.length}` : '-'}
          </Text>
        </View>
        <Text style={styles.statusText}>{status}</Text>
      </Card>

      <Card>
        <SectionLabel>Metin</SectionLabel>
        <TextInput
          value={text}
          onChangeText={onTextChange}
          placeholder="Örn: ben seni seviyorum"
          placeholderTextColor={palette.tertiary}
          multiline
          style={styles.textInput}
        />
        <PrimaryButton label="İşarete Çevir" onPress={onConvert} />
      </Card>

      <Card>
        <SectionLabel>Gloss Önizleme</SectionLabel>
        {hasGlosses ? (
          <View style={styles.glossLine}>
            {glosses.map((gloss, index) => (
              <React.Fragment key={`${gloss}-${index}`}>
                <GlossChip active={index === activeIndex}>{gloss}</GlossChip>
                {index < glosses.length - 1 && <Text style={styles.arrow}>›</Text>}
              </React.Fragment>
            ))}
          </View>
        ) : (
          <Text style={styles.emptyPreview}>Henüz gloss oluşturulmadı.</Text>
        )}
        <Text style={styles.noteText}>
          Desteklenmeyen kelimeler avatar kuyruğunda uyarı olarak gösterilecek.
        </Text>
      </Card>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  headerColumn: {
    marginBottom: 8,
  },
  title: {
    color: palette.text,
    fontSize: 22,
    fontWeight: '700',
  },
  subtitle: {
    color: palette.secondary,
    fontSize: 13,
    marginTop: 2,
  },
  playbackRow: {
    alignItems: 'center',
    flexDirection: 'row',
    gap: 10,
    marginTop: 12,
  },
  iconButton: {
    alignItems: 'center',
    backgroundColor: palette.accentSoft,
    borderRadius: 10,
    height: 40,
    justifyContent: 'center',
    width: 42,
  },
  iconButtonText: {
    color: palette.accent,
    fontSize: 28,
    fontWeight: '700',
  },
  playButton: {
    alignItems: 'center',
    backgroundColor: palette.accent,
    borderRadius: 10,
    flex: 1,
    height: 40,
    justifyContent: 'center',
  },
  playButtonText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '800',
  },
  progressText: {
    color: palette.secondary,
    fontSize: 13,
    fontWeight: '700',
  },
  statusText: {
    color: palette.secondary,
    fontSize: 12,
    fontWeight: '700',
    marginTop: 8,
  },
  textInput: {
    backgroundColor: palette.panel,
    borderRadius: 8,
    color: palette.text,
    fontSize: 16,
    marginBottom: 10,
    minHeight: 78,
    padding: 12,
    textAlignVertical: 'top',
  },
  glossLine: {
    alignItems: 'center',
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
  },
  arrow: {
    color: palette.tertiary,
    fontSize: 18,
    fontWeight: '800',
  },
  emptyPreview: {
    color: palette.tertiary,
    fontSize: 14,
    fontWeight: '700',
  },
  noteText: {
    color: palette.secondary,
    fontSize: 12,
    lineHeight: 18,
    marginTop: 10,
  },
});
