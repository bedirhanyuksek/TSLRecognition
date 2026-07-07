import NetInfo from '@react-native-community/netinfo';
import { NativeModules } from 'react-native';

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
const HOTSPOT_BACKEND_CANDIDATE = 'http://10.177.14.24:8000';

type TidNetworkModule = {
  getWifiIpAddress?: () => Promise<string | null>;
};

const tidNetwork = NativeModules.TidNetwork as TidNetworkModule | undefined;

function normalizeBaseUrl(baseUrl: string): string {
  return baseUrl.replace(/\/+$/, '');
}

async function fetchWithTimeout(url: string, timeoutMs = REQUEST_TIMEOUT_MS) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetch(url, { signal: controller.signal });
  } finally {
    clearTimeout(timeout);
  }
}

export async function checkBackendHealth(
  baseUrl: string,
): Promise<BackendHealth> {
  const response = await fetchWithTimeout(
    `${normalizeBaseUrl(baseUrl)}/health`,
  );
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

function hostsForPrefix(prefix: string, ownHost?: number): string[] {
  const likelyHosts = [1, 2, 3, 4, 5, 10, 20, 50, 100, 101, 102, 150, 200, 254];
  const hosts = Array.from(
    new Set([
      ...likelyHosts,
      ...Array.from({ length: 254 }, (_, index) => index + 1),
    ]),
  ).filter(host => host !== ownHost);
  return hosts.map(host => `http://${prefix}.${host}:${DISCOVERY_PORT}`);
}

function fallbackSubnetCandidates(): string[] {
  return [
    '192.168.1',
    '192.168.0',
    '192.168.43',
    '192.168.49',
    '192.168.137',
    '172.20.10',
    '10.0.0',
    '10.227.122',
    '10.177.14',
  ].flatMap(prefix => hostsForPrefix(prefix));
}

function subnetCandidates(ipAddress: string): string[] {
  const parts = ipAddress.split('.');
  if (parts.length !== 4) {
    return [];
  }
  const prefix = parts.slice(0, 3).join('.');
  const ownHost = Number(parts[3]);
  return hostsForPrefix(prefix, ownHost);
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

async function getDeviceWifiIpAddress(): Promise<string | null> {
  const netState = await NetInfo.fetch();
  const netInfoIp =
    netState.type === 'wifi' &&
    netState.details &&
    'ipAddress' in netState.details
      ? netState.details.ipAddress
      : null;
  if (netInfoIp) {
    return netInfoIp;
  }
  return tidNetwork?.getWifiIpAddress?.() ?? null;
}

export async function discoverBackendUrl(currentUrl: string): Promise<string> {
  const directCandidates = [
    currentUrl,
    HOTSPOT_BACKEND_CANDIDATE,
    LOCAL_HOSTNAME_CANDIDATE,
    'http://10.0.2.2:8000',
  ].filter(Boolean);

  const directFound = await findReachableUrl(directCandidates);
  if (directFound) {
    return directFound;
  }

  const ipAddress = await getDeviceWifiIpAddress();
  const networkCandidates = ipAddress
    ? subnetCandidates(ipAddress)
    : fallbackSubnetCandidates();

  const subnetFound = await findReachableUrl(networkCandidates);
  if (subnetFound) {
    return subnetFound;
  }

  if (!ipAddress) {
    throw new Error('Wi-Fi IP alınamadı; yaygın ağlarda backend bulunamadı');
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
