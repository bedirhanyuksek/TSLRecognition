import {NativeModules} from 'react-native';

type TidSpeechModule = {
  speak: (text: string) => Promise<boolean>;
  stop: () => void;
};

const nativeSpeech = NativeModules.TidSpeech as TidSpeechModule | undefined;

export async function speakTurkish(text: string) {
  if (!nativeSpeech) {
    throw new Error('TidSpeech native module bulunamadi.');
  }

  return nativeSpeech.speak(text);
}

export function stopSpeech() {
  nativeSpeech?.stop();
}
