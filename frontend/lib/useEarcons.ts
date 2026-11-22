'use client';

import { useCallback } from 'react';
import { useAccessibility } from '@/lib/accessibility';
import { earconPlayer, type EarconName } from '@/lib/earcons';

export function useEarcons() {
  const { earcons, earconVolume } = useAccessibility();

  /** Trả về thời lượng âm báo (ms) để chờ xong rồi mới đọc; 0 nếu âm báo đang tắt. */
  const play = useCallback(
    (name: EarconName, options?: { force?: boolean }): number => {
      if (!earcons && !options?.force) return 0;
      earconPlayer.setVolume(earconVolume);
      return earconPlayer.play(name);
    },
    [earcons, earconVolume],
  );

  const playSequence = useCallback(
    (names: EarconName[]): number => {
      if (!earcons) return 0;
      earconPlayer.setVolume(earconVolume);
      return earconPlayer.playSequence(names);
    },
    [earcons, earconVolume],
  );

  const cancel = useCallback(() => earconPlayer.cancel(), []);

  const startProcessing = useCallback(() => {
    if (!earcons) return;
    earconPlayer.setVolume(earconVolume);
    earconPlayer.startProcessing();
  }, [earcons, earconVolume]);

  const stopProcessing = useCallback(() => earconPlayer.stopProcessing(), []);

  return { play, playSequence, cancel, startProcessing, stopProcessing };
}
