import React, {useMemo, useState} from 'react';
import {StatusBar, StyleSheet, useWindowDimensions, View} from 'react-native';
import {SafeAreaProvider, useSafeAreaInsets} from 'react-native-safe-area-context';
import {TabBar} from './src/components/TabBar';
import {mockPredictions} from './src/data/mockPredictions';
import {AvatarScreen} from './src/screens/AvatarScreen';
import {HistoryScreen} from './src/screens/HistoryScreen';
import {LiveScreen} from './src/screens/LiveScreen';
import {SettingsScreen} from './src/screens/SettingsScreen';
import {speakTurkish} from './src/services/speechService';
import {palette} from './src/theme/palette';
import type {
  CameraPosition,
  HistoryItem,
  Prediction,
  TabKey,
} from './src/types/translation';
import {
  buildMeaningfulSentence,
  buildSentence,
  tokenizeTurkish,
} from './src/utils/translation';

function App() {
  return (
    <SafeAreaProvider>
      <MainApp />
    </SafeAreaProvider>
  );
}

function MainApp() {
  const insets = useSafeAreaInsets();
  const {height} = useWindowDimensions();
  const [tab, setTab] = useState<TabKey>('live');
  const [predictionIndex, setPredictionIndex] = useState(0);
  const [currentPrediction, setCurrentPrediction] = useState<Prediction | null>(
    null,
  );
  const [committedWords, setCommittedWords] = useState<string[]>([]);
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [autoSpeak, setAutoSpeak] = useState(true);
  const [cameraPosition, setCameraPosition] =
    useState<CameraPosition>('front');
  const [confidenceThreshold, setConfidenceThreshold] = useState(0.7);
  const [modelMode, setModelMode] = useState<'server' | 'device'>('server');
  const [avatarText, setAvatarText] = useState('ben seni seviyorum');
  const [avatarGlosses, setAvatarGlosses] = useState(['ben', 'sen', 'sevmek']);
  const [avatarIndex, setAvatarIndex] = useState(0);
  const [isAvatarPlaying, setIsAvatarPlaying] = useState(false);

  const naturalSentence = useMemo(
    () => buildSentence(committedWords),
    [committedWords],
  );
  const activeAvatarGloss = avatarGlosses[avatarIndex] ?? '-';
  const liveCameraHeight = Math.min(430, Math.max(372, Math.round(height * 0.48)));

  function simulatePrediction() {
    const next = mockPredictions[predictionIndex % mockPredictions.length];
    setPredictionIndex(predictionIndex + 1);
    setCurrentPrediction(next);

    setCommittedWords(previous => {
      if (previous[previous.length - 1] === next.gloss) {
        return previous;
      }

      const nextWords = [...previous, next.gloss];
      const meaningfulSentence = buildMeaningfulSentence(nextWords);
      if (autoSpeak && meaningfulSentence) {
        speakText(meaningfulSentence);
      }
      return nextWords;
    });
  }

  function speakCurrentOutput() {
    const fallback = currentPrediction?.display ?? '';
    speakText(naturalSentence || fallback);
  }

  function speakText(text: string) {
    speakTurkish(text).catch(error => {
      console.warn('TextToSpeech error', error);
    });
  }

  function clearSession() {
    if (committedWords.length > 0) {
      setHistory(previous => [
        {
          id: Date.now(),
          words: committedWords,
          sentence: naturalSentence,
          time: new Date().toLocaleTimeString('tr-TR', {
            hour: '2-digit',
            minute: '2-digit',
          }),
        },
        ...previous,
      ]);
    }

    setCommittedWords([]);
    setCurrentPrediction(null);
  }

  function removeLastWord() {
    setCommittedWords(previous => previous.slice(0, -1));
  }

  function convertAvatarText() {
    const glosses = tokenizeTurkish(avatarText);
    setAvatarGlosses(glosses.length ? glosses : ['-']);
    setAvatarIndex(0);
  }

  return (
    <View style={[styles.root, {paddingTop: Math.max(insets.top, 10)}]}>
      <StatusBar barStyle="dark-content" backgroundColor={palette.background} />
      <View style={styles.appShell}>
        {tab === 'live' && (
          <LiveScreen
            cameraHeight={liveCameraHeight}
            currentPrediction={currentPrediction}
            cameraPosition={cameraPosition}
            committedWords={committedWords}
            naturalSentence={naturalSentence}
            autoSpeak={autoSpeak}
            onCameraPositionChange={setCameraPosition}
            onAutoSpeakChange={setAutoSpeak}
            onMock={simulatePrediction}
            onSpeak={speakCurrentOutput}
            onClear={clearSession}
            onUndo={removeLastWord}
          />
        )}

        {tab === 'avatar' && (
          <AvatarScreen
            text={avatarText}
            glosses={avatarGlosses}
            activeGloss={activeAvatarGloss}
            activeIndex={avatarIndex}
            isPlaying={isAvatarPlaying}
            onTextChange={setAvatarText}
            onConvert={convertAvatarText}
            onPrevious={() => setAvatarIndex(Math.max(0, avatarIndex - 1))}
            onNext={() =>
              setAvatarIndex(Math.min(avatarGlosses.length - 1, avatarIndex + 1))
            }
            onPlayToggle={() => setIsAvatarPlaying(!isAvatarPlaying)}
          />
        )}

        {tab === 'history' && (
          <HistoryScreen history={history} onClear={() => setHistory([])} />
        )}

        {tab === 'settings' && (
          <SettingsScreen
            autoSpeak={autoSpeak}
            cameraPosition={cameraPosition}
            confidenceThreshold={confidenceThreshold}
            modelMode={modelMode}
            onAutoSpeakChange={setAutoSpeak}
            onCameraPositionChange={setCameraPosition}
            onConfidenceThresholdChange={setConfidenceThreshold}
            onModelModeChange={setModelMode}
          />
        )}
      </View>

      <TabBar activeTab={tab} bottomInset={insets.bottom} onChange={setTab} />
    </View>
  );
}

const styles = StyleSheet.create({
  root: {
    backgroundColor: palette.background,
    flex: 1,
  },
  appShell: {
    flex: 1,
    paddingHorizontal: 14,
    paddingTop: 4,
  },
});

export default App;
