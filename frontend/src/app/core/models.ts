export type ProviderId = 'jev' | 'haiku' | 'sonnet';
export type UseCaseKind = 'choice' | 'score' | 'noul' | 'generation';
export interface UseCase { id: string; name: string; kind: UseCaseKind; description: string; example: string; prompt: string; criteria: string[] | Record<string,string> | null; providers: ProviderId[]; }
export interface ProviderResult { provider: ProviderId; status: 'success' | 'error' | 'unsupported'; model?: string; value?: string | number; raw?: unknown; usage?: {input_tokens?: number; output_tokens?: number} | null; latencyMs: number; error?: string; detail?: string; }
export interface Execution { id: string; useCaseId: string; input: string; timestamp: string; results: ProviderResult[]; }
