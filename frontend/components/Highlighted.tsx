import { splitSentences, type WordRange } from '@/lib/useReader';

type Props = {
  text: string;
  speech: string;
  active: boolean;
  sentence: number;
  wordRange: WordRange;
};

export function currentWord(
  text: string,
  speech: string,
  sentence: number,
  wordRange: WordRange,
): string | null {
  if (!wordRange || text !== speech) return null;
  const sentences = splitSentences(speech);
  const part = sentences[sentence];
  if (!part) return null;
  const word = part.slice(wordRange[0], wordRange[1]).replace(/[.,;:!?]+$/, '');
  return word || null;
}

export function Highlighted({ text, speech, active, sentence, wordRange }: Props) {
  if (!active || !wordRange || text !== speech) return <>{text}</>;
  const sentences = splitSentences(speech);
  const part = sentences[sentence];
  if (!part) return <>{text}</>;
  const offset = text.indexOf(part);
  if (offset < 0) return <>{text}</>;
  const start = offset + wordRange[0];
  const end = offset + wordRange[1];
  if (end <= start) return <>{text}</>;
  return (
    <>
      {text.slice(0, start)}
      <mark className="rounded bg-ac px-0.5 text-onac">{text.slice(start, end)}</mark>
      {text.slice(end)}
    </>
  );
}
