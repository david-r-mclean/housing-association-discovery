/**
 * Social Media Intelligence Dashboard - Fixed Chart Implementation
 */

class SocialMediaIntelligence {
    constructor() {
        this.platforms = [];
        this.currentAnalysis = null;
        this.charts = {}; // Store chart instances
        this.init();
    }

    async init() {
        await this.loadDashboardStats();
        await this.loadSupportedPlatforms();
        await this.loadRecentReports();
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Analysis form submission
        const analysisForm = document.getElementById('analysisForm');
        if (analysisForm) {
            analysisForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.startAnalysis();
            });
        }

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.hideAllModals();
            }
        });
    }

    async loadDashboardStats() {
        try {
            const response = await fetch('/api/social-media/dashboard-stats');
            const data = await response.json();

            if (data.success) {
                const stats = data.stats;
                
                // Update stat cards
                this.updateStatCard('total-associations', stats.total_associations_analyzed);
                this.updateStatCard('total-profiles', stats.total_profiles_found);
                this.updateStatCard('total-posts', stats.total_posts_analyzed);
                this.updateStatCard('total-reports', stats.total_reports_generated);

                // Update charts with delay to ensure DOM is ready
                setTimeout(() => {
                    this.updatePlatformChart(stats.platform_distribution);
                    this.updateSentimentChart(stats.sentiment_overview);
                }, 100);
            }
        } catch (error) {
            console.error('Error loading dashboard stats:', error);
            this.showFallbackStats();
        }
    }

    updateStatCard(elementId, value) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = (value || 0).toLocaleString();
        }
    }

    showFallbackStats() {
        // Show fallback stats if API fails
        this.updateStatCard('total-associations', 0);
        this.updateStatCard('total-profiles', 0);
        this.updateStatCard('total-posts', 0);
        this.updateStatCard('total-reports', 0);

        // Show empty charts
        setTimeout(() => {
            this.updatePlatformChart([]);
            this.updateSentimentChart([]);
        }, 100);
    }

    updatePlatformChart(platformData) {
        const canvas = document.getElementById('platformChart');
        if (!canvas) {
            console.error('Platform chart canvas not found');
            return;
        }

        const ctx = canvas.getContext('2d');
        
        // Destroy existing chart if it exists
        if (this.charts.platformChart) {
            this.charts.platformChart.destroy();
        }

        // Prepare data
        const labels = platformData.length > 0 ? platformData.map(p => p.platform) : ['No Data'];
        const data = platformData.length > 0 ? platformData.map(p => p.count) : [1];
        const colors = [
            '#3B82F6', '#10B981', '#8B5CF6', '#F59E0B',
            '#EF4444', '#6B7280', '#EC4899'
        ];

        try {
            this.charts.platformChart = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: labels,
                    datasets: [{
                        data: data,
                        backgroundColor: colors.slice(0, labels.length),
                        borderWidth: 2,
                        borderColor: '#ffffff'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: {
                                padding: 20,
                                usePointStyle: true
                            }
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const label = context.label || '';
                                    const value = context.parsed || 0;
                                    return `${label}: ${value}`;
                                }
                            }
                        }
                    }
                }
            });
        } catch (error) {
            console.error('Error creating platform chart:', error);
            this.showChartError('platformChart', 'Platform Distribution');
        }
    }

    updateSentimentChart(sentimentData) {
        const canvas = document.getElementById('sentimentChart');
        if (!canvas) {
           console.error('Sentiment chart canvas not found');
            return;
        }

        const ctx = canvas.getContext('2d');
    
        // Destroy existing chart if it exists
       if (this.charts.sentimentChart) {
         this.charts.sentimentChart.destroy();
     }

        // Prepare data
        const labels = sentimentData.length > 0 ? sentimentData.map(s => this.capitalizeFirst(s.sentiment)) : ['No Data'];
        const data = sentimentData.length > 0 ? sentimentData.map(s => s.count) : [1];
        const colors = sentimentData.length > 0 ? sentimentData.map(s => {
            switch(s.sentiment.toLowerCase()) {
               case 'positive': return '#10B981';
             case 'negative': return '#EF4444';
             default: return '#6B7280';
         }
        }) : ['#6B7280'];

        try {
            this.charts.sentimentChart = new Chart(ctx, {
             type: 'bar',
             data: {
                 labels: labels,
                 datasets: [{
                        label: 'Posts',
                        data: data,
                        backgroundColor: colors,
                        borderColor: colors,
                        borderWidth: 1,
                        borderRadius: 4,
                        borderSkipped: false,
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                 plugins: {
                     legend: {
                         display: false
                     },
                     tooltip: {
                            callbacks: {
                                label: function(context) {
                                    return `${context.dataset.label}: ${context.parsed.y}`;
                                }
                         }
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                stepSize: 1
                            },
                            grid: {
                                color: '#f3f4f6'
                            }
                        },
                        x: {
                            grid: {
                                display: false
                            }
                        }
                    },
                    // Force specific dimensions
                    layout: {
                        padding: 10
                    }
                }
           });
        } catch (error) {
            console.error('Error creating sentiment chart:', error);
         this.showChartError('sentimentChart', 'Sentiment Overview');
       }
    }

    showChartError(canvasId, chartTitle) {
        const canvas = document.getElementById(canvasId);
        if (canvas) {
            const parent = canvas.parentElement;
            parent.innerHTML = `
                <div class="flex items-center justify-center h-48">
                    <div class="text-center text-gray-500">
                        <i class="fas fa-chart-bar text-4xl mb-2"></i>
                        <p class="text-sm">${chartTitle}</p>
                        <p class="text-xs">Chart loading error</p>
                    </div>
                </div>
            `;
        }
    }

    capitalizeFirst(str) {
        return str.charAt(0).toUpperCase() + str.slice(1);
    }

    async loadSupportedPlatforms() {
        try {
            const response = await fetch('/api/social-media/platforms');
            const data = await response.json();

            if (data.success) {
                this.platforms = data.platforms;
                this.renderPlatformsGrid();
                this.renderPlatformCheckboxes();
            }
        } catch (error) {
            console.error('Error loading platforms:', error);
            this.showFallbackPlatforms();
        }
    }

    showFallbackPlatforms() {
        // Show fallback platforms if API fails
        this.platforms = [
            { id: 'twitter', name: 'Twitter/X', description: 'Real-time updates', data_types: ['posts', 'mentions'] },
            { id: 'facebook', name: 'Facebook', description: 'Community pages', data_types: ['pages', 'posts'] },
            { id: 'linkedin', name: 'LinkedIn', description: 'Professional presence', data_types: ['company_pages'] }
        ];
        this.renderPlatformsGrid();
        this.renderPlatformCheckboxes();
    }

    renderPlatformsGrid() {
        const grid = document.getElementById('platforms-grid');
        if (!grid) return;
        
        grid.innerHTML = this.platforms.map(platform => `
            <div class="social-platform-card bg-gray-50 rounded-lg p-4 border border-gray-200">
                <div class="flex items-center mb-2">
                    <i class="fab fa-${platform.id} text-2xl mr-3 text-gray-600"></i>
                    <div>
                        <h4 class="font-semibold text-gray-900">${platform.name}</h4>
                        <p class="text-xs text-gray-500">
                            ${platform.api_required ? 'API Required' : 'Web Scraping'}
                        </p>
                    </div>
                </div>
                <p class="text-sm text-gray-600 mb-3">${platform.description}</p>
                <div class="flex flex-wrap gap-1">
                    ${platform.data_types.map(type => 
                        `<span class="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">${type}</span>`
                    ).join('')}
                </div>
            </div>
        `).join('');
    }

    renderPlatformCheckboxes() {
        const container = document.getElementById('platformCheckboxes');
        if (!container) return;
        
        container.innerHTML = this.platforms.map(platform => `
            <label class="flex items-center space-x-2 cursor-pointer">
                <input type="checkbox" value="${platform.id}" 
                       ${['twitter', 'facebook', 'linkedin'].includes(platform.id) ? 'checked' : ''}
                       class="rounded border-gray-300 text-blue-600 focus:ring-blue-500">
                <span class="text-sm text-gray-700">
                    <i class="fab fa-${platform.id} mr-1"></i>${platform.name}
                </span>
            </label>
        `).join('');
    }

    async loadRecentReports() {
        try {
            // Mock reports for now since the endpoint might not be fully implemented
            const reports = [
                {
                    id: 1,
                    association_name: 'Sample Housing Association',
                    created_at: new Date().toISOString(),
                    platforms_analyzed: ['twitter', 'facebook'],
                    digital_presence_score: 75.5,
                    overall_sentiment: 0.2,
                    report_type: 'comprehensive_analysis'
                }
            ];
            
            this.renderReportsList(reports);
        } catch (error) {
            console.error('Error loading reports:', error);
            this.renderReportsList([]);
        }
    }

    renderReportsList(reports) {
        const container = document.getElementById('reports-list');
        if (!container) return;

        if (reports.length === 0) {
            container.innerHTML = `
                <div class="text-center py-8">
                    <i class="fas fa-chart-line text-4xl text-gray-300 mb-4"></i>
                    <p class="text-gray-500">No analysis reports yet</p>
                    <button onclick="showAnalysisModal()" class="mt-4 text-blue-600 hover:text-blue-800">
                        Start your first analysis
                    </button>
                </div>
            `;
            return;
        }

        container.innerHTML = `
            <div class="space-y-4">
                ${reports.map(report => this.renderReportCard(report)).join('')}
            </div>
        `;
    }

    renderReportCard(report) {
        const createdDate = new Date(report.created_at).toLocaleDateString();
        const platforms = Array.isArray(report.platforms_analyzed) ? 
            report.platforms_analyzed : [];
        
        return `
            <div class="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer"
                 onclick="showReportDetails(${report.id})">
                <div class="flex justify-between items-start mb-2">
                    <h4 class="font-semibold text-gray-900">${report.association_name}</h4>
                    <span class="text-sm text-gray-500">${createdDate}</span>
                </div>
                
                <div class="flex items-center space-x-4 mb-3">
                    <div class="flex items-center">
                        <i class="fas fa-chart-line text-blue-600 mr-1"></i>
                        <span class="text-sm text-gray-600">
                            Score: ${report.digital_presence_score?.toFixed(1) || 'N/A'}%
                        </span>
                    </div>
                    <div class="flex items-center">
                        <i class="fas fa-heart text-red-500 mr-1"></i>
                        <span class="text-sm text-gray-600">
                            Sentiment: ${this.getSentimentLabel(report.overall_sentiment)}
                        </span>
                    </div>
                </div>
                
                <div class="flex flex-wrap gap-2 mb-3">
                    ${platforms.map(platform => 
                        `<span class="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">
                            <i class="fab fa-${platform} mr-1"></i>${platform}
                        </span>`
                    ).join('')}
                </div>
                
                <div class="flex justify-between items-center">
                    <span class="text-sm text-gray-500">
                        ${report.report_type.replace('_', ' ').toUpperCase()}
                    </span>
                    <button class="text-blue-600 hover:text-blue-800 text-sm">
                        View Details <i class="fas fa-arrow-right ml-1"></i>
                    </button>
                </div>
            </div>
        `;
    }

    getSentimentLabel(score) {
        if (score > 0.1) return 'Positive';
        if (score < -0.1) return 'Negative';
        return 'Neutral';
    }

    async startAnalysis() {
        const formData = this.getFormData();
        
        if (!formData.associationName.trim()) {
            alert('Please enter a housing association name');
            return;
        }

        this.hideAnalysisModal();
        this.showProgressModal();

        try {
            const response = await fetch('/api/social-media/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    housing_association: {
                        name: formData.associationName
                    },
                    search_terms: formData.searchTerms,
                    platforms: formData.platforms,
                    analysis_depth: formData.analysisDepth
                })
            });

            const result = await response.json();

            this.hideProgressModal();

            if (result.success) {
                this.showSuccessMessage('Analysis completed successfully!');
                await this.loadDashboardStats();
                await this.loadRecentReports();
            } else {
                this.showErrorMessage(result.error || 'Analysis failed');
            }

        } catch (error) {
            this.hideProgressModal();
            this.showErrorMessage('Network error: ' + error.message);
        }
    }

    getFormData() {
        const associationName = document.getElementById('associationName')?.value || '';
        const searchTermsText = document.getElementById('searchTerms')?.value || '';
        const analysisDepth = document.getElementById('analysisDepth')?.value || 'standard';
        
        const searchTerms = searchTermsText
            .split('\n')
            .map(term => term.trim())
            .filter(term => term.length > 0);

        const platformCheckboxes = document.querySelectorAll('#platformCheckboxes input[type="checkbox"]:checked');
        const platforms = Array.from(platformCheckboxes).map(cb => cb.value);

        return {
            associationName,
            searchTerms,
            platforms,
            analysisDepth
        };
    }

    showProgressModal() {
        const modal = document.getElementById('progressModal');
        if (modal) {
            modal.classList.remove('hidden');
            this.simulateProgress();
        }
    }

    hideProgressModal() {
        const modal = document.getElementById('progressModal');
        if (modal) {
            modal.classList.add('hidden');
        }
    }

    simulateProgress() {
        const progressBar = document.getElementById('progressBar');
        const progressText = document.getElementById('progressText');
        
        if (!progressBar || !progressText) return;
        
        const steps = [
            { progress: 10, text: 'Initializing analysis...' },
            { progress: 25, text: 'Searching social media platforms...' },
            { progress: 50, text: 'Analyzing profiles and content...' },
            { progress: 75, text: 'Generating insights...' },
            { progress: 90, text: 'Creating report...' },
            { progress: 100, text: 'Analysis complete!' }
        ];

        let currentStep = 0;
        const interval = setInterval(() => {
            if (currentStep < steps.length) {
                const step = steps[currentStep];
                progressBar.style.width = step.progress + '%';
                progressText.textContent = step.text;
                currentStep++;
            } else {
                clearInterval(interval);
            }
        }, 2000);
    }

    showSuccessMessage(message) {
        // Simple alert for now - you can implement a toast system later
        alert(message);
    }

    showErrorMessage(message) {
        alert('Error: ' + message);
    }

    hideAllModals() {
        const modals = ['analysisModal', 'progressModal', 'reportModal'];
        modals.forEach(modalId => {
            const modal = document.getElementById(modalId);
            if (modal) {
                modal.classList.add('hidden');
            }
        });
    }

    hideAnalysisModal() {
        const modal = document.getElementById('analysisModal');
        if (modal) {
            modal.classList.add('hidden');
        }
    }

    async refreshReports() {
        await this.loadRecentReports();
        await this.loadDashboardStats();
    }
}

