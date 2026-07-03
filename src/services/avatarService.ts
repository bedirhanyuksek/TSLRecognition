import {NativeModules} from 'react-native';

type TidUnityAvatarModule = {
  isAvailable?: () => Promise<boolean>;
  open?: () => Promise<boolean>;
  playGlosses?: (glossCsv: string) => Promise<boolean>;
  playText?: (text: string) => Promise<boolean>;
  stop?: () => Promise<boolean>;
};

const nativeAvatar = NativeModules.TidUnityAvatar as
  | TidUnityAvatarModule
  | undefined;

function toGlossCsv(glosses: string[]) {
  return glosses
    .map(gloss => gloss.trim())
    .filter(Boolean)
    .join(',');
}

export async function isUnityAvatarAvailable() {
  if (!nativeAvatar?.isAvailable) {
    return false;
  }

  return nativeAvatar.isAvailable();
}

export async function playUnityGlosses(glosses: string[]) {
  if (!nativeAvatar?.playGlosses) {
    return false;
  }

  const glossCsv = toGlossCsv(glosses);
  if (!glossCsv) {
    return false;
  }

  return nativeAvatar.playGlosses(glossCsv);
}

export async function openUnityAvatar() {
  if (!nativeAvatar?.open) {
    return false;
  }

  return nativeAvatar.open();
}

export async function playUnityText(text: string) {
  if (!nativeAvatar?.playText) {
    return false;
  }

  return nativeAvatar.playText(text);
}

export async function stopUnityAvatar() {
  if (!nativeAvatar?.stop) {
    return false;
  }

  return nativeAvatar.stop();
}
