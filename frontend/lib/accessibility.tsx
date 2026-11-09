'use client';

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from 'react';

export type Contrast = 'standard' | 'dark-yellow' | 'light-black';
export type ZoomMode = 'lens' | 'docked' | 'reflow';

export const CONTRAST_ORDER: Contrast[] = ['standard', 'dark-yellow', 'light-black'];

export const CONTRAST_LABEL: Record<Contrast, string> = {
  standard: 'Chuẩn',
  'dark-yellow': 'Đen - Vàng',
  'light-black': 'Trắng - Đen',
};

export const ZOOM_MODE_ORDER: ZoomMode[] = ['docked', 'lens', 'reflow'];

export const ZOOM_MODE_LABEL: Record<ZoomMode, string> = {
  docked: 'Cố định',
  lens: 'Ống kính',
  reflow: 'Reflow',
};

export const ZOOM_MIN = 100;
export const ZOOM_MAX = 400;
export const ZOOM_STEP = 25;

export const STORAGE_KEY = 'eyeassist:prefs';

type Prefs = {
  contrast: Contrast;
  zoom: number;
  zoomMode: ZoomMode;
  follow: boolean;
  shortcutsEnabled: boolean;
};

const DEFAULTS: Prefs = {
  contrast: 'standard',
  zoom: 200,
  zoomMode: 'docked',
  follow: true,
  shortcutsEnabled: true,
};

type AccessibilityValue = Prefs & {
  announcement: string;
  helpOpen: boolean;
  announce: (message: string) => void;
  cycleContrast: () => void;
  setContrast: (value: Contrast) => void;
  changeZoom: (delta: number) => void;
  resetZoom: () => void;
  cycleZoomMode: () => void;
  toggleFollow: () => void;
  toggleShortcuts: () => void;
  openHelp: () => void;
  closeHelp: () => void;
};

const AccessibilityContext = createContext<AccessibilityValue | null>(null);

function loadPrefs(): Prefs | null {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as Partial<Prefs>;
    const next: Prefs = { ...DEFAULTS, ...parsed };
    if (!CONTRAST_ORDER.includes(next.contrast)) next.contrast = DEFAULTS.contrast;
    if (!ZOOM_MODE_ORDER.includes(next.zoomMode)) next.zoomMode = DEFAULTS.zoomMode;
    next.zoom = Math.min(ZOOM_MAX, Math.max(ZOOM_MIN, Number(next.zoom) || DEFAULTS.zoom));
    return next;
  } catch {
    return null;
  }
}

function savePrefs(prefs: Prefs) {
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(prefs));
  } catch {
    return;
  }
}

export function AccessibilityProvider({ children }: { children: ReactNode }) {
  const [prefs, setPrefs] = useState<Prefs>(DEFAULTS);
  const [loaded, setLoaded] = useState(false);
  const [announcement, setAnnouncement] = useState('');
  const [helpOpen, setHelpOpen] = useState(false);
  const flip = useRef(false);

  useEffect(() => {
    const stored = loadPrefs();
    if (stored) {
      setPrefs(stored);
    } else if (window.matchMedia('(prefers-contrast: more)').matches) {
      setPrefs((p) => ({ ...p, contrast: 'light-black' }));
    }
    setLoaded(true);
  }, []);

  useEffect(() => {
    document.documentElement.dataset.theme = prefs.contrast;
  }, [prefs.contrast]);

  useEffect(() => {
    if (loaded) savePrefs(prefs);
  }, [prefs, loaded]);

  const announce = useCallback((message: string) => {
    flip.current = !flip.current;
    setAnnouncement(message + (flip.current ? '​' : ''));
  }, []);

  const setContrast = useCallback(
    (value: Contrast) => {
      setPrefs((p) => ({ ...p, contrast: value }));
      announce(`Chế độ màu: ${CONTRAST_LABEL[value]}`);
    },
    [announce],
  );

  const cycleContrast = useCallback(() => {
    const next = CONTRAST_ORDER[(CONTRAST_ORDER.indexOf(prefs.contrast) + 1) % CONTRAST_ORDER.length];
    setContrast(next);
  }, [prefs.contrast, setContrast]);

  const changeZoom = useCallback(
    (delta: number) => {
      const next = Math.min(ZOOM_MAX, Math.max(ZOOM_MIN, prefs.zoom + delta));
      if (next === prefs.zoom) {
        announce(delta > 0 ? 'Đã đạt mức phóng đại tối đa 400%' : 'Đã đạt mức nhỏ nhất 100%');
        return;
      }
      setPrefs((p) => ({ ...p, zoom: next }));
      announce(`Phóng đại ${next}%`);
    },
    [prefs.zoom, announce],
  );

  const resetZoom = useCallback(() => {
    setPrefs((p) => ({ ...p, zoom: 100 }));
    announce('Đã đặt lại phóng đại 100%');
  }, [announce]);

  const cycleZoomMode = useCallback(() => {
    const next = ZOOM_MODE_ORDER[(ZOOM_MODE_ORDER.indexOf(prefs.zoomMode) + 1) % ZOOM_MODE_ORDER.length];
    setPrefs((p) => ({ ...p, zoomMode: next }));
    announce(`Kiểu zoom: ${ZOOM_MODE_LABEL[next]}`);
  }, [prefs.zoomMode, announce]);

  const toggleFollow = useCallback(() => {
    const next = !prefs.follow;
    setPrefs((p) => ({ ...p, follow: next }));
    announce(next ? 'Zoom bám theo vùng đọc: bật' : 'Zoom bám theo vùng đọc: tắt');
  }, [prefs.follow, announce]);

  const toggleShortcuts = useCallback(() => {
    const next = !prefs.shortcutsEnabled;
    setPrefs((p) => ({ ...p, shortcutsEnabled: next }));
    announce(next ? 'Phím tắt một phím: bật' : 'Phím tắt một phím: tắt');
  }, [prefs.shortcutsEnabled, announce]);

  const openHelp = useCallback(() => setHelpOpen(true), []);
  const closeHelp = useCallback(() => setHelpOpen(false), []);

  const value = useMemo<AccessibilityValue>(
    () => ({
      ...prefs,
      announcement,
      helpOpen,
      announce,
      cycleContrast,
      setContrast,
      changeZoom,
      resetZoom,
      cycleZoomMode,
      toggleFollow,
      toggleShortcuts,
      openHelp,
      closeHelp,
    }),
    [
      prefs,
      announcement,
      helpOpen,
      announce,
      cycleContrast,
      setContrast,
      changeZoom,
      resetZoom,
      cycleZoomMode,
      toggleFollow,
      toggleShortcuts,
      openHelp,
      closeHelp,
    ],
  );

  return <AccessibilityContext.Provider value={value}>{children}</AccessibilityContext.Provider>;
}

export function useAccessibility(): AccessibilityValue {
  const ctx = useContext(AccessibilityContext);
  if (!ctx) throw new Error('useAccessibility must be used inside AccessibilityProvider');
  return ctx;
}
