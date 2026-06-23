import React, {useCallback, useEffect, useMemo, useRef, useState} from 'react';
import {StatusBar, StyleSheet, useWindowDimensions, View} from 'react-native';
import {SafeAreaProvider, useSafeAreaInsets} from 'react-native-safe-area-context';
import {TabBar} from './src/components/TabBar';
import {AvatarScreen} from './src/screens/AvatarScreen';
import {HistoryScreen} from './src/screens/HistoryScreen';
import {LiveScreen} from './src/screens/LiveScreen';
import {SettingsScreen} from './src/screens/SettingsScreen';
import {
  checkBackendHealth,
  discoverBackendUrl,
  predictFrameFiles,
} from './src/services/inferenceService';
import {speakTurkish} from './src/services/speechService';
import {palette} from './src/theme/palette';
import type {
  BackendStatus,
  CameraPosition,
  HistoryItem,
  LiveInferenceStatus,
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
  const [backendUrl, setBackendUrl] = useState(
    'http://Bedirhan-MacBook-Air.local:8000',
  );
  const [backendStatus, setBackendStatus] = useState<BackendStatus>({
    state: 'idle',
    message: 'Test edilmedi',
  });
  const [liveInferenceStatus, setLiveInferenceStatus] =
    useState<LiveInferenceStatus>({
      running: false,
      busy: false,
      message: 'Hazır',
    });
  const captureWindowRef = useRef<(() => Promise<string[]>) | null>(null);
  const lastAcceptedGlossRef = useRef<string | null>(null);
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

  async function testBackend() {
    setBackendStatus({state: 'checking', message: 'Kontrol ediliyor'});
    try {
      const health = await checkBackendHealth(backendUrl);
      const ready = Object.values(health.models).every(Boolean);
      setBackendStatus({
        state: ready ? 'ready' : 'error',
        message: ready ? 'Model hazır' : 'Model dosyası eksik',
      });
      setCurrentPrediction(
        ready
          ? {
              gloss: 'backend_hazir',
              display: 'Backend hazır',
              confidence: 1,
            }
          : null,
      );
    } catch (error) {
      setBackendStatus({
        state: 'error',
        message: error instanceof Error ? error.message : 'Backend hatası',
      });
      setCurrentPrediction(null);
    }
  }

  const speakText = useCallback((text: string) => {
    speakTurkish(text).catch(error => {
      console.warn('TextToSpeech error', error);
    });
  }, []);

  const acceptPrediction = useCallback((next: Prediction) => {
    if (next.confidence < confidenceThreshold) {
      return;
    }
    if (lastAcceptedGlossRef.current === next.gloss) {
      setCurrentPrediction(next);
      return;
    }
    lastAcceptedGlossRef.current = next.gloss;
    setCurrentPrediction(next);
    setCommittedWords(previous => {
      const nextWords = [...previous, next.gloss];
      const meaningfulSentence = buildMeaningfulSentence(nextWords);
      if (autoSpeak && meaningfulSentence) {
        speakText(meaningfulSentence);
      }
      return nextWords;
    });
  }, [autoSpeak, confidenceThreshold, speakText]);

  const runLiveInferenceTick = useCallback(async () => {
    const captureWindow = captureWindowRef.current;
    if (!captureWindow) {
      setLiveInferenceStatus(previous => ({
        ...previous,
        message: 'Kamera hazır değil',
      }));
      return;
    }

    setLiveInferenceStatus(previous => ({
      ...previous,
      busy: true,
      message: 'Frame penceresi işleniyor',
    }));
    try {
      const framePaths = await captureWindow();
      const prediction = await predictFrameFiles(backendUrl, framePaths);
      if (prediction.hasSign && prediction.gloss && prediction.display) {
        acceptPrediction({
          gloss: prediction.gloss,
          display: prediction.display,
          confidence: prediction.confidence,
        });
        setLiveInferenceStatus(previous => ({
          ...previous,
          busy: false,
          message: `${prediction.display} (${Math.round(prediction.confidence * 100)}%)`,
        }));
      } else {
        setCurrentPrediction(null);
        setLiveInferenceStatus(previous => ({
          ...previous,
          busy: false,
          message: prediction.error || 'İşaret yok',
        }));
      }
    } catch (error) {
      setLiveInferenceStatus(previous => ({
        ...previous,
        busy: false,
        message: error instanceof Error ? error.message : 'Canlı tahmin hatası',
      }));
    }
  }, [acceptPrediction, backendUrl]);

  function toggleLiveInference() {
    setLiveInferenceStatus(previous => ({
      running: !previous.running,
      busy: false,
      message: !previous.running ? 'Başlatıldı' : 'Durduruldu',
    }));
  }

  useEffect(() => {
    if (!liveInferenceStatus.running || liveInferenceStatus.busy) {
      return;
    }
    const timeout = setTimeout(() => {
      runLiveInferenceTick();
    }, 250);
    return () => clearTimeout(timeout);
  }, [
    liveInferenceStatus.busy,
    liveInferenceStatus.running,
    runLiveInferenceTick,
  ]);

  async function autoDiscoverBackend() {
    setBackendStatus({state: 'checking', message: 'Backend aranıyor'});
    try {
      const discoveredUrl = await discoverBackendUrl(backendUrl);
      setBackendUrl(discoveredUrl);
      const health = await checkBackendHealth(discoveredUrl);
      const ready = Object.values(health.models).every(Boolean);
      setBackendStatus({
        state: ready ? 'ready' : 'error',
        message: ready ? `Bulundu: ${discoveredUrl}` : 'Model dosyası eksik',
      });
    } catch (error) {
      setBackendStatus({
        state: 'error',
        message: error instanceof Error ? error.message : 'Backend bulunamadı',
      });
    }
  }

  function speakCurrentOutput() {
    const fallback = currentPrediction?.display ?? '';
    speakText(naturalSentence || fallback);
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
    lastAcceptedGlossRef.current = null;
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
            backendStatus={backendStatus}
            liveInferenceStatus={liveInferenceStatus}
            onCameraPositionChange={setCameraPosition}
            onCaptureWindowReady={captureWindow => {
              captureWindowRef.current = captureWindow;
            }}
            onAutoSpeakChange={setAutoSpeak}
            onMock={testBackend}
            onLiveToggle={toggleLiveInference}
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
            backendUrl={backendUrl}
            backendStatus={backendStatus}
            modelMode={modelMode}
            onAutoSpeakChange={setAutoSpeak}
            onCameraPositionChange={setCameraPosition}
            onConfidenceThresholdChange={setConfidenceThreshold}
            onBackendUrlChange={setBackendUrl}
            onBackendDiscover={autoDiscoverBackend}
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
