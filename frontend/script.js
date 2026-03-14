document.addEventListener("DOMContentLoaded", () => {
    // ------------------------------------------------------------------------
    // Tabs Navigation
    // ------------------------------------------------------------------------
    const navButtons = document.querySelectorAll('.nav-btn');
    const tabPanes = document.querySelectorAll('.tab-pane');

    navButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            // Remove active class
            navButtons.forEach(b => b.classList.remove('active'));
            tabPanes.forEach(t => t.classList.remove('active'));

            // Add active class
            btn.classList.add('active');
            const target = btn.getAttribute('data-target');
            document.getElementById(target).classList.add('active');
            
            // Re-render charts if analytics tab is opened
            if(target === 'tab-analytics') {
                loadAnalytics();
            }
        });
    });

    // ------------------------------------------------------------------------
    // Upload Dataset
    // ------------------------------------------------------------------------
    const fileInput = document.getElementById('fileDownload');
    const uploadBtn = document.getElementById('upload-btn');
    const uploadArea = document.getElementById('upload-area');
    
    // Drag & Drop visual feedback
    uploadArea.addEventListener('dragover', (e) => {
        uploadArea.classList.add('dragover');
    });
    uploadArea.addEventListener('dragleave', (e) => {
        uploadArea.classList.remove('dragover');
    });
    uploadArea.addEventListener('drop', (e) => {
        uploadArea.classList.remove('dragover');
    });

    fileInput.addEventListener('change', () => {
        if(fileInput.files.length > 0) {
            uploadArea.querySelector('.upload-text').innerText = fileInput.files[0].name;
            uploadBtn.style.display = 'inline-block';
        }
    });

    uploadBtn.addEventListener('click', async () => {
        const file = fileInput.files[0];
        if(!file) return;

        uploadBtn.innerText = "Processing...";
        uploadBtn.disabled = true;

        const formData = new FormData();
        formData.append('file', file);

        try {
            // Check file extension to route appropriately
            let endpoint = '/api/dashboard/upload_dataset'; // default for csv/excel
            if (file.name.endsWith('.fasta') || file.name.endsWith('.fa')) {
                endpoint = '/upload-fasta'; 
            }

            const response = await fetch(endpoint, {
                method: 'POST',
                body: formData
            });

            if(!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || "Upload failed");
            }

            const data = await response.json();
            
            // Handle tabular data preview for CSV/Excel
            if(data.preview) {
                const tableContainer = document.getElementById('upload-preview');
                const thead = document.querySelector('#preview-table thead');
                const tbody = document.querySelector('#preview-table tbody');
                
                // Clear existing
                thead.innerHTML = '';
                tbody.innerHTML = '';

                // Headers
                if(data.preview.length > 0) {
                    const trH = document.createElement('tr');
                    Object.keys(data.preview[0]).forEach(key => {
                        const th = document.createElement('th');
                        th.innerText = key;
                        trH.appendChild(th);
                    });
                    thead.appendChild(trH);
                }

                // Rows
                data.preview.forEach(row => {
                    const tr = document.createElement('tr');
                    Object.values(row).forEach(val => {
                        const td = document.createElement('td');
                        td.innerText = val !== null ? val : '';
                        tr.appendChild(td);
                    });
                    tbody.appendChild(tr);
                });

                tableContainer.style.display = 'block';
                uploadArea.querySelector('.upload-text').innerHTML = `<span style="color:var(--success)">✅ Uploaded: ${file.name}</span>`;
            } else if (data.predictions) {
                // Handle FASTA response showing prediction
                document.querySelector('[data-target="tab-prediction"]').click();
                displayPrediction(data);
            }

        } catch(error) {
            alert(`Error: ${error.message}`);
        } finally {
            uploadBtn.innerText = "Process File";
            uploadBtn.disabled = false;
        }
    });

    // ------------------------------------------------------------------------
    // Patient Form Submit
    // ------------------------------------------------------------------------
    const patientForm = document.getElementById('patient-form');
    
    patientForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const submitBtn = document.getElementById('submit-patient-btn');
        submitBtn.innerText = "Processing...";
        submitBtn.disabled = true;

        const formData = new FormData(patientForm);
        const payload = Object.fromEntries(formData.entries());
        // Basic type conversions
        payload.age = parseInt(payload.age);
        payload.hospital_stay = parseInt(payload.hospital_stay || 0);

        try {
            const response = await fetch('/api/dashboard/predict', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if(!response.ok) {
                const err = await response.json();
                throw new Error(err.detail || 'Prediction request failed');
            }

            const data = await response.json();
            
            // Switch to prediction tab & show result
            document.querySelector('[data-target="tab-prediction"]').click();
            displayPrediction(data);

        } catch(error) {
            alert(`Error: ${error.message}`);
        } finally {
            submitBtn.innerText = "Run Prediction";
            submitBtn.disabled = false;
        }
    });

    // ------------------------------------------------------------------------
    // Display Prediction Logic
    // ------------------------------------------------------------------------
    function displayPrediction(data) {
        const resultBox = document.getElementById('prediction-result');
        const detailsBox = document.getElementById('prediction-details');
        
        resultBox.classList.remove('empty', 'resistant', 'susceptible');
        
        // Handling direct patient input format OR fasta upload format
        let status = "Unknown";
        let subtext = "";
        let isResistant = false;

        if (data.result) {
            // Patient input format
            status = data.result;
            isResistant = status === 'Resistant';
            const speciesStr = data.species || "";
            const abxStr = data.antibiotic || "";
            subtext = `<br><span style="font-size: 0.9em; font-weight: 400;">Pathogen: ${speciesStr} | Antibiotic: ${abxStr}</span>`;
            if(data.warnings && data.warnings.length) {
                subtext += `<br><br><span style="color:var(--warning)">⚠️ Warnings: ${data.warnings.join(', ')}</span>`;
            }
        } 
        else if (data.predictions) {
            // FASTA format (returns multiple antibiotics)
            status = "Analysis Complete";
            subtext = `<br><br><b>Overall Results:</b><br>`;
            let resCount = 0;
            for(const [abx, info] of Object.entries(data.predictions)) {
                if(info.prediction === "Resistant") resCount++;
                const color = info.prediction === "Resistant" ? "var(--danger)" : "var(--success)";
                subtext += `<div style="margin-top:5px"><span style="color:${color}">${info.prediction}</span> - ${abx} (Conf: ${(info.confidence*100).toFixed(1)}%)</div>`;
            }
            if (resCount > 0) {
                isResistant = true;
                status = "Resistant Strains Detected";
            } else {
                status = "All Susceptible";
            }
            if(data.warnings && data.warnings.length) {
                subtext += `<br><span style="color:var(--warning)">⚠️ Alerts: ${data.warnings.join(', ')}</span>`;
            }
        }

        resultBox.innerHTML = `<h2><strong>${status}</strong></h2>${subtext}`;
        
        if (isResistant || status === "Resistant Strains Detected") {
            resultBox.classList.add('resistant');
        } else {
            resultBox.classList.add('susceptible');
        }
    }


    // ------------------------------------------------------------------------
    // Analytics Dashboard Logic (Chart.js)
    // ------------------------------------------------------------------------
    let chartsRendered = false;
    
    async function loadAnalytics() {
        if(chartsRendered) return; // Prevent re-rendering
        
        try {
            const res = await fetch('/api/dashboard/analytics');
            if(!res.ok) throw new Error("Could not load analytics data");
            const data = await res.json();
            
            renderCharts(data);
            chartsRendered = true;
        } catch (e) {
            console.error(e);
        }
    }

    function renderCharts(data) {
        Chart.defaults.color = '#94a3b8';
        Chart.defaults.font.family = 'Inter';

        // 1. Infection Distribution (Doughnut)
        new Chart(document.getElementById('infectionChart'), {
            type: 'doughnut',
            data: {
                labels: Object.keys(data.infection_distribution),
                datasets: [{
                    data: Object.values(data.infection_distribution),
                    backgroundColor: ['#3b82f6', '#8b5cf6', '#a855f7'],
                    borderWidth: 0
                }]
            },
            options: { responsive: true, maintainAspectRatio: false }
        });

        // 2. Antibiotic Usage (Bar)
        new Chart(document.getElementById('antibioticChart'), {
            type: 'bar',
            data: {
                labels: Object.keys(data.antibiotic_usage),
                datasets: [{
                    label: 'Prescriptions',
                    data: Object.values(data.antibiotic_usage),
                    backgroundColor: 'rgba(59, 130, 246, 0.8)',
                    borderRadius: 4
                }]
            },
            options: { 
                responsive: true, 
                maintainAspectRatio: false,
                scales: { y: { beginAtZero: true, grid: { color: 'rgba(255,255,255,0.05)' } }, x: { grid: { display: false } } }
            }
        });

        // 3. Resistance Trends (Line)
        new Chart(document.getElementById('resistanceChart'), {
            type: 'line',
            data: {
                labels: data.resistance_trends.labels,
                datasets: [{
                    label: 'Resistance %',
                    data: data.resistance_trends.data,
                    borderColor: '#ef4444',
                    backgroundColor: 'rgba(239, 68, 68, 0.2)',
                    fill: true,
                    tension: 0.4
                }]
            },
            options: { 
                responsive: true, 
                maintainAspectRatio: false,
                scales: { y: { beginAtZero: true, max: 100, grid: { color: 'rgba(255,255,255,0.05)' } }, x: { grid: { display: false } } }
            }
        });

        // 4. Model Accuracy (Radar)
        new Chart(document.getElementById('accuracyChart'), {
            type: 'radar',
            data: {
                labels: Object.keys(data.model_accuracy),
                datasets: [{
                    label: 'Accuracy %',
                    data: Object.values(data.model_accuracy),
                    backgroundColor: 'rgba(16, 185, 129, 0.2)',
                    borderColor: '#10b981',
                    pointBackgroundColor: '#10b981'
                }]
            },
            options: { 
                responsive: true, 
                maintainAspectRatio: false,
                scales: { r: { angleLines: { color: 'rgba(255,255,255,0.1)' }, grid: { color: 'rgba(255,255,255,0.1)' }, pointLabels: { color: '#94a3b8' }, ticks: { display: false } } }
            }
        });
    }
});
