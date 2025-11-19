export type Platform = 'youtube' | 'tiktok' | 'instagram'
export type Sentiment = 'positive' | 'neutral' | 'negative'

export interface FeatureSentiment {
    id: string;
    feature: string;
    score: number;
    sentiment: string;
    summary?: string;
    examples?: string[];
}

export interface AnalysisResult {
    id: string;
    sentiment?: Sentiment | string;
    summary?: string;
    features: FeatureSentiment[];
    // dodatkowe pola z backendu
    title?: string;
    url?: string;
}

export interface JobStatus {
    id: string;
    state: 'pending' | 'running' | 'finished' | 'failed';
    analysisId?: string;
    error?: string;
    progress?: number;
}

export interface Video {
    id: string,
    title: string,
    url: string,
    features: FeatureSentiment[]
}