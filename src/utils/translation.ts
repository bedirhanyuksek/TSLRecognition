export function tokenizeTurkish(text: string) {
  return text
    .toLocaleLowerCase('tr-TR')
    .replaceAll('seni', 'sen')
    .replaceAll('seviyorum', 'sevmek')
    .replaceAll('yardım', 'yardim')
    .replaceAll('ı', 'i')
    .replaceAll('ğ', 'g')
    .replaceAll('ü', 'u')
    .replaceAll('ş', 's')
    .replaceAll('ö', 'o')
    .replaceAll('ç', 'c')
    .split(/\s+/)
    .filter(Boolean);
}

export function buildSentence(words: string[]) {
  const key = words.join(' ');
  const exact = getExactSentences();

  if (exact[key]) {
    return exact[key];
  }

  if (words.length === 0) {
    return '';
  }

  return `${words.map(word => word.replace('_', ' ')).join(' ')}.`;
}

export function buildMeaningfulSentence(words: string[]) {
  const key = words.join(' ');
  return getExactSentences()[key] ?? '';
}

function getExactSentences(): Record<string, string> {
  return {
    'ben sen sevmek': 'Ben seni seviyorum.',
    'yardim istemek': 'Yardım istiyorum.',
    'ben yardim istemek': 'Yardım istiyorum.',
    'ben doktor istemek': 'Doktor istiyorum.',
  };
}
