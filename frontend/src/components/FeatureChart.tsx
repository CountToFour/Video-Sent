import React from "react";
import { Bar } from "react-chartjs-2";

import {
    Chart as ChartJS,
    BarElement,
    CategoryScale,
    LinearScale,
    Tooltip,
    Legend
} from "chart.js";

ChartJS.register(
    BarElement,
    CategoryScale,
    LinearScale,
    Tooltip,
    Legend
);

// eslint-disable-next-line @typescript-eslint/ban-ts-comment
// @ts-expect-error
import type { Feature } from "../types";

interface Props {
    features?: Feature[];
}

const FeatureChart: React.FC<Props> = ({ features = [] }) => {
    const labels = features.map(f => f.feature);
    const scores = features.map(f => f.score);

    const data = {
        labels,
        datasets: [
            {
                label: "Wynik",
                data: scores,
                backgroundColor: "rgba(25, 118, 210, 0.4)",
                borderColor: "rgba(25, 118, 210, 1)",
                borderWidth: 2,
            },
        ],
    };

    const options = {
        maintainAspectRatio: false,   // opcjonalnie
        scales: {
            y: {
                beginAtZero: true,
            },
        },
    };

    return (
        <div style={{ height: 500 }}>
            <Bar data={data} options={options} />
        </div>
    );
};

export default FeatureChart;
