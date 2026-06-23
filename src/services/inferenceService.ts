import NetInfo from '@react-native-community/netinfo';

export type BackendHealth = {
  ok: boolean;
  models: {
    word_model: boolean;
    sign_gate: boolean;
    class_names: boolean;
    holistic_model: boolean;
  };
};

export type BackendPrediction = {
  hasSign: boolean;
  gloss: string | null;
  display: string | null;
  confidence: number;
  top5: Array<{
    gloss: string;
    display: string;
    confidence: number;
  }>;
  error?: string | null;
  frameCount?: number;
};

const REQUEST_TIMEOUT_MS = 1200;
const DISCOVERY_PORT = 8000;
const LOCAL_HOSTNAME_CANDIDATE = 'http://Bedirhan-MacBook-Air.local:8000';

function normalizeBaseUrl(baseUrl: string): string {
  return baseUrl.replace(/\/+$/, '');
}

async function fetchWithTimeout(url: string, timeoutMs = REQUEST_TIMEOUT_MS) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetch(url, {signal: controller.signal});
  } finally {
    clearTimeout(timeout);
  }
}

export async function checkBackendHealth(baseUrl: string): Promise<BackendHealth> {
  const response = await fetchWithTimeout(`${normalizeBaseUrl(baseUrl)}/health`);
  if (!response.ok) {
    throw new Error(`Backend health failed: ${response.status}`);
  }
  return response.json();
}

async function tryBackendUrl(baseUrl: string): Promise<string | null> {
  try {
    const health = await checkBackendHealth(baseUrl);
    if (health.ok) {
      return normalizeBaseUrl(baseUrl);
    }
  } catch {
    return null;
  }
  return null;
}

function subnetCandidates(ipAddress: string): string[] {
  const parts = ipAddress.split('.');
  if (parts.length !== 4) {
    return [];
  }
  const prefix = parts.slice(0, 3).join('.');
  const ownHost = Number(parts[3]);
  const likelyHosts = [1, 2, 3, 4, 5, 10, 20, 50, 100, 101, 102, 150, 200, 254];
  const hosts = Array.from(
    new Set([
      ...likelyHosts,
      ...Array.from({length: 254}, (_, index) => index + 1),
    ]),
  ).filter(host => host !== ownHost);
  return hosts.map(host => `http://${prefix}.${host}:${DISCOVERY_PORT}`);
}

async function findReachableUrl(candidates: string[]): Promise<string | null> {
  const batchSize = 24;
  for (let index = 0; index < candidates.length; index += batchSize) {
    const batch = candidates.slice(index, index + batchSize);
    const results = await Promise.all(batch.map(tryBackendUrl));
    const found = results.find(Boolean);
    if (found) {
      return found;
    }
  }
  return null;
}

export async function discoverBackendUrl(
  currentUrl: string,
): Promise<string> {
  const directCandidates = [
    currentUrl,
    LOCAL_HOSTNAME_CANDIDATE,
    'http://10.0.2.2:8000',
  ].filter(Boolean);

  const directFound = await findReachableUrl(directCandidates);
  if (directFound) {
    return directFound;
  }

  const netState = await NetInfo.fetch();
  const ipAddress =
    netState.type === 'wifi' && netState.details && 'ipAddress' in netState.details
      ? netState.details.ipAddress
      : null;

  if (!ipAddress) {
    throw new Error('Wi-Fi IP adresi alınamadı');
  }

  const subnetFound = await findReachableUrl(subnetCandidates(ipAddress));
  if (subnetFound) {
    return subnetFound;
  }

  throw new Error(`${ipAddress} ağı içinde backend bulunamadı`);
}

export async function predictImage(
  baseUrl: string,
  image: {
    uri: string;
    name: string;
    type: string;
  },
): Promise<BackendPrediction> {
  const payload = new FormData();
  payload.append('image', image as unknown as Blob);
  const response = await fetch(`${normalizeBaseUrl(baseUrl)}/predict/image`, {
    method: 'POST',
    body: payload,
  });
  if (!response.ok) {
    throw new Error(`Image prediction failed: ${response.status}`);
  }
  return response.json();
}

export async function predictFrameFiles(
  baseUrl: string,
  framePaths: string[],
): Promise<BackendPrediction> {
  const payload = new FormData();
  framePaths.forEach((path, index) => {
    payload.append('frames', {
      uri: `file://${path}`,
      name: `frame_${index}.jpg`,
      type: 'image/jpeg',
    } as unknown as Blob);
  });
  const response = await fetch(`${normalizeBaseUrl(baseUrl)}/predict/frames`, {
    method: 'POST',
    body: payload,
  });
  if (!response.ok) {
    throw new Error(`Frame prediction failed: ${response.status}`);
  }
  return response.json();
}
