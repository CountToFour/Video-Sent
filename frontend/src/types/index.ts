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
  url: string
  platform?: Platform
  overall: { sentiment: Sentiment; score: number }
  features: FeatureSentiment[]
  createdAt: string
}