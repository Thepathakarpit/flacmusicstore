const API_URL = 'https://flacmusicstore-production.up.railway.app';
let audioPlayer;
let isPlaying = false;

async function searchTracks(query) {
    try {
        if (!query || query.trim() === '') {
            console.log('Empty search query');
            return [];
        }
        
        const searchUrl = `${API_URL}/api/search?q=${encodeURIComponent(query)}`;
        console.log('Searching:', searchUrl);
        
        const response = await fetch(searchUrl);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Received data:', data);
        
        // Directly check if data.results is an array and has elements
        if (data.results && Array.isArray(data.results) && data.results.length > 0) {
            displayResults(data.results);
            return data.results;
        } else {
            console.error('No results found or unknown error');
            displayResults([]); // Clear previous results if no new results
            return [];
        }
    } catch (error) {
        console.error('Error searching tracks:', error.message || error);
        displayResults([]); // Clear previous results on error
        return [];
    }
}

function displayResults(results) {
    const resultsContainer = document.getElementById('results');
    resultsContainer.innerHTML = ''; // Clear previous results

    console.log('Displaying results:', results);

    if (!results || results.length === 0) {
        resultsContainer.innerHTML = '<p>No results found</p>';
        return;
    }

    results.forEach(track => {
        const trackElement = document.createElement('div');
        trackElement.className = 'track-item';
        trackElement.innerHTML = `
            <h3>${track.title}</h3>
            <p>${track.artist} - ${track.album}</p>
            <div class="track-buttons">
                <button class="play-button" onclick="playTrack('${track.file_id}', '${track.title}')">Play</button>
                <button class="download-button" onclick="downloadTrack('${track.file_id}')">Download</button>
            </div>
        `;
        resultsContainer.appendChild(trackElement);
    });
}

async function playTrack(fileId, title) {
    try {
        const playerContainer = document.getElementById('player-container');
        const audioPlayer = document.getElementById('audio-player');
        const nowPlaying = document.getElementById('now-playing');
        const seekSlider = document.getElementById('seek-slider');
        const playPauseBtn = document.getElementById('play-pause');
        
        playerContainer.classList.remove('hidden');
        nowPlaying.textContent = title;
        
        const timestamp = new Date().getTime();
        audioPlayer.src = `${API_URL}/stream/${fileId}?t=${timestamp}`;
        
        audioPlayer.addEventListener('loadedmetadata', () => {
            seekSlider.max = Math.floor(audioPlayer.duration);
            document.getElementById('duration').textContent = formatTime(audioPlayer.duration);
        });
        
        audioPlayer.addEventListener('timeupdate', () => {
            seekSlider.value = Math.floor(audioPlayer.currentTime);
            document.getElementById('current-time').textContent = formatTime(audioPlayer.currentTime);
            
            playPauseBtn.innerHTML = audioPlayer.paused ? 
                '<i class="fas fa-play"></i>' : 
                '<i class="fas fa-pause"></i>';
        });
        
        seekSlider.addEventListener('input', () => {
            const time = Number(seekSlider.value);
            audioPlayer.currentTime = time;
            document.getElementById('current-time').textContent = formatTime(time);
        });
        
        audioPlayer.addEventListener('ended', () => {
            playPauseBtn.innerHTML = '<i class="fas fa-play"></i>';
        });
        
        audioPlayer.play();
    } catch (error) {
        console.error('Error playing track:', error);
        alert('Error playing track. Please try again.');
    }
}

function togglePlay() {
    const audioPlayer = document.getElementById('audio-player');
    const playPauseBtn = document.getElementById('play-pause');
    
    if (audioPlayer.paused) {
        audioPlayer.play();
        playPauseBtn.innerHTML = '<i class="fas fa-pause"></i>';
    } else {
        audioPlayer.pause();
        playPauseBtn.innerHTML = '<i class="fas fa-play"></i>';
    }
}

function formatTime(seconds) {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
}

// Remove duplicate event listener for 'keydown'
document.addEventListener('keydown', (e) => {
    if (e.code === 'Space' && e.target.tagName !== 'INPUT') {
        e.preventDefault();
        togglePlay();
    }
});

// Ensure handleSearch is defined and accessible
async function handleSearch() {
    try {
        const searchInput = document.getElementById('search-input');
        const query = searchInput.value;
        
        // Show loading state
        const results = await searchTracks(query);
        
        // Display results
        displayResults(results);
    } catch (error) {
        console.error('Search failed:', error);
        alert('Error searching tracks. Please try again.');
    }
}

function downloadTrack(fileId) {
    try {
        console.log('Downloading track:', fileId);
        const downloadUrl = `${API_URL}/api/download/${fileId}`;
    } catch (error) {
        console.error('Error downloading track:', error);
        alert('Error downloading track. Please try again.');
    }
}

// Initialize when the page loads
document.addEventListener('DOMContentLoaded', () => {
    console.log('Page loaded, initializing...');
    audioPlayer = document.getElementById('audio-player');
}); 
