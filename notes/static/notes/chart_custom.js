document.addEventListener("DOMContentLoaded", function () {
    let chart = generate_rt_graph();
    let showingReactionTime = true;
    // Button toggling logic
    const toggleButton = document.getElementById("toggle-data-button");
    toggleButton.addEventListener("click", () => {
        showingReactionTime = !showingReactionTime;
        toggleButton.textContent = showingReactionTime
            ? "Show % Correct"
            : "Show Reaction Time";
        chart.destroy();
        if (showingReactionTime) chart = generate_rt_graph();
        else chart = generate_correct_graph();
    });
});

function generate_rt_graph() {
    const progress_data_unsorted = JSON.parse(
        document.getElementById("progress-data").textContent
    );
    const rt_per_sk = JSON.parse(
        document.getElementById("rt_per_sk-data").textContent
    );

    function getNoteOrder(note) {
        // Define the order of natural notes (C < D < E < F < G < A < B)
        const noteOrder = ["C", "D", "E", "F", "G", "A", "B"];
        return noteOrder.indexOf(note);
    }

    function sortProgressData(a, b) {
        // Sort by octave first
        if (a.octave !== b.octave) {
            return a.octave - b.octave; // Lower octave comes first
        }

        // Sort by natural note order (C < D < E < F < G < A < B)
        const orderA = getNoteOrder(a.note);
        const orderB = getNoteOrder(b.note);
        if (orderA !== orderB) {
            return orderA - orderB;
        }

        // Sort by alter (accidentals): ♭♭ < ♭ < natural < ♯ < ♯♯
        return a.alter - b.alter; // `alter` ranges from -2 to 2
    }

    const progress_data = progress_data_unsorted.sort(sortProgressData);

    function median(numbers) {
        numbers = numbers.map(Number);
        const sorted = Array.from(numbers).sort((a, b) => a - b);
        const middle = Math.floor(sorted.length / 2);

        if (sorted.length % 2 === 0) {
            return (sorted[middle - 1] + sorted[middle]) / 2;
        }
        return sorted[middle];
    }

// Prepare scatter plot data from progress_data
    let data = [];
    let staveLines = [];

    for (let i = 0; i < progress_data.length; i++) {
        const pd = progress_data[i];
        const rt_log = pd.reaction_time_log;

        if (!rt_log || rt_log.length === 0) continue; // Skip if no reaction time data found

        let rt = median(rt_log);

        // Include `alter` value in `note_id` to create unique identifiers
        let note_id;
        switch (pd.alter) {
            case "-2":
                note_id = pd.note + "♭♭/" + pd.octave; // Double flat
                break;
            case "-1":
                note_id = pd.note + "♭/" + pd.octave; // Flat
                break;
            case "0":
            case undefined:
                note_id = pd.note + "/" + pd.octave; // Natural
                break;
            case "1":
                note_id = pd.note + "♯/" + pd.octave; // Sharp
                break;
            case "2":
                note_id = pd.note + "♯♯/" + pd.octave; // Double sharp
                break;
            default:
                throw new Error('Unexpected value encountered for the note alteration: ' + pd);
        }

        data.push({note: note_id, time: rt});
        staveLines.push(note_id);
    }

    function removeOutliers(data, stavelines) {

        const reactionTimes = data.map(entry => entry.time);

        // Step 2: Calculate mean and standard deviation of reaction times
        const mean = reactionTimes.reduce((sum, rt) => sum + rt, 0) / reactionTimes.length;
        const variance = reactionTimes.reduce((sum, rt) => sum + Math.pow(rt - mean, 2), 0) / reactionTimes.length;
        const standardDeviation = Math.sqrt(variance);

        const threshold = mean + 3 * standardDeviation;

        const filteredData = data.filter(entry => entry.time <= threshold);
        const filteredStavelines = stavelines.filter((_, index) => data[index]?.time <= threshold);

        return {
            updatedData: filteredData,
            updatedStavelines: filteredStavelines,
        };
    }

    const outliers_removed = removeOutliers(data, staveLines);
    data = outliers_removed.updatedData;
    staveLines = outliers_removed.updatedStavelines;


    // Calculate note position for the x-axis
    const notePositions = staveLines.reduce((acc, note, index) => {
        acc[note] = index * 20 + 50; // X positions for each note, evenly spaced
        return acc;
    }, {});

    // Extract reaction times from progress and rt_per_sk
    const reactionTimesProgress = data.map((d) => d.time);
    const reactionTimesSkills = Object.values(rt_per_sk)
        .flat()
        .map((d) => d.rt);

    const allReactionTimes = [...reactionTimesProgress, ...reactionTimesSkills];
    const maxTime = Math.max(...allReactionTimes);

    const createBand = (skillLevel, color, stack, fill_info) => {
        const skillData = rt_per_sk[skillLevel];

        if (!skillData || skillData.length === 0) return null;

        // Calculate the minimum and maximum x-axis positions
        const minX = Math.min(...Object.values(notePositions)) - 10; // Add padding if needed
        const maxX = Math.max(...Object.values(notePositions)) + 10; // Add padding if needed

        // Prepare band data
        const bandData = staveLines.map((note) => {
            const matchingNote = skillData.find((d) => `${d.note}/${d.octave}` === note);
            return {
                x: notePositions[note],
                y: matchingNote ? matchingNote.rt : null,
                stack: stack, // Ensure stacking for the band
            };
        });

        // Filter only valid points (y !== null)
        const validPoints = bandData.filter((point) => point.y !== null);

        // Helper function for linear interpolation
        const interpolate = (x, x1, y1, x2, y2) => {
            return y1 + ((y2 - y1) / (x2 - x1)) * (x - x1);
        };

        // Interpolate the y value for minX
        if (validPoints.length > 1) {
            const [point1, point2] = validPoints.slice(0, 2); // Nearest two points for the start
            const minY = interpolate(minX, point1.x, point1.y, point2.x, point2.y);

            // Add the interpolated start point
            validPoints.unshift({x: minX, y: minY});
        }

        // Interpolate the y value for maxX
        if (validPoints.length > 1) {
            const [point1, point2] = validPoints.slice(-2); // Nearest two points for the end
            const maxY = interpolate(maxX, point1.x, point1.y, point2.x, point2.y);

            // Add the interpolated end point
            validPoints.push({x: maxX, y: maxY});
        }

        return {
            label: skillLevel.charAt(0).toUpperCase() + skillLevel.slice(1),
            data: validPoints,
            borderColor: color,
            backgroundColor: color,
            borderWidth: 1,
            fill: fill_info, // Fill the band
            stack: stack, // Stack the band
            pointRadius: 0,
            type: "line",
            tension: 0.4,
            order: 100,
        };
    };
    // Create all bands for the skill levels
    const bands = [
        createBand("beginner", "rgba(102, 192, 168, 0.6)", "beginner-stack", 1),
        createBand("intermediate", "rgba(255, 217, 47, 0.6)", "intermediate-stack", 'start'),
        createBand("advanced", "rgba(213, 94, 0, 0.6)", "advanced-stack", 'start', 'start'),
    ].filter((b) => b !== null);

    const color = "rgba(255, 99, 132, 1)";
    // Prepare the chart data
    const chartData = {
        labels: data.map((d) => `${d.note}`),
        datasets: [
            ...bands, // Zones (bands) appear first
            {
                label: "Your Data",
                borderColor: "rgba(255, 99, 132, 1)", // Point color
                backgroundColor: "rgba(255, 99, 132, 1)", // Point fill color
                data: data.map((d) => ({
                    x: notePositions[d.note],
                    y: d.time,
                })),
                pointRadius: 10, // Size of points
                pointHoverRadius: 12, // Size on hover
                type: "scatter", // Scatter plot for points
                order: 1, // Ensures it stays on top (optional, but clarifies intention)
            },
        ],
    };

    // Add plugin to render labels below circles
    const addPointLabelsPlugin = {
        id: "addPointLabels",
        afterDatasetDraw(chart, args, options) {
            const {ctx} = chart;
            const datasetIndex = chart.data.datasets.length - 1; // Scatter dataset
            const meta = chart.getDatasetMeta(datasetIndex);

            meta.data.forEach((point, index) => {
                const {x, y} = point.tooltipPosition();
                const label = chart.data.labels[index];
                ctx.save();
                ctx.font = "12px Arial";
                ctx.fillStyle = "#000"; // Label color
                ctx.textAlign = "center";
                ctx.textBaseline = "top";
                ctx.fillText(label, x, y + 12); // Position label below the circle
                ctx.restore();
            });
        },
    };

    Chart.register(addPointLabelsPlugin);

    const config = {
        type: "scatter",
        data: chartData,
        options: {
            responsive: true,
            plugins: {
                addPointLabelsPlugin: addPointLabelsPlugin,


                legend: {
                    display: true,
                },
                tooltip: {
                    callbacks: {
                        label: function (tooltipItem) {
                            return `Note: ${
                                staveLines[tooltipItem.dataIndex]
                            }, Time: ${
                                data[tooltipItem.dataIndex].time
                            } ms`;
                        },
                    },
                },
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: "Notes",
                    },
                    ticks: {
                        callback: function (value) {
                            const note = Object.keys(notePositions).find(
                                (note) => notePositions[note] === value
                            );
                            return note || "";
                        },
                    },
                },
                y: {
                    title: {
                        display: true,
                        text: "Reaction Time (ms)",
                    },
                    min: 0,
                },
            },
        },
    };

    // Render the chart
    const ctx = document.getElementById("staveChart").getContext("2d");
    return new Chart(ctx, config);
}

