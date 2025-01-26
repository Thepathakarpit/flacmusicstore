const API_URL = 'https://flacmusicstore-production.up.railway.app';
let audioPlayer;
let isPlaying = false;

async function searchTracks(query) {
    try {
        const response = await fetch(`${API_URL}/api/search?q=${encodeURIComponent(query)}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error searching tracks:', error);
        throw error;
    }
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
        
        // Set audio source with cache-busting parameter
        const timestamp = new Date().getTime();
        audioPlayer.src = `${API_URL}/stream/${fileId}?t=${timestamp}`;
        
        audioPlayer.addEventListener('loadedmetadata', () => {
            seekSlider.max = Math.floor(audioPlayer.duration);
            document.getElementById('duration').textContent = formatTime(audioPlayer.duration);
        });
        
        audioPlayer.addEventListener('timeupdate', () => {
            seekSlider.value = Math.floor(audioPlayer.currentTime);
            document.getElementById('current-time').textContent = formatTime(audioPlayer.currentTime);
            
            // Update play/pause button
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

// Add keyboard shortcuts
document.addEventListener('keydown', (e) => {
    if (e.code === 'Space' && e.target.tagName !== 'INPUT') {
        e.preventDefault();
        togglePlay();
    }
}); 
