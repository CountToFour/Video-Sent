import React from 'react'
import Card from '@mui/material/Card'
import CardContent from '@mui/material/CardContent'
import Typography from '@mui/material/Typography'

export default function FeatureCard({ feature, sentiment, score, examples }: any) {
  return (
    <Card>
      <CardContent>
        <Typography variant="h6">{feature}</Typography>
        <Typography variant="body2">{sentiment} ({score.toFixed(2)})</Typography>
        <Typography variant="subtitle2" sx={{ mt: 1 }}>Examples:</Typography>
        <ul>
          {examples.slice(0,4).map((e: string, i: number) => <li key={i}><Typography variant="body2">{e}</Typography></li>)}
        </ul>
      </CardContent>
    </Card>
  )
}