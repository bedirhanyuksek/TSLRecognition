import React from 'react';
import {Pressable, ScrollView, StyleSheet, Text, View} from 'react-native';
import {Card} from '../components/Card';
import {GlossChip} from '../components/GlossChip';
import {SectionLabel} from '../components/SectionLabel';
import {palette} from '../theme/palette';
import type {HistoryItem} from '../types/translation';

type Props = {
  history: HistoryItem[];
  onClear: () => void;
};

export function HistoryScreen({history, onClear}: Props) {
  return (
    <ScrollView showsVerticalScrollIndicator={false}>
      <View style={styles.headerRow}>
        <Text style={styles.title}>Geçmiş</Text>
        <Pressable onPress={onClear}>
          <Text style={styles.clearText}>Temizle</Text>
        </Pressable>
      </View>

      {history.length === 0 ? (
        <View style={styles.emptyHistory}>
          <Text style={styles.emptyTitle}>Henüz kayıt yok</Text>
          <Text style={styles.emptyText}>
            Canlı çeviride temizlenen oturumlar burada listelenecek.
          </Text>
        </View>
      ) : (
        history.map(item => (
          <Card key={item.id}>
            <View style={styles.historyTop}>
              <SectionLabel>{item.time}</SectionLabel>
              <Text style={styles.smallMuted}>{item.words.length} işaret</Text>
            </View>
            <View style={styles.chipWrap}>
              {item.words.map((word, index) => (
                <GlossChip key={`${word}-${index}`}>{word}</GlossChip>
              ))}
            </View>
            <Text style={styles.sentence}>{item.sentence}</Text>
          </Card>
        ))
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
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
  clearText: {
    color: palette.danger,
    fontSize: 14,
    fontWeight: '800',
  },
  emptyHistory: {
    alignItems: 'center',
    backgroundColor: palette.surface,
    borderRadius: 8,
    marginTop: 24,
    padding: 24,
  },
  emptyTitle: {
    color: palette.text,
    fontSize: 18,
    fontWeight: '800',
    marginBottom: 6,
  },
  emptyText: {
    color: palette.secondary,
    fontSize: 14,
    lineHeight: 20,
    textAlign: 'center',
  },
  historyTop: {
    alignItems: 'center',
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  smallMuted: {
    color: palette.tertiary,
    fontSize: 12,
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
});
