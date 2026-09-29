import React from 'react';
import {Pressable, StyleSheet, Text, View} from 'react-native';
import {palette} from '../theme/palette';
import type {TabKey} from '../types/translation';

const tabs: Array<{key: TabKey; label: string; symbol: string}> = [
  {key: 'live', label: 'Canlı', symbol: '◉'},
  {key: 'avatar', label: 'Avatar', symbol: '◇'},
  {key: 'history', label: 'Geçmiş', symbol: '≡'},
  {key: 'settings', label: 'Ayarlar', symbol: '⚙'},
];

type Props = {
  activeTab: TabKey;
  bottomInset: number;
  onChange: (tab: TabKey) => void;
};

export function TabBar({activeTab, bottomInset, onChange}: Props) {
  return (
    <View style={[styles.tabBar, {paddingBottom: Math.max(bottomInset, 8)}]}>
      {tabs.map(tab => {
        const active = activeTab === tab.key;

        return (
          <Pressable
            key={tab.key}
            onPress={() => onChange(tab.key)}
            style={[styles.tabButton, active && styles.tabButtonActive]}>
            <Text style={[styles.tabSymbol, active && styles.tabTextActive]}>
              {tab.symbol}
            </Text>
            <Text style={[styles.tabLabel, active && styles.tabTextActive]}>
              {tab.label}
            </Text>
          </Pressable>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  tabBar: {
    backgroundColor: palette.surface,
    borderTopColor: palette.stroke,
    borderTopWidth: 1,
    flexDirection: 'row',
    paddingHorizontal: 10,
    paddingTop: 8,
  },
  tabButton: {
    alignItems: 'center',
    borderRadius: 10,
    flex: 1,
    paddingVertical: 7,
  },
  tabButtonActive: {
    backgroundColor: palette.accentSoft,
  },
  tabSymbol: {
    color: palette.tertiary,
    fontSize: 18,
    fontWeight: '800',
  },
  tabLabel: {
    color: palette.secondary,
    fontSize: 12,
    fontWeight: '700',
    marginTop: 2,
  },
  tabTextActive: {
    color: palette.accent,
  },
});
