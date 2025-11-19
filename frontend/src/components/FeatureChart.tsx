import { Bar } from "react-chartjs-2"
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    BarElement,
    Tooltip,
    Legend
} from "chart.js"
import type {FeatureSentiment} from "../types"

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip, Legend)

interface Props {
    features: FeatureSentiment[]
}

export default function FeatureChart({ features }: Props) {
    const labels = features.map(f => f.feature)
    const scores = features.map(f => f.score)

    const chartData = {
        labels,
        datasets: [
            {
                label: "Wynik sentymentu",
                data: scores,
                backgroundColor: "rgba(75, 192, 192, 0.5)",
            }
        ]
    }

    return (
        <div style={{ width: 600, margin: "40px auto" }}>
            <Bar data={chartData} />
        </div>
    )
}
