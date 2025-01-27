const API_URL = 'https://flacmusicstore-production.up.railway.app';
let audioPlayer;
let currentAudio = null;
let seeking = false;
let mouseDownOnSlider = false;

function initializeAudioPlayer(audioElement) {
    const seekSlider = document.getElementById('seek-slider');
    const currentTimeDisplay = document.getElementById('current-time');
    const durationDisplay = document.getElementById('duration');
    const playPauseBtn = document.getElementById('play-pause');
    const progressCurrent = document.getElementById('progress-current');
    const progressBuffer = document.getElementById('progress-buffer');
    const volumeSlider = document.getElementById('volume-slider');
    const volumeBtn = document.getElementById('volume-btn');

    // Update time displays and buffer progress
    audioElement.addEventListener('loadedmetadata', () => {
        seekSlider.max = audioElement.duration;
        durationDisplay.textContent = formatTime(audioElement.duration);
        currentTimeDisplay.textContent = '0:00';
        seekSlider.value = 0;
    });

    audioElement.addEventListener('progress', () => {
        if (audioElement.buffered.length > 0) {
            const bufferedEnd = audioElement.buffered.end(audioElement.buffered.length - 1);
            const duration = audioElement.duration;
            progressBuffer.style.width = `${(bufferedEnd / duration) * 100}%`;
        }
    });

    // Update current time and progress
    audioElement.addEventListener('timeupdate', () => {
        if (!mouseDownOnSlider) {
            const currentTime = audioElement.currentTime;
            const duration = audioElement.duration;
            
            seekSlider.value = currentTime;
            currentTimeDisplay.textContent = formatTime(currentTime);
            progressCurrent.style.width = `${(currentTime / duration) * 100}%`;
        }
    });

    // Improved seeking functionality
    seekSlider.addEventListener('mousedown', () => {
        mouseDownOnSlider = true;
        audioElement.pause();
    });

    seekSlider.addEventListener('mousemove', (e) => {
        if (mouseDownOnSlider) {
            const time = seekSlider.value;
            currentTimeDisplay.textContent = formatTime(time);
            progressCurrent.style.width = `${(time / audioElement.duration) * 100}%`;
        }
    });

    seekSlider.addEventListener('mouseup', () => {
        if (mouseDownOnSlider) {
            mouseDownOnSlider = false;
            audioElement.currentTime = seekSlider.value;
            if (!audioElement.paused) audioElement.play();
        }
    });

    // Volume control
    volumeSlider.addEventListener('input', () => {
        audioElement.volume = volumeSlider.value;
        updateVolumeIcon(volumeSlider.value);
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
        progressCurrent.style.width = '0%';
    });

    // Error handling
    audioElement.addEventListener('error', (e) => {
        console.error('Audio error:', e);
        alert('Error playing track. Please try again.');
        playPauseBtn.innerHTML = '<i class="fas fa-play"></i>';
    });

    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        if (e.target.tagName === 'INPUT') return;
        
        switch(e.code) {
            case 'Space':
                e.preventDefault();
                togglePlay();
                break;
            case 'ArrowLeft':
                e.preventDefault();
                audioElement.currentTime = Math.max(0, audioElement.currentTime - 5);
                break;
            case 'ArrowRight':
                e.preventDefault();
                audioElement.currentTime = Math.min(audioElement.duration, audioElement.currentTime + 5);
                break;
            case 'ArrowUp':
                e.preventDefault();
                audioElement.volume = Math.min(1, audioElement.volume + 0.1);
                volumeSlider.value = audioElement.volume;
                updateVolumeIcon(audioElement.volume);
                break;
            case 'ArrowDown':
                e.preventDefault();
                audioElement.volume = Math.max(0, audioElement.volume - 0.1);
                volumeSlider.value = audioElement.volume;
                updateVolumeIcon(audioElement.volume);
                break;
        }
    });
}

function updateVolumeIcon(volume) {
    const volumeBtn = document.getElementById('volume-btn');
    if (volume === 0) {
        volumeBtn.innerHTML = '<i class="fas fa-volume-mute"></i>';
    } else if (volume < 0.5) {
        volumeBtn.innerHTML = '<i class="fas fa-volume-down"></i>';
    } else {
        volumeBtn.innerHTML = '<i class="fas fa-volume-up"></i>';
    }
}

