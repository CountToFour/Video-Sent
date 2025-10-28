export type Platform = 'youtube' | 'tiktok' | 'instagram'
export type Sentiment = 'positive' | 'neutral' | 'negative'

export interface FeatureSentiment {
  feature: string
  sentiment: Sentiment
  score: number
  examples: string[]
}

export interface AnalysisResult {
  id: string
  feature: string
  sentiment: Sentiment
  score: number
  summary: string
}