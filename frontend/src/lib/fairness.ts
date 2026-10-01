/**
 * Client-side FWOS computation — mirrors the Python fairness_agent logic.
 */
const URGENCY_WEIGHTS: Record<string, number> = {
  critical: 1.0,
  high: 0.75,
  medium: 0.5,
  low: 0.25,
};

const MAX_POSITION = 6;

export function compute_fwos_client(
  canalPosition: number,
  eta: number,
  historicalDeficit: number,
  missedTurns: number,
  urgency: string,
): number {
  const downstream = ((canalPosition - 1) / (MAX_POSITION - 1)) * 30;
  const efficiency = (1 - eta) * 20;
  const deficit = Math.min(historicalDeficit / 5.0, 1.0) * 25;
  const missed = Math.min(missedTurns / 5.0, 1.0) * 15;
  const urgencyScore = (URGENCY_WEIGHTS[urgency] ?? 0.5) * 10;
  return Math.round(downstream + efficiency + deficit + missed + urgencyScore);
}

export function computeCompensation(
  hoursYielded: number,
  yieldingEta: number,
  receivingEta: number,
): number {
  if (receivingEta <= 0) receivingEta = 0.01;
  return Math.round(hoursYielded * (yieldingEta / receivingEta) * 100) / 100;
}
