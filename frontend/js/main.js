const API_URL = 'https://flacmusicstore-production.up.railway.app';
let audioPlayer;

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
        
        // Remove the data.success check since the API returns the array directly
        if (Array.isArray(data)) {
            displayResults(data);
            return data;
        } else {
            console.error('Invalid response format:', data);
            return [];
        }
    } catch (error) {
        console.error('Error searching tracks:', error);
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
        // Clean up the title by removing the file extension
        const cleanTitle = track.title.replace('.flac', '');
        const cleanArtist = track.artist.replace('.flac', '');
        const cleanAlbum = track.album.replace('.flac', '');

        const trackElement = document.createElement('div');
        trackElement.className = 'track-item';
        trackElement.innerHTML = `
            <h3>${cleanTitle}</h3>
            <p>${cleanArtist} - ${cleanAlbum}</p>
            <div class="track-buttons">
                <button class="play-button" onclick="playTrack('${track.file_id}', '${cleanTitle.replace(/'/g, "\\'")}')">Play</button>
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
        const streamUrl = `${API_URL}/stream/${fileId}?t=${timestamp}`;
        audioPlayer.src = streamUrl;
        
        // Rest of the function remains the same...
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
        console.log('Download URL:', downloadUrl);
        // Initiate download
        const link = document.createElement('a');
        link.href = downloadUrl;
        link.download = ''; // Optional: specify a filename if needed
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
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