// Global functions for modal management
function showAnalysisModal() {
    const modal = document.getElementById('analysisModal');
    if (modal) {
        modal.classList.remove('hidden');
    }
}

function hideAnalysisModal() {
    const modal = document.getElementById('analysisModal');
    if (modal) {
        modal.classList.add('hidden');
    }
}

function hideReportModal() {
    const modal = document.getElementById('reportModal');
    if (modal) {
        modal.classList.add('hidden');
    }
}

async function showReportDetails(reportId) {
    // Mock report details for now
    const report = {
        id: reportId,
        association_name: 'Sample Housing Association',
        created_at: new Date().toISOString(),
        platforms_analyzed: ['twitter', 'facebook'],
        digital_presence_score: 75.5,
        overall_sentiment: 0.2,
        report_type: 'comprehensive_analysis',
        key_findings: [
            'Active presence on Twitter and Facebook',
            'Good community engagement rates',
            'Positive sentiment overall'
        ],
        recommendations: [
            'Expand to LinkedIn for professional networking',
            'Increase posting frequency on Instagram',
            'Implement social media monitoring tools'
        ]
    };
    
    displayReportDetails(report);
    const modal = document.getElementById('reportModal');
    if (modal) {
        modal.classList.remove('hidden');
    }
}

function displayReportDetails(report) {
    const container = document.getElementById('reportContent');
    if (!container) return;
    
    container.innerHTML = `
        <div class="space-y-6">
            <!-- Executive Summary -->
            <div>
                <h3 class="text-lg font-semibold text-gray-900 mb-3">Executive Summary</h3>
                <div class="bg-gray-50 rounded-lg p-4">
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                        <div class="text-center">
                            <div class="text-2xl font-bold text-blue-600">
                                ${report.digital_presence_score?.toFixed(1) || 'N/A'}%
                            </div>
                            <div class="text-sm text-gray-600">Digital Presence Score</div>
                        </div>
                        <div class="text-center">
                            <div class="text-2xl font-bold text-green-600">
                                ${Array.isArray(report.platforms_analyzed) ? report.platforms_analyzed.length : 0}
                            </div>
                            <div class="text-sm text-gray-600">Platforms Analyzed</div>
                        </div>
                        <div class="text-center">
                            <div class="text-2xl font-bold text-purple-600">
                                ${window.socialMediaIntelligence?.getSentimentLabel(report.overall_sentiment) || 'Neutral'}
                            </div>
                            <div class="text-sm text-gray-600">Overall Sentiment</div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Key Findings -->
            <div>
                <h3 class="text-lg font-semibold text-gray-900 mb-3">Key Findings</h3>
                <div class="space-y-2">
                    ${Array.isArray(report.key_findings) ? 
                        report.key_findings.map(finding => 
                            `<div class="flex items-start">
                                <i class="fas fa-check-circle text-green-500 mr-2 mt-1"></i>
                                <span class="text-gray-700">${finding}</span>
                            </div>`
                        ).join('') : 
                        '<p class="text-gray-500">No key findings available</p>'
                    }
                </div>
            </div>

            <!-- Recommendations -->
            <div>
                <h3 class="text-lg font-semibold text-gray-900 mb-3">Recommendations</h3>
                <div class="space-y-2">
                    ${Array.isArray(report.recommendations) ? 
                        report.recommendations.map(rec => 
                            `<div class="flex items-start">
                                <i class="fas fa-lightbulb text-yellow-500 mr-2 mt-1"></i>
                                <span class="text-gray-700">${rec}</span>
                            </div>`
                        ).join('') : 
                        '<p class="text-gray-500">No recommendations available</p>'
                    }
                </div>
            </div>

            <!-- Report Metadata -->
            <div class="border-t pt-4">
                <div class="grid grid-cols-2 gap-4 text-sm text-gray-600">
                    <div>
                        <strong>Analysis Date:</strong> ${new Date(report.created_at).toLocaleDateString()}
                    </div>
                    <div>
                        <strong>Report Type:</strong> ${report.report_type.replace('_', ' ').toUpperCase()}
                    </div>
                    <div>
                        <strong>Association:</strong> ${report.association_name}
                    </div>
                </div>
            </div>
        </div>
    `;
}

async function refreshReports() {
    if (window.socialMediaIntelligence) {
        await window.socialMediaIntelligence.refreshReports();
    }
}

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    // Wait for Chart.js to load
    if (typeof Chart !== 'undefined') {
        window.socialMediaIntelligence = new SocialMediaIntelligence();
    } else {
        console.error('Chart.js not loaded');
        // Fallback initialization without charts
        setTimeout(() => {
            window.socialMediaIntelligence = new SocialMediaIntelligence();
        }, 1000);
    }
});