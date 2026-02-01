let topicsChart = null;

let trendChart = null; // New variable for the line chart

let recommendationsRendered = false;

let pollingInterval = null;




async function handleStart() {
    const channelId = document.getElementById('channelInput').value;
    const btn = document.getElementById('runBtn');
    
    btn.disabled = true;
    btn.innerText = "Agents Working...";

    await fetch('/api/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ channel_id: channelId })
    });

    startPolling();
}
function startPolling() {
    if (pollingInterval) return;
    pollingInterval = setInterval(async () => {
        const response = await fetch('/api/status');
        const data = await response.json();

        console.log("STATUS PAYLOAD:", data);


        // Update Pipeline Status
        document.getElementById('statusValue').innerText = data.status;
        document.getElementById('statusDetails').innerText = data.details;

        // --- NEW: PROGRESS BAR LOGIC ---
        // Parses "Step 3/6" or "Step 5/6" to calculate percentage
        if (data.details && data.details.includes("Step")) {
            const match = data.details.match(/Step (\d+)\/(\d+)/);
            if (match) {
                const current = parseInt(match[1]);
                const total = parseInt(match[2]);
                const percentage = Math.round((current / total) * 100);
                updateGlobalProgressBar(percentage);

                // Update Specific Card Bar (if an index is being processed)
                // Note: You'll need to pass 'target_index' in your FastAPI status response
                if (data.target_index !== undefined) {
                    const cardBar = document.getElementById(`prog-bar-${data.target_index}`);
                    const cardLabel = document.getElementById(`prog-label-${data.target_index}`);
                    if (cardBar) {
                        cardBar.style.width = percentage + "%";
                        cardLabel.innerText = `Processing: ${percentage}%`;
                    }
                }
            }
        }

        // Update Channel Overview with the new order
        if (data.stats && data.stats.channel_name) {
            // 1. Handle Logo
            const logoImg = document.getElementById('channelLogo');
            if (data.stats.channel_logo && data.stats.channel_logo !== "") {
                logoImg.src = data.stats.channel_logo;
                logoImg.style.display = 'block';
            } 

            // 2. Handle Text Stats
            document.getElementById('displayChannelName').innerText = data.stats.channel_name;
            document.getElementById('statSubscribers').innerText = data.stats.subscribers;
            document.getElementById('statVideos').innerText = data.stats.videos;
            document.getElementById('statViews').innerText = data.stats.views;
            document.getElementById('statEngagement').innerText = data.stats.engagement;
            document.getElementById('displayDescription').innerText = data.stats.channel_description;
        }

        // Update Top Topics Chart
        if (data.top_videos && data.top_videos.length > 0) {
            updateChart(data.top_videos);
        }

        // Inside your startPolling loop, add:
        if (data.recent_engagement && data.recent_engagement.length > 0) {
            updateTrendChart(data.recent_engagement);
        }

                    if (
                data.recommendations &&
                data.recommendations.length > 0 &&
                !recommendationsRendered
            ) {
                renderRecommendations(data.recommendations);
                recommendationsRendered = true;
            }

                if (data.status === "Error") {
            clearInterval(pollingInterval);
            pollingInterval = null;
        }
                    if (
            data.status === "Completed" &&
            data.target_index === null
        ) {
            clearInterval(pollingInterval);
            pollingInterval = null;
        }

        if (
            (data.status === "Completed" || data.status === "Error") &&
            data.target_index === null
        ) {
            document.getElementById('runBtn').disabled = false;
            document.getElementById('runBtn').innerText = "Launch Agents";
        }
        // Show generated video when ready
        if (data.video_url) {
            const videoCard = document.getElementById('videoOutputCard');
            const videoEl = document.getElementById('generatedVideo');
            const downloadBtn = document.getElementById('downloadVideoBtn');


            if (data.video_url && videoEl.src !== location.origin + data.video_url) {
                videoEl.src = data.video_url;
                downloadBtn.href = data.video_url;
                videoCard.style.display = 'block';
                videoCard.scrollIntoView({ behavior: "smooth" });

            }
        }

                if (data.status === "GeneratingVideo" && data.target_index !== undefined) {
            const btn = document.getElementById(`gen-btn-${data.target_index}`);
            if (btn) {
                btn.disabled = true;
                btn.innerText = "Rendering…";
            }
        }

                if (data.video_url && data.target_index !== undefined) {
            const btn = document.getElementById(`gen-btn-${data.target_index}`);
            if (btn) {
                btn.innerText = "Generated ✓";
                btn.disabled = true;
            }
        }

        
    }, 3000);
}

// Helper for the status bar at the top of the dashboard
function updateGlobalProgressBar(percent) {
    const bar = document.getElementById('pipelineProgressBar');
    if (bar) {
        bar.style.width = percent + "%";
        bar.innerText = percent + "%";
    }
}

function updateChart(videoData) {
    const ctx = document.getElementById('topicsChart').getContext('2d');
    const labels = videoData.map(v => v.title.substring(0, 30) + "...");
    const values = videoData.map(v => v.engagement_rate * 100);

    if (topicsChart) topicsChart.destroy();

    topicsChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Engagement %',
                data: values,
                backgroundColor: '#FF0000',
                borderRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: { beginAtZero: true, grid: { color: '#333' } },
                x: { grid: { display: false } }
            },
            plugins: { legend: { display: false } }
        }
    });
}

function updateTrendChart(engagementData) {
    const ctx = document.getElementById('engagementTrendChart').getContext('2d');
    
    // Reverse the data if your API sends it oldest to newest
    // We want the chart to flow from left (past) to right (recent)
    const labels = engagementData.map(v => v.title.substring(0, 20) + "...");
    const values = engagementData.map(v => (v.engagement_rate * 100).toFixed(2));

    if (trendChart) trendChart.destroy();

    trendChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Engagement Rate %',
                data: values,
                borderColor: '#FF0000', // YouTube Red
                backgroundColor: 'rgba(255, 0, 0, 0.1)',
                borderWidth: 3,
                tension: 0.4, // Smooth curves
                fill: true,
                pointBackgroundColor: '#fff',
                pointRadius: 5
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: { 
                    beginAtZero: true, 
                    grid: { color: '#333' },
                    ticks: { color: '#aaa' } 
                },
                x: { 
                    grid: { color: '#333' },
                    ticks: { color: '#fff' }
                }
            },
            plugins: {
                legend: { display: false }
            }
        }
    });
}

function renderRecommendations(recs) {
    const container = document.getElementById('recommendationsContainer');

    

    container.innerHTML = '';

    recs.forEach((rec, index) => {
        const views = rec.estimated_engagement?.["Expected views"] ?? "N/A";
        const rate = rec.estimated_engagement?.["Engagement rate"] ?? "N/A";

        const card = document.createElement('div');
        card.className = 'rec-card';
        card.innerHTML = `
            <div class="rec-badge">Option ${index + 1}</div>
            <h4>${rec.target_title}</h4>
            <p class="rec-topic"><strong>Topic:</strong> ${rec.recommended_topic}</p>

            <div class="rec-stats">
                <span>📊 ${views.toLocaleString()} views · ${rate}% engagement</span>
                <span>⏱️ ${rec.estimated_duration}</span>
            </div>

            <div id="prog-wrapper-${index}" class="progress-wrapper" style="display:none; margin: 10px 0;">
                <small id="prog-label-${index}">Preparing...</small>
                <div class="progress-container">
                    <div id="prog-bar-${index}" class="progress-fill"></div>
                </div>
            </div>

            <button id="gen-btn-${index}" class="gen-specific-btn"
                    onclick="generateSpecificVideo(${index})">
                Generate This Video
            </button>
        `;
        container.appendChild(card);
    });
}


async function generateSpecificVideo(index) {
    const btn = document.getElementById(`gen-btn-${index}`);
    const progWrapper = document.getElementById(`prog-wrapper-${index}`);
    
    btn.disabled = true;
    btn.innerText = "Preparing...";
    progWrapper.style.display = 'block';

    const response = await fetch('/api/generate_selected', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ index: index })
    });

        if (!response.ok) {
        btn.disabled = false;
        btn.innerText = "Generate This Video";
        progWrapper.style.display = 'none';
    }

    if (response.ok) {
        startPolling();
    }
}