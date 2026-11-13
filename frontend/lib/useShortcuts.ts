'use client';

import { useCallback, useEffect, type KeyboardEvent as ReactKeyboardEvent } from 'react';
import { useAccessibility, ZOOM_STEP } from '@/lib/accessibility';
import { SPEED_STEP, type Reader } from '@/lib/useReader';

function isEditable(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false;
  if (target.isContentEditable) return true;
  const tag = target.tagName;
  return tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT';
}

function isActivatable(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false;
  const tag = target.tagName;
  return tag === 'BUTTON' || tag === 'A' || tag === 'SUMMARY';
}

export function useGlobalShortcuts() {
  const { openHelp } = useAccessibility();

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'F1' && !event.ctrlKey && !event.altKey && !event.metaKey) {
        event.preventDefault();
        openHelp();
      }
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [openHelp]);
}

export function useViewerShortcuts(reader: Reader) {
  const a11y = useAccessibility();
  const {
    shortcutsEnabled,
    cycleContrast,
    changeZoom,
    resetZoom,
    toggleFollow,
    cycleZoomMode,
    toggleEarcons,
    openHelp,
    announce,
  } = a11y;

  return useCallback(
    (event: ReactKeyboardEvent<HTMLElement>) => {
      if (event.ctrlKey || event.altKey || event.metaKey || event.nativeEvent.isComposing) return;
      if (isEditable(event.target)) return;

      const key = event.key;
      const shift = event.shiftKey;
      const handled = () => {
        event.preventDefault();
        event.stopPropagation();
      };

      if (key === 'ArrowDown') {
        handled();
        reader.next();
        return;
      }
      if (key === 'ArrowUp') {
        handled();
        reader.prev();
        return;
      }
      if (key === 'ArrowRight') {
        handled();
        reader.stepSentence(1);
        return;
      }
      if (key === 'ArrowLeft') {
        handled();
        reader.stepSentence(-1);
        return;
      }

      if (!shortcutsEnabled) return;

      const lower = key.length === 1 ? key.toLowerCase() : key;
      const direction = shift ? -1 : 1;

      switch (lower) {
        case 'j':
          handled();
          reader.next();
          return;
        case 'k':
          handled();
          reader.prev();
          return;
        case 'h':
          handled();
          reader.jumpToType('heading', direction);
          return;
        case 'g':
          handled();
          reader.jumpToType('figure', direction);
          return;
        case 't':
          handled();
          reader.jumpToType('table', direction);
          return;
        case ' ':
          if (isActivatable(event.target)) return;
          handled();
          reader.toggle();
          return;
        case 'r':
          handled();
          reader.repeat();
          return;
        case 's':
          handled();
          reader.stop();
          return;
        case '[':
          handled();
          reader.changeSpeed(-SPEED_STEP);
          return;
        case ']':
          handled();
          reader.changeSpeed(SPEED_STEP);
          return;
        case 'c':
          handled();
          cycleContrast();
          return;
        case '+':
        case '=':
          handled();
          changeZoom(ZOOM_STEP);
          return;
        case '-':
        case '_':
          handled();
          changeZoom(-ZOOM_STEP);
          return;
        case '0':
          handled();
          resetZoom();
          return;
        case 'z':
          handled();
          toggleFollow();
          return;
        case 'l':
          handled();
          cycleZoomMode();
          return;
        case 'e':
          handled();
          toggleEarcons();
          return;
        case 'd':
          handled();
          reader.describeFigure();
          return;
        case 'm':
        case 'q':
        case 'u':
          handled();
          announce('Chức năng giọng nói và hỏi đáp AI sẽ được tích hợp ở bước sau');
          return;
        case '?':
          handled();
          openHelp();
          return;
        default:
          return;
      }
    },
    [
      reader,
      shortcutsEnabled,
      cycleContrast,
      changeZoom,
      resetZoom,
      toggleFollow,
      cycleZoomMode,
      toggleEarcons,
      openHelp,
      announce,
    ],
  );
}
