'use client';

import {
  CONTRAST_LABEL,
  CONTRAST_ORDER,
  ZOOM_MAX,
  ZOOM_MIN,
  ZOOM_MODE_LABEL,
  ZOOM_STEP,
  useAccessibility,
} from '@/lib/accessibility';

export function Toolbar() {
  const {
    contrast,
    setContrast,
    zoom,
    changeZoom,
    resetZoom,
    zoomMode,
    cycleZoomMode,
    follow,
    toggleFollow,
    shortcutsEnabled,
    toggleShortcuts,
    earcons,
    toggleEarcons,
    earconVolume,
    setEarconVolume,
    openHelp,
  } = useAccessibility();

  return (
    <header className="border-b-[3px] border-fg bg-bg">
      <div className="mx-auto flex max-w-[1600px] flex-wrap items-center gap-x-6 gap-y-3 px-4 py-3">
        <h1 className="text-2xl font-extrabold text-ac">EyeAssist</h1>

        <div role="group" aria-label="Chế độ màu và tương phản" className="flex flex-wrap items-center gap-2">
          <span className="font-bold" aria-hidden="true">
            Tương phản (C):
          </span>
          {CONTRAST_ORDER.map((mode) => (
            <button
              key={mode}
              type="button"
              className="btn"
              aria-pressed={contrast === mode}
              onClick={() => setContrast(mode)}
            >
              {CONTRAST_LABEL[mode]}
            </button>
          ))}
        </div>

        <div role="group" aria-label="Phóng đại" className="flex flex-wrap items-center gap-2">
          <span className="font-bold" aria-hidden="true">
            Zoom:
          </span>
          <button
            type="button"
            className="btn"
            aria-label="Thu nhỏ"
            disabled={zoom <= ZOOM_MIN}
            onClick={() => changeZoom(-ZOOM_STEP)}
          >
            −
          </button>
          <output className="min-w-[4.5rem] text-center text-lg font-extrabold" aria-label={`Mức phóng đại ${zoom} phần trăm`}>
            {zoom}%
          </output>
          <button
            type="button"
            className="btn"
            aria-label="Phóng to"
            disabled={zoom >= ZOOM_MAX}
            onClick={() => changeZoom(ZOOM_STEP)}
          >
            +
          </button>
          <button type="button" className="btn" onClick={resetZoom}>
            100% (0)
          </button>
          <button type="button" className="btn" onClick={cycleZoomMode}>
            Kiểu: {ZOOM_MODE_LABEL[zoomMode]} (L)
          </button>
          <button type="button" className="btn" aria-pressed={follow} onClick={toggleFollow}>
            Bám vùng đọc (Z): {follow ? 'Bật' : 'Tắt'}
          </button>
        </div>

        <div role="group" aria-label="Âm báo" className="flex flex-wrap items-center gap-2">
          <button type="button" className="btn" aria-pressed={earcons} onClick={toggleEarcons}>
            Âm báo (E): {earcons ? 'Bật' : 'Tắt'}
          </button>
          <label className="flex items-center gap-2 font-bold">
            <span>Âm lượng</span>
            <input
              type="range"
              min={0}
              max={100}
              step={5}
              value={Math.round(earconVolume * 100)}
              onChange={(event) => setEarconVolume(Number(event.target.value) / 100)}
              className="h-11 w-28 accent-ac"
            />
          </label>
        </div>

        <div role="group" aria-label="Phím tắt" className="flex flex-wrap items-center gap-2">
          <button type="button" className="btn" aria-pressed={shortcutsEnabled} onClick={toggleShortcuts}>
            Phím đơn: {shortcutsEnabled ? 'Bật' : 'Tắt'}
          </button>
          <button type="button" className="btn btn-primary" onClick={openHelp}>
            Phím tắt (F1)
          </button>
        </div>
      </div>
    </header>
  );
}
