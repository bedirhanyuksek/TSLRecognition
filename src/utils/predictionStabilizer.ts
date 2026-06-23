import type {BackendPrediction} from '../services/inferenceService';
import type {Prediction, PredictionCandidate} from '../types/translation';

export type StabilizerState = {
  recent: PredictionCandidate[];
  lastAcceptedGloss: string | null;
  lastAcceptedAt: number;
};

export type StabilizerResult =
  | {
      accepted: true;
      prediction: Prediction;
      reason: string;
    }
  | {
      accepted: false;
      reason: string;
    };

const WINDOW_SIZE = 5;
const REQUIRED_REPEATS = 3;
const MIN_TOP_MARGIN = 0.12;
export function createStabilizerState(): StabilizerState {
  return {
    recent: [],
    lastAcceptedGloss: null,
    lastAcceptedAt: 0,
  };
}

export function resetStabilizerState(state: StabilizerState) {
  state.recent = [];
  state.lastAcceptedGloss = null;
  state.lastAcceptedAt = 0;
}

export function evaluatePredictionCandidate(
  state: StabilizerState,
  backendPrediction: BackendPrediction,
  confidenceThreshold: number,
  now = Date.now(),
): StabilizerResult {
  if (
    !backendPrediction.hasSign ||
    !backendPrediction.gloss ||
    !backendPrediction.display
  ) {
    resetStabilizerState(state);
    return {accepted: false, reason: backendPrediction.error || 'İşaret yok'};
  }

  const candidate: PredictionCandidate = {
    gloss: backendPrediction.gloss,
    display: backendPrediction.display,
    confidence: backendPrediction.confidence,
    top5: backendPrediction.top5 ?? [],
  };

  state.recent = [...state.recent, candidate].slice(-WINDOW_SIZE);

  if (candidate.confidence < confidenceThreshold) {
    return {
      accepted: false,
      reason: `Güven düşük: ${Math.round(candidate.confidence * 100)}%`,
    };
  }

  const margin = getTopMargin(candidate);
  if (margin < MIN_TOP_MARGIN) {
    return {
      accepted: false,
      reason: `Kararsız tahmin: fark ${Math.round(margin * 100)}%`,
    };
  }

  const repeatCount = state.recent.filter(
    item => item.gloss === candidate.gloss,
  ).length;
  if (repeatCount < REQUIRED_REPEATS) {
    return {
      accepted: false,
      reason: `Stabil değil: ${repeatCount}/${REQUIRED_REPEATS}`,
    };
  }

  if (state.lastAcceptedGloss === candidate.gloss) {
    return {accepted: false, reason: 'Aynı kelime bekletiliyor'};
  }

  state.lastAcceptedGloss = candidate.gloss;
  state.lastAcceptedAt = now;
  state.recent = [];

  return {
    accepted: true,
    prediction: {
      gloss: candidate.gloss,
      display: candidate.display,
      confidence: candidate.confidence,
      top5: candidate.top5,
    },
    reason: 'Kabul edildi',
  };
}

function getTopMargin(candidate: PredictionCandidate) {
  const top = candidate.top5 ?? [];
  if (top.length < 2) {
    return 1;
  }
  return Math.max(0, top[0].confidence - top[1].confidence);
}
