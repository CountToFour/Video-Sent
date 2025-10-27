import React from 'react'
import { Chart as ChartJS, BarElement, CategoryScale, LinearScale, Tooltip, Legend } from 'chart.js'
import { Bar } from 'react-chartjs-2'

ChartJS.register(BarElement, CategoryScale, LinearScale, Tooltip, Legend)

export default function AnalysisChart({ features }: any) {
  const data = {
    labels: features.map((f: any) => f.feature),
    datasets: [
      {
        label: 'Score (abs)',
        data: features.map((f: any) => Math.abs(f.score)),
      }
    ]
  }

  return <Bar data={data} />
}