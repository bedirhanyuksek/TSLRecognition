export type TabKey = 'live' | 'avatar' | 'history' | 'settings';

export type CameraPosition = 'front' | 'back';

export type Prediction = {
  gloss: string;
  display: string;
  confidence: number;
  top5?: PredictionAlternative[];
};

export type PredictionAlternative = {
  gloss: string;
  display: string;
  confidence: number;
};

export type PredictionCandidate = Prediction & {
  top5: PredictionAlternative[];
};

export type HistoryItem = {
  id: number;
  words: string[];
  sentence: string;
  time: string;
};

export type BackendStatus = {
  state: 'idle' | 'checking' | 'ready' | 'error';
  message: string;
};

export type LiveInferenceStatus = {
  running: boolean;
  busy: boolean;
  message: string;
};
