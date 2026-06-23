export type TabKey = 'live' | 'avatar' | 'history' | 'settings';

export type CameraPosition = 'front' | 'back';

export type Prediction = {
  gloss: string;
  display: string;
  confidence: number;
};

export type HistoryItem = {
  id: number;
  words: string[];
  sentence: string;
  time: string;
};
