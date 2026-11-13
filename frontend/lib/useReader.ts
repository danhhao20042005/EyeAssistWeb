'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { TYPE_LABEL, type Block, type BlockType } from '@/lib/demoDocument';

export const SPEED_MIN = 0.5;
export const SPEED_MAX = 2;
export const SPEED_STEP = 0.25;

export function splitSentences(text: string): string[] {
  const parts = text.split(/(?<=[.!?])\s+/).filter(Boolean);
  return parts.length ? parts : [text];
}

type Options = {
  blocks: Block[];
  announce: (message: string) => void;
  onNavigate?: (type: BlockType) => void;
};

export type WordRange = [number, number] | null;

export function useReader({ blocks, announce, onNavigate }: Options) {
  const onNavigateRef = useRef(onNavigate);
  onNavigateRef.current = onNavigate;
  const [current, setCurrent] = useState(0);
  const [sentence, setSentence] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState(1);
  const [wordRange, setWordRange] = useState<WordRange>(null);

  const playingRef = useRef(false);
  const tokenRef = useRef(0);
  const speedRef = useRef(1);
  const positionRef = useRef({ block: 0, sentence: 0 });

  const supported = typeof window !== 'undefined' && 'speechSynthesis' in window;

  const cancelSpeech = useCallback(() => {
    tokenRef.current += 1;
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
  }, []);

  const setPosition = useCallback((block: number, sent: number) => {
    positionRef.current = { block, sentence: sent };
    setCurrent(block);
    setSentence(sent);
    setWordRange(null);
  }, []);

  const stopPlaying = useCallback(() => {
    playingRef.current = false;
    setPlaying(false);
    setWordRange(null);
    cancelSpeech();
  }, [cancelSpeech]);

  const speakAt = useCallback(
    (blockIndex: number, sentenceIndex: number) => {
      if (!supported) {
        announce('Trình duyệt này không hỗ trợ đọc thành tiếng');
        stopPlaying();
        return;
      }
      const block = blocks[blockIndex];
      if (!block) {
        stopPlaying();
        announce('Đã đọc hết tài liệu');
        return;
      }
      const sentences = splitSentences(block.speech);
      if (sentenceIndex >= sentences.length) {
        speakAt(blockIndex + 1, 0);
        return;
      }
      cancelSpeech();
      const token = tokenRef.current;
      setPosition(blockIndex, sentenceIndex);
      const utterance = new SpeechSynthesisUtterance(sentences[sentenceIndex]);
      utterance.lang = 'vi-VN';
      utterance.rate = speedRef.current;
      utterance.onboundary = (event) => {
        if (token !== tokenRef.current) return;
        const text = sentences[sentenceIndex];
        const start = event.charIndex;
        const match = /^\S+/.exec(text.slice(start));
        const end = match ? start + match[0].length : start;
        setWordRange([start, end]);
      };
      utterance.onend = () => {
        if (token !== tokenRef.current || !playingRef.current) return;
        speakAt(blockIndex, sentenceIndex + 1);
      };
      utterance.onerror = (event) => {
        if (token !== tokenRef.current) return;
        if (event.error === 'canceled' || event.error === 'interrupted') return;
        stopPlaying();
        announce('Không đọc được nội dung này');
      };
      window.speechSynthesis.speak(utterance);
    },
    [announce, blocks, cancelSpeech, setPosition, stopPlaying, supported],
  );

  const describeBlock = useCallback(
    (index: number) => {
      const block = blocks[index];
      return `${TYPE_LABEL[block.type]} ${index + 1} trên ${blocks.length}`;
    },
    [blocks],
  );

  const goTo = useCallback(
    (index: number) => {
      const clamped = Math.min(blocks.length - 1, Math.max(0, index));
      setPosition(clamped, 0);
      announce(describeBlock(clamped));
      if (playingRef.current) speakAt(clamped, 0);
      else onNavigateRef.current?.(blocks[clamped].type);
    },
    [announce, blocks, describeBlock, setPosition, speakAt],
  );

  const next = useCallback(() => {
    const index = positionRef.current.block;
    if (index >= blocks.length - 1) {
      announce('Đây là mục cuối cùng');
      return;
    }
    goTo(index + 1);
  }, [announce, blocks.length, goTo]);

  const prev = useCallback(() => {
    const index = positionRef.current.block;
    if (index <= 0) {
      announce('Đây là mục đầu tiên');
      return;
    }
    goTo(index - 1);
  }, [announce, goTo]);

  const jumpToType = useCallback(
    (type: BlockType, direction: 1 | -1) => {
      const start = positionRef.current.block;
      for (let i = start + direction; i >= 0 && i < blocks.length; i += direction) {
        if (blocks[i].type === type) {
          goTo(i);
          return;
        }
      }
      const name = TYPE_LABEL[type].toLowerCase();
      announce(direction === 1 ? `Không còn ${name} phía sau` : `Không còn ${name} phía trước`);
    },
    [announce, blocks, goTo],
  );

  const play = useCallback(() => {
    playingRef.current = true;
    setPlaying(true);
    announce('Đang đọc');
    speakAt(positionRef.current.block, positionRef.current.sentence);
  }, [announce, speakAt]);

  const pause = useCallback(() => {
    stopPlaying();
    announce('Đã tạm dừng');
  }, [announce, stopPlaying]);

  const toggle = useCallback(() => {
    if (playingRef.current) pause();
    else play();
  }, [pause, play]);

  const stop = useCallback(() => {
    stopPlaying();
    setPosition(positionRef.current.block, 0);
    announce('Đã dừng đọc');
  }, [announce, setPosition, stopPlaying]);

  const repeat = useCallback(() => {
    setPosition(positionRef.current.block, 0);
    playingRef.current = true;
    setPlaying(true);
    speakAt(positionRef.current.block, 0);
  }, [setPosition, speakAt]);

  const stepSentence = useCallback(
    (direction: 1 | -1) => {
      const { block, sentence: sent } = positionRef.current;
      const sentences = splitSentences(blocks[block].speech);
      let nextBlock = block;
      let nextSentence = sent + direction;
      if (nextSentence < 0) {
        nextBlock = block - 1;
        if (nextBlock < 0) return;
        nextSentence = splitSentences(blocks[nextBlock].speech).length - 1;
      } else if (nextSentence >= sentences.length) {
        nextBlock = block + 1;
        if (nextBlock >= blocks.length) return;
        nextSentence = 0;
      }
      setPosition(nextBlock, nextSentence);
      if (playingRef.current) speakAt(nextBlock, nextSentence);
      else announce(describeBlock(nextBlock));
    },
    [announce, blocks, describeBlock, setPosition, speakAt],
  );

  const changeSpeed = useCallback(
    (delta: number) => {
      const value = Math.round(Math.min(SPEED_MAX, Math.max(SPEED_MIN, speedRef.current + delta)) * 100) / 100;
      if (value === speedRef.current) {
        announce(delta > 0 ? 'Đã đạt tốc độ tối đa' : 'Đã đạt tốc độ chậm nhất');
        return;
      }
      speedRef.current = value;
      setSpeed(value);
      announce(`Tốc độ đọc ${value.toFixed(2).replace(/0$/, '')} lần`);
      if (playingRef.current) speakAt(positionRef.current.block, positionRef.current.sentence);
    },
    [announce, speakAt],
  );

  const describeFigure = useCallback(() => {
    const block = blocks[positionRef.current.block];
    if (block.type !== 'figure' || !block.description) {
      announce('Mục này không phải hình hoặc biểu đồ');
      return;
    }
    if (!supported) {
      announce(block.description);
      return;
    }
    stopPlaying();
    const token = tokenRef.current;
    const utterance = new SpeechSynthesisUtterance(block.description);
    utterance.lang = 'vi-VN';
    utterance.rate = speedRef.current;
    utterance.onend = () => {
      if (token === tokenRef.current) setWordRange(null);
    };
    window.speechSynthesis.speak(utterance);
    announce('Đang đọc mô tả hình');
  }, [announce, blocks, stopPlaying, supported]);

  useEffect(() => {
    return () => {
      tokenRef.current += 1;
      if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
        window.speechSynthesis.cancel();
      }
    };
  }, []);

  return {
    current,
    sentence,
    playing,
    speed,
    wordRange,
    supported,
    goTo,
    next,
    prev,
    jumpToType,
    play,
    pause,
    toggle,
    stop,
    repeat,
    stepSentence,
    changeSpeed,
    describeFigure,
  };
}

export type Reader = ReturnType<typeof useReader>;