function toggleMute() {
    const audioPlayer = document.getElementById('audio-player');
    const volumeSlider = document.getElementById('volume-slider');
    
    if (audioPlayer.volume > 0) {
        audioPlayer.dataset.lastVolume = audioPlayer.volume;
        audioPlayer.volume = 0;
        volumeSlider.value = 0;
    } else {
        audioPlayer.volume = audioPlayer.dataset.lastVolume || 1;
        volumeSlider.value = audioPlayer.volume;
    }
    updateVolumeIcon(audioPlayer.volume);
}




async function playTrack(fileId, title) {
    try {
        const playerContainer = document.getElementById('player-container');
        const audioPlayer = document.getElementById('audio-player');
        const nowPlaying = document.getElementById('now-playing');
        const playPauseBtn = document.getElementById('play-pause');
        const progressCurrent = document.getElementById('progress-current');
        const progressBuffer = document.getElementById('progress-buffer');

        // Reset state and UI
        if (currentAudio && !currentAudio.paused) {
            currentAudio.pause();
            currentAudio.currentTime = 0;
        }

        progressCurrent.style.width = '0%';
        progressBuffer.style.width = '0%';
        playPauseBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';

        // Show player and update title
        playerContainer.classList.remove('hidden');
        nowPlaying.textContent = title;

        // Set up new audio source with cache-busting
        const timestamp = new Date().getTime();
        const streamUrl = `${API_URL}/stream/${fileId}?t=${timestamp}`;
        
        // Reset audio player state
        audioPlayer.removeAttribute('src');
        audioPlayer.load();
        
        // Set new source
        audioPlayer.src = streamUrl;
        
        // Initialize player controls
        initializeAudioPlayer(audioPlayer);
        currentAudio = audioPlayer;

        // Handle playback
        try {
            await audioPlayer.play();
            playPauseBtn.innerHTML = '<i class="fas fa-pause"></i>';
        } catch (playError) {
            // Handle user interaction required error
            if (playError.name === 'NotAllowedError') {
                playPauseBtn.innerHTML = '<i class="fas fa-play"></i>';
                console.log('Playback requires user interaction');
            } else {
                throw playError; // Re-throw other play errors
            }
        }

        // Add specific error handler for this track
        audioPlayer.onerror = (e) => {
            console.error('Audio error:', {
                error: audioPlayer.error,
                code: audioPlayer.error.code,
                message: audioPlayer.error.message,
                details: e
            });
            
            playPauseBtn.innerHTML = '<i class="fas fa-play"></i>';
            
            // Show user-friendly error message based on error code
            let errorMessage = 'Error playing track. ';
            switch (audioPlayer.error.code) {
                case 1:
                    errorMessage += 'The audio file cannot be fetched.';
                    break;
                case 2:
                    errorMessage += 'Network error occurred during playback.';
                    break;
                case 3:
                    errorMessage += 'Audio decoding failed.';
                    break;
                case 4:
                    errorMessage += 'Audio format not supported.';
                    break;
                default:
                    errorMessage += 'Please try again.';
            }
            alert(errorMessage);
        };

    } catch (error) {
        console.error('Error in playTrack:', error);
        playPauseBtn.innerHTML = '<i class="fas fa-play"></i>';
        alert('Error initializing track playback. Please try again.');
    }
}

// Helper function to check if audio can be played
function canPlayAudio(audio) {
    return audio.readyState >= 2;
}

// Update togglePlay to include better error handling
function togglePlay() {
    const audioPlayer = document.getElementById('audio-player');
    const playPauseBtn = document.getElementById('play-pause');
    
    if (!audioPlayer.src) {
        console.log('No audio source set');
        return;
    }
    
    if (audioPlayer.paused) {
        playPauseBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
        
        const playPromise = audioPlayer.play();
        if (playPromise !== undefined) {
            playPromise
                .then(() => {
                    playPauseBtn.innerHTML = '<i class="fas fa-pause"></i>';
                })
                .catch(error => {
                    console.error('Playback error:', error);
                    playPauseBtn.innerHTML = '<i class="fas fa-play"></i>';
                    if (error.name !== 'NotAllowedError') {
                        alert('Playback error. Please try again.');
                    }
                });
        }
    } else {
        audioPlayer.pause();
        playPauseBtn.innerHTML = '<i class="fas fa-play"></i>';
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
