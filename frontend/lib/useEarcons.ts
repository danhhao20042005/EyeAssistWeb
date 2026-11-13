'use client';

import { useCallback } from 'react';
import { useAccessibility } from '@/lib/accessibility';
import { earconPlayer, type EarconName } from '@/lib/earcons';

export function useEarcons() {
  const { earcons, earconVolume } = useAccessibility();

  const play = useCallback(
    (name: EarconName, options?: { force?: boolean }) => {
      if (!earcons && !options?.force) return;
      earconPlayer.setVolume(earconVolume);
      earconPlayer.play(name);
    },
    [earcons, earconVolume],
  );

  const stopProcessing = useCallback(() => earconPlayer.stopProcessing(), []);

  return { play, stopProcessing };
}
