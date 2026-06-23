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
};

function normalizeBaseUrl(baseUrl: string): string {
  return baseUrl.replace(/\/+$/, '');
}

export async function checkBackendHealth(baseUrl: string): Promise<BackendHealth> {
  const response = await fetch(`${normalizeBaseUrl(baseUrl)}/health`);
  if (!response.ok) {
    throw new Error(`Backend health failed: ${response.status}`);
  }
  return response.json();
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
