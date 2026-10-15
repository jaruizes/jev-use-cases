export type ProviderId = 'jev' | 'haiku' | 'sonnet';
export type UseCaseKind = 'choice' | 'score' | 'noul' | 'generation';
export interface Scenario { id: string; title: string; input: string; expected: string | number | null; }
export interface QualityEntry { provider: ProviderId; correct: number; total: number; accuracyPercent: number | null; }
export interface QualitySummary { useCaseId: string; referenceType: string; results: QualityEntry[]; }
export interface UseCase { scenarios: Scenario[]; id: string; name: string; kind: UseCaseKind; description: string; example: string; prompt: string; criteria: string[] | Record<string,string> | null; providers: ProviderId[]; }
export interface ProviderResult { provider: ProviderId; status: 'success' | 'error' | 'unsupported'; model?: string; value?: string | number; raw?: unknown; usage?: {input_tokens?: number; output_tokens?: number} | null; latencyMs: number; error?: string; detail?: string; correct?: boolean | null; estimatedCostUsd?: number | null; costPer1000Usd?: number | null; pricingStatus?: string; pricingVersion?: string; pricingSource?: string; ratesUsdPerMillion?: {input: number; output: number}; }
export interface Execution { id: string; useCaseId: string; scenarioId?: string | null; expected?: string | number | null; input: string; timestamp: string; results: ProviderResult[]; }
