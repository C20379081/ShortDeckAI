// Displays the login modal which pops up over the homepage whena user isnt signed in.
document.addEventListener('DOMContentLoaded', function() {
    var modal = document.getElementById('loginModal');
    if (modal) {
        modal.style.display = "block";
    }
});

// function to show  the pie charts and the line chart 
document.addEventListener('DOMContentLoaded', function() {

    // This is a helper function to safely parse JSON
    function safeParse(jsonString) {
        try {
            return JSON.parse(jsonString);
        } catch (e) {
            console.error("Parsing error:", e);
            return null;
        }
    }

    // retrieving the data for the charts and graph
    var winningsData = safeParse(document.getElementById('winningsData').textContent);
    var vpipData = safeParse(document.getElementById('vpipData').textContent);
    var pfrData = safeParse(document.getElementById('pfrData').textContent);
    var winRatioData = safeParse(document.getElementById('winRatioData').textContent);
    var chart;

    // if all teh data is present then the charts can be displayed
    if (winningsData && vpipData && pfrData && winRatioData) {
        
        // fucntion of rthe time trend line graph 
        function updateTimeTrendView(viewType) {
            var ctxTimeTrend = document.getElementById('timeTrendChart').getContext('2d');

            // befreo creating a new chart, the old must be deleted.
            if (chart) {
                chart.destroy();
            }
            
            // Using chart.js to create it, it can toggle between the viewtype which is daily and weekly data, defualtis set to daily
            chart = new Chart(ctxTimeTrend, {
                type: 'line',
                data: viewType === 'daily' ? winningsData.daily : winningsData.weekly,
                options: {
                    scales: {
                        x: {
                            type: 'time',
                            time: {
                                parser: 'yyyy-MM-dd',
                                tooltipFormat: 'DD MMM, yyyy',
                                unit: viewType === 'daily' ? 'day' : 'week'
                            },
                            title: {
                                display: true,
                                text: 'Date'
                            }
                        },
                        y: {
                            beginAtZero: false,
                            title: {
                                display: true,
                                text: 'Winnings'
                            },
                            ticks: {
                                stepSize: 1000,
                                callback: function(value) {
                                    return value.toLocaleString();
                                }
                            }
                        }
                    },
                    responsive: true,
                    plugins: {
                        legend: {
                            display: true,
                            position: 'top'
                        },
                        title: {
                            display: true,
                            text: 'Winnings Over Time (' + (viewType === 'daily' ? 'Daily' : 'Weekly') + ')'
                        }
                    }
                }
            });
           
        }
        // daily is called by defualt
        updateTimeTrendView('daily')

        // the button for the daily view, if clicked it will hsow the daily data
        document.getElementById('dailyView').addEventListener('click', function() {
            updateTimeTrendView('daily');
        });

        // the button for the weekly view, if clicked it will hsow the weekly data
        document.getElementById('weeklyView').addEventListener('click', function() {
            updateTimeTrendView('weekly');
        });

        
        // Win/Loss Pie Chart 
        createPieChart('winRatioChart', ['Wins', 'Losses'], [winRatioData, 100 - winRatioData], ['green','red'], 'Win vs Loss Percentage');

        // VPIP Pie Chart - showing only VPIP 
        createPieChart('vpipPieChart', ['VPIP'], [vpipData, 100 - vpipData], ['rgba(255, 99, 132, 0.9)', 'rgba(0, 0, 0, 0)'], 'VPIP Percentage');

        // PFR Pie Chart - showing only PFR
        createPieChart('pfrPieChart', ['PFR'], [pfrData, 100 - pfrData], ['rgba(54, 162, 235, 0.9)', 'rgba(0, 0, 0, 0)'], 'PFR Percentage');


        
    } 
    else {
        console.error("One or more of the chart data elements is null.");
    }

    // fucntion for the pie charts, created using the data for each chart once create pie chart is called
    function createPieChart(chartElementId, labels, data, backgroundColors, chartLabel, includeOthers = true) {
        var ctx = document.getElementById(chartElementId).getContext('2d');

        var dataSet = {
            label: chartLabel,
            data: includeOthers ? data : [data[0]],
            backgroundColor: includeOthers ? backgroundColors : [backgroundColors[0]],
            borderColor: includeOthers ? backgroundColors.map(color => color.replace('0.2', '1')) : [backgroundColors[0].replace('0.2', '1')],
            borderWidth: 1
        };

        new Chart(ctx, {
            type: 'pie',
            data: {
                // Use only the first label if includeOthers is false
                labels: includeOthers ? labels : [labels[0]],
                datasets: [dataSet]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        display: includeOthers, 
                        position: 'top',
                    },
                    title: {
                        display: false,
                    },
                    tooltip: {
                        enabled: false
                    }
                },
                animation: {
                    animateScale: true,
                    animateRotate: true
                }
            }
        });
    }
    
});

