document.addEventListener('DOMContentLoaded', function() {
    const chartCanvas = document.getElementById('employeeChart');
    
    if (chartCanvas) {
        const labels = JSON.parse(chartCanvas.getAttribute('data-labels') || '[]');
        const activeData = JSON.parse(chartCanvas.getAttribute('data-active') || '[]');
        const completedData = JSON.parse(chartCanvas.getAttribute('data-completed') || '[]');
        const overdueData = JSON.parse(chartCanvas.getAttribute('data-overdue') || '[]');

        new Chart(chartCanvas.getContext('2d'), {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Активных',
                        data: activeData,
                        backgroundColor: '#0d6efd',
                        borderColor: '#0d6efd',
                        borderWidth: 1,
                        borderRadius: 3,
                        borderSkipped: false
                    },
                    {
                        label: 'Выполнено',
                        data: completedData,
                        backgroundColor: '#198754',
                        borderColor: '#198754',
                        borderWidth: 1,
                        borderRadius: 3,
                        borderSkipped: false
                    },
                    {
                        label: 'Просрочено',
                        data: overdueData,
                        backgroundColor: '#dc3545',
                        borderColor: '#dc3545',
                        borderWidth: 1,
                        borderRadius: 3,
                        borderSkipped: false
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                scales: {
                    x: {
                        stacked: false,
                        grid: { display: false },
                        ticks: {
                            font: { size: 11 },
                            maxRotation: 0,
                            minRotation: 0
                        }
                    },
                    y: {
                        beginAtZero: true,
                        ticks: { stepSize: 1 },
                        grid: { color: 'rgba(0, 0, 0, 0.04)' }
                    }
                },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: '#212529',
                        titleFont: { size: 13, weight: 'bold' },
                        bodyFont: { size: 12 },
                        padding: 10,
                        cornerRadius: 4,
                        callbacks: {
                            label: function(context) {
                                return context.dataset.label + ': ' + context.parsed.y;
                            }
                        }
                    }
                },
                interaction: {
                    mode: 'index',
                    intersect: false
                }
            }
        });
    }
});