const API_URL = 'https://flacmusicstore-production.up.railway.app';
let audioPlayer;
let currentAudio = null;
let seeking = false;

function initializeAudioPlayer(audioElement) {
    const seekSlider = document.getElementById('seek-slider');
    const currentTimeDisplay = document.getElementById('current-time');
    const durationDisplay = document.getElementById('duration');
    const playPauseBtn = document.getElementById('play-pause');

    // Update time displays
    audioElement.addEventListener('loadedmetadata', () => {
        seekSlider.max = Math.floor(audioElement.duration);
        durationDisplay.textContent = formatTime(audioElement.duration);
        currentTimeDisplay.textContent = '0:00';
        seekSlider.value = 0;
    });

    // Update current time
    audioElement.addEventListener('timeupdate', () => {
        if (!seeking) {
            seekSlider.value = Math.floor(audioElement.currentTime);
            currentTimeDisplay.textContent = formatTime(audioElement.currentTime);
        }
    });

    // Handle seeking
    seekSlider.addEventListener('mousedown', () => {
        seeking = true;
    });

    seekSlider.addEventListener('mousemove', (e) => {
        if (seeking) {
            const time = formatTime(seekSlider.value);
            currentTimeDisplay.textContent = time;
        }
    });

    seekSlider.addEventListener('mouseup', () => {
        seeking = false;
        audioElement.currentTime = seekSlider.value;
    });

    // Handle loading states
    audioElement.addEventListener('waiting', () => {
        playPauseBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
    });

    audioElement.addEventListener('playing', () => {
        playPauseBtn.innerHTML = '<i class="fas fa-pause"></i>';
    });

    audioElement.addEventListener('ended', () => {
        playPauseBtn.innerHTML = '<i class="fas fa-play"></i>';
        seekSlider.value = 0;
        currentTimeDisplay.textContent = '0:00';
    });

    // Add error handling
    audioElement.addEventListener('error', (e) => {
        console.error('Audio error:', e);
        alert('Error playing track. Please try again.');
        playPauseBtn.innerHTML = '<i class="fas fa-play"></i>';
    });
}

async function playTrack(fileId, title) {
    try {
        const playerContainer = document.getElementById('player-container');
        const audioPlayer = document.getElementById('audio-player');
        const nowPlaying = document.getElementById('now-playing');
        const playPauseBtn = document.getElementById('play-pause');
        
        // Stop current audio if playing
        if (currentAudio && !currentAudio.paused) {
            currentAudio.pause();
        }

        playerContainer.classList.remove('hidden');
        nowPlaying.textContent = title;
        
        // Add timestamp to prevent caching
        const timestamp = new Date().getTime();
        const streamUrl = `${API_URL}/stream/${fileId}?t=${timestamp}`;
        
        // Reset player state
        audioPlayer.src = streamUrl;
        playPauseBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
        
        // Initialize new audio player
        initializeAudioPlayer(audioPlayer);
        currentAudio = audioPlayer;
        
        // Start playing
        const playPromise = audioPlayer.play();
        if (playPromise !== undefined) {
            playPromise.catch(error => {
                console.error('Playback error:', error);
            });
        }
    } catch (error) {
        console.error('Error playing track:', error);
        alert('Error playing track. Please try again.');
    }
}

// Update the formatTime function to handle larger durations
function formatTime(seconds) {
    if (isNaN(seconds) || !isFinite(seconds)) return '0:00';
    
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    
    if (hours > 0) {
        return `${hours}:${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
    }
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
}

// Update the togglePlay function
function togglePlay() {
    const audioPlayer = document.getElementById('audio-player');
    const playPauseBtn = document.getElementById('play-pause');
    
    if (!audioPlayer.src) return;
    
    if (audioPlayer.paused) {
        const playPromise = audioPlayer.play();
        if (playPromise !== undefined) {
            playPromise.catch(error => {
                console.error('Playback error:', error);
                playPauseBtn.innerHTML = '<i class="fas fa-play"></i>';
            });
        }
    } else {
        audioPlayer.pause();
        playPauseBtn.innerHTML = '<i class="fas fa-play"></i>';
    }
}


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
        const downloadUrl = `${API_URL}/api/download/${fileId}`;
        console.log('Downloading track:', fileId);
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
