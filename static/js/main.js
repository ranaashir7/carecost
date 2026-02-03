// Main JavaScript functionality
class CareCostApp {
    constructor() {
        this.selectedIcdIndex = null;
        this.icdCodes = [];
        this.currentSymptom = '';
        this.init();
    }

    init() {
        this.bindEvents();
    }

    bindEvents() {
        // Loading overlay management
        this.loadingOverlay = document.getElementById('loadingOverlay');
        
        // Form submissions
        const symptomForm = document.getElementById('symptomForm');
        if (symptomForm) {
            symptomForm.addEventListener('submit', (e) => this.handleSymptomSearch(e));
        }

        const zipForm = document.getElementById('zipForm');
        if (zipForm) {
            zipForm.addEventListener('submit', (e) => this.handleCostAnalysis(e));
        }

        // Zip code validation on input
        const zipInput = document.getElementById('zipCode');
        if (zipInput) {
            zipInput.addEventListener('input', (e) => this.validateZipCode(e.target.value));
        }

        // Smooth scrolling for anchor links
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            });
        });
    }

    showLoading() {
        this.loadingOverlay.classList.add('show');
    }

    hideLoading() {
        this.loadingOverlay.classList.remove('show');
    }

    async handleSymptomSearch(e) {
        e.preventDefault();
        
        const symptomInput = document.getElementById('symptom');
        const symptom = symptomInput.value.trim();
        
        if (!symptom) {
            this.showError('Please enter a symptom');
            return;
        }

        this.currentSymptom = symptom;
        this.showLoading();

        try {
            const response = await fetch('/api/search-icd', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ symptom: symptom })
            });

            const data = await response.json();

            if (response.ok) {
                this.icdCodes = data.icd_codes;
                this.displayIcdCodes(data.icd_codes);
                this.showSection('icdSection');
            } else {
                this.showError(data.error || 'Failed to search ICD codes');
            }
        } catch (error) {
            this.showError('Network error. Please try again.');
            console.error('Error:', error);
        } finally {
            this.hideLoading();
        }
    }

    displayIcdCodes(icdCodes) {
        const container = document.getElementById('icdResults');
        
        if (!icdCodes || icdCodes.length === 0) {
            container.innerHTML = '<p class="text-center">No matching codes found.</p>';
            return;
        }

        container.innerHTML = icdCodes.map((icd, index) => `
            <div class="icd-card" data-index="${index}" onclick="app.selectIcd(${index})">
                <div class="icd-header">
                    <span class="icd-code">${icd.code}</span>
                </div>
                <div class="icd-name">${icd.name}</div>
                <div class="icd-description">${icd.description}</div>
            </div>
        `).join('');
    }

    selectIcd(index) {
        // Remove previous selection
        document.querySelectorAll('.icd-card').forEach(card => {
            card.classList.remove('selected');
        });

        // Add selection to clicked card
        const selectedCard = document.querySelector(`[data-index="${index}"]`);
        selectedCard.classList.add('selected');
        
        this.selectedIcdIndex = index;
        
        // Show zip code section after a brief delay
        setTimeout(() => {
            this.showSection('zipSection');
        }, 300);
    }

    async validateZipCode(zipCode) {
        const validationDiv = document.getElementById('zipValidation');
        
        if (zipCode.length !== 5) {
            validationDiv.innerHTML = '';
            return;
        }

        try {
            const response = await fetch('/api/validate-zip', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ zip_code: zipCode })
            });

            const data = await response.json();

            if (data.valid) {
                validationDiv.innerHTML = '<i class="fas fa-check"></i> Valid ZIP code';
                validationDiv.className = 'validation-message success';
            } else {
                validationDiv.innerHTML = '<i class="fas fa-times"></i> Invalid ZIP code';
                validationDiv.className = 'validation-message error';
            }
        } catch (error) {
            console.error('ZIP validation error:', error);
        }
    }

    async handleCostAnalysis(e) {
        e.preventDefault();
        
        const zipInput = document.getElementById('zipCode');
        const zipCode = zipInput.value.trim();
        
        if (!zipCode || zipCode.length !== 5) {
            this.showError('Please enter a valid 5-digit ZIP code');
            return;
        }

        if (this.selectedIcdIndex === null) {
            this.showError('Please select an ICD code first');
            return;
        }

        this.showLoading();

        try {
            const response = await fetch('/api/analyze-costs', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    symptom: this.currentSymptom,
                    icd_selection_index: this.selectedIcdIndex,
                    zip_code: zipCode
                })
            });

            const data = await response.json();

            if (response.ok) {
                this.displayCostResults(data.analysis);
                this.showSection('resultsSection');
            } else {
                this.showError(data.error || 'Failed to analyze costs');
            }
        } catch (error) {
            this.showError('Network error. Please try again.');
            console.error('Error:', error);
        } finally {
            this.hideLoading();
        }
    }

    displayCostResults(analysis) {
        const container = document.getElementById('costResults');
        const selectedIcd = analysis.selected_icd;
        const costAnalysis = analysis.cost_analysis;

        let html = `
            <div class="selected-diagnosis">
                <div class="diagnosis-code">${selectedIcd.code}</div>
                <h3>${selectedIcd.name}</h3>
                <p>${selectedIcd.description}</p>
            </div>
        `;

        if (costAnalysis.categories && costAnalysis.categories.length > 0) {
            html += '<div class="cost-categories">';
            
            costAnalysis.categories.forEach(category => {
                html += `
                    <div class="category-card">
                        <div class="category-header">${category.category}</div>
                `;

                if (category.in_network_range) {
                    html += `
                        <div class="cost-row">
                            <span class="cost-label">In-Network Range</span>
                            <span class="cost-value">$${category.in_network_range.min.toLocaleString()} - $${category.in_network_range.max.toLocaleString()}</span>
                        </div>
                    `;
                } else {
                    html += `
                        <div class="cost-row">
                            <span class="cost-label">In-Network Range</span>
                            <span class="cost-value">No data available</span>
                        </div>
                    `;
                }

                if (category.out_network_range) {
                    html += `
                        <div class="cost-row">
                            <span class="cost-label">Out-of-Network Range</span>
                            <span class="cost-value">$${category.out_network_range.min.toLocaleString()} - $${category.out_network_range.max.toLocaleString()}</span>
                        </div>
                    `;
                } else {
                    html += `
                        <div class="cost-row">
                            <span class="cost-label">Out-of-Network Range</span>
                            <span class="cost-value">No data available</span>
                        </div>
                    `;
                }

                html += '</div>';
            });

            html += '</div>';
        }

        // Overall summary
        if (costAnalysis.overall_in_network_range || costAnalysis.overall_out_network_range) {
            html += `
                <div class="cost-summary">
                    <div class="summary-title">Overall Cost Summary</div>
                    <div class="summary-grid">
            `;

            if (costAnalysis.overall_in_network_range) {
                html += `
                    <div class="summary-item">
                        <h4>Total In-Network Range</h4>
                        <div class="amount">$${costAnalysis.overall_in_network_range.min.toLocaleString()} - $${costAnalysis.overall_in_network_range.max.toLocaleString()}</div>
                    </div>
                `;
            } else {
                html += `
                    <div class="summary-item">
                        <h4>Total In-Network Range</h4>
                        <div class="amount">No data available</div>
                    </div>
                `;
            }

            if (costAnalysis.overall_out_network_range) {
                html += `
                    <div class="summary-item">
                        <h4>Total Out-of-Network Range</h4>
                        <div class="amount">$${costAnalysis.overall_out_network_range.min.toLocaleString()} - $${costAnalysis.overall_out_network_range.max.toLocaleString()}</div>
                    </div>
                `;
            } else {
                html += `
                    <div class="summary-item">
                        <h4>Total Out-of-Network Range</h4>
                        <div class="amount">No data available</div>
                    </div>
                `;
            }

            html += `
                    </div>
                </div>
            `;
        }

        container.innerHTML = html;
    }

    showSection(sectionId) {
        const section = document.getElementById(sectionId);
        if (section) {
            section.classList.remove('hidden');
            section.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    }

    showError(message) {
        // Simple error display - you could make this more sophisticated
        alert(message);
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new CareCostApp();
});