function generate_correct_graph() {
    const progress_data_unsorted = JSON.parse(
        document.getElementById("progress-data").textContent
    );

    // Function to define the order of natural notes
    function getNoteOrder(note) {
        const noteOrder = ["C", "D", "E", "F", "G", "A", "B"];
        return noteOrder.indexOf(note);
    }

    // Function to sort progress data
    function sortProgressData(a, b) {
        // Sort by octave first
        if (a.octave !== b.octave) {
            return a.octave - b.octave; // Lower octave comes first
        }

        // Sort by natural note order (C < D < E < F < G < A < B)
        const orderA = getNoteOrder(a.note);
        const orderB = getNoteOrder(b.note);
        if (orderA !== orderB) {
            return orderA - orderB;
        }

        // Sort by alterations (accidentals): ♭♭ < ♭ < natural < ♯ < ♯♯
        return a.alter - b.alter; // `alter` ranges from -2 to 2
    }

    // Sort the progress data
    const progress_data = progress_data_unsorted.sort(sortProgressData);

    // Prepare scatter plot data for percentage correct
    const data = [];
    const staveLines = [];

    for (const pd of progress_data) {
        const correctLog = pd.correct;

        if (!correctLog || correctLog.length === 0) continue; // Skip if no correctness data found

        // Calculate the percentage correctness
        const totalAttempts = correctLog.length;
        const correctAttempts = correctLog.filter((entry) => entry === true).length;
        const percentageCorrect = (correctAttempts / totalAttempts) * 100;

        // Include `alter` value in `note_id` to create unique identifiers
        let note_id;
        switch (pd.alter) {
            case "-2":
                note_id = pd.note + "♭♭/" + pd.octave; // Double flat
                break;
            case "-1":
                note_id = pd.note + "♭/" + pd.octave; // Flat
                break;
            case "0":
            case undefined:
                note_id = pd.note + "/" + pd.octave; // Natural
                break;
            case "1":
                note_id = pd.note + "♯/" + pd.octave; // Sharp
                break;
            case "2":
                note_id = pd.note + "♯♯/" + pd.octave; // Double sharp
                break;
            default:
                throw new Error("Unexpected value encountered for note alteration: " + pd);
        }

        data.push({note: note_id, correctPercentage: percentageCorrect});
        staveLines.push(note_id);
    }

    // Calculate note positions for the x-axis
    const notePositions = staveLines.reduce((acc, note, index) => {
        acc[note] = index * 20 + 50; // X positions for each note, evenly spaced
        return acc;
    }, {});

    // Prepare the chart data
    const chartData = {
        labels: data.map((d) => d.note),
        datasets: [
            {
                label: "Correctness (%)", // Label for the dataset
                borderColor: "rgb(0,0,0)", // Point color
                backgroundColor: "rgb(0,0,0)", // Point fill color
                data: data.map((d) => ({
                    x: notePositions[d.note],
                    y: d.correctPercentage,
                })),
                pointRadius: 10, // Size of points
                pointHoverRadius: 12, // Size on hover
                type: "scatter", // Scatter plot for points
                order: 1, // Ensure it stays on top (optional)
            },
        ],
    };

    // Add plugin to render labels below circles
    const addPointLabelsPlugin = {
        id: "addPointLabels",
        afterDatasetDraw(chart, args, options) {
            const {ctx} = chart;
            const datasetIndex = chart.data.datasets.length - 1; // Scatter dataset
            const meta = chart.getDatasetMeta(datasetIndex);

            meta.data.forEach((point, index) => {
                const {x, y} = point.tooltipPosition();
                const label = chart.data.labels[index];
                ctx.save();
                ctx.font = "12px Arial";
                ctx.fillStyle = "#000"; // Label color
                ctx.textAlign = "center";
                ctx.textBaseline = "top";
                ctx.fillText(label, x, y + 12); // Position label below the circle
                ctx.restore();
            });
        },
    };

    Chart.register(addPointLabelsPlugin);

    // Chart configuration
    const config = {
        type: "scatter",
        data: chartData,
        options: {
            responsive: true,
            plugins: {
                addPointLabelsPlugin: addPointLabelsPlugin,
                legend: {
                    display: true,
                },
                tooltip: {
                    callbacks: {
                        label: function (tooltipItem) {
                            return `Note: ${
                                staveLines[tooltipItem.dataIndex]
                            }, Correct: ${
                                data[tooltipItem.dataIndex].correctPercentage.toFixed(2)
                            }%`;
                        },
                    },
                },
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: "Notes",
                    },
                    ticks: {
                        callback: function (value) {
                            const note = Object.keys(notePositions).find(
                                (note) => notePositions[note] === value
                            );
                            return note || "";
                        },
                    },
                },
                y: {
                    title: {
                        display: true,
                        text: "Correctness (%)",
                    },
                    min: 0,
                    suggestedMax: 105, // Add padding but don't show labels beyond 100%
                    ticks: {
                        callback: function (value) {
                            return value > 100 ? "" : value + "%"; // Show values only up to 100%
                        },
                    },
                },
            },
        },
    };

    // Render the chart
    const ctx = document.getElementById("staveChart").getContext("2d");
    return new Chart(ctx, config);
}
