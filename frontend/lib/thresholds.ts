// Ngưỡng độ tin cậy dùng chung cho giao diện. PHẢI khớp CONFIDENT_THRESHOLD / LOW_THRESHOLD của backend
// (backend/app/config.py); backend/tests/test_thresholds_parity.py kiểm tra hai bên không lệch nhau.
export type UncertaintyLevel = 'confident' | 'uncertain' | 'low';

export const CONFIDENT_THRESHOLD = 0.85;
export const LOW_THRESHOLD = 0.6;

export function levelOf(
  confidence: number,
  confident: number = CONFIDENT_THRESHOLD,
  low: number = LOW_THRESHOLD,
): UncertaintyLevel {
  if (confidence >= confident) return 'confident';
  if (confidence >= low) return 'uncertain';
  return 'low';
}
