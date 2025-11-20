import React from "react";
import { Bar } from "react-chartjs-2";
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
                backgroundColor: "rgba(25, 118, 210, 0.4)",   // jasny niebieski
                borderColor: "rgba(25, 118, 210, 1)",          // główny niebieski
                borderWidth: 2,
            },
        ],
    };

    const options = {
        scales: {
            y: {
                beginAtZero: true,
            },
        },
    };

    return <Bar data={data} options={options} />;
};

export default FeatureChart;
