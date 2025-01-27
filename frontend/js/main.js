const API_URL = 'https://flacmusicstore-production.up.railway.app';
let audioPlayer;
let currentAudio = null;
let seeking = false;
const DB_NAME = 'musicCache';
const STORE_NAME = 'tracks';
let db;



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


// Initialize IndexedDB
const initDB = () => {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open(DB_NAME, 1);
        
        request.onerror = () => reject(request.error);
        request.onsuccess = () => {
            db = request.result;
            resolve(db);
        };
        
        request.onupgradeneeded = (event) => {
            const db = event.target.result;
            if (!db.objectStoreNames.contains(STORE_NAME)) {
                db.createObjectStore(STORE_NAME, { keyPath: 'fileId' });
            }
        };
    });
};

class DirectStreamPlayer {
    constructor(audioElement) {
        this.audio = audioElement;
        this.fileId = null;
        this.driveUrl = null;
        this.confirmToken = null;
        this.dbInitialized = false;
        
        // Initialize IndexedDB
        initDB()
            .then(() => {
                this.dbInitialized = true;
                console.log('IndexedDB initialized successfully');
            })
            .catch(error => {
                console.error('Error initializing IndexedDB:', error);
            });
    }
    
    async getConfirmToken(fileId) {
        try {
            const driveUrl = `${API_URL}/api/stream/${fileId}`;
            const response = await fetch(driveUrl);
            if (!response.ok) throw new Error('Failed to get confirmation token');
            const text = await response.text();
            
            const match = text.match(/confirm=([0-9A-Za-z]+)/);
            return match ? match[1] : null;
        } catch (error) {
            console.error('Error getting confirm token:', error);
            throw error;
        }
    }
    
    async getDriveDirectUrl(fileId) {
        try {
            const token = await this.getConfirmToken(fileId);
            return token ? 
                `${API_URL}/api/stream/${fileId}?confirm=${token}` :
                `${API_URL}/api/stream/${fileId}`;
        } catch (error) {
            console.error('Error getting drive direct URL:', error);
            throw error;
        }
    }
    
    async checkCache(fileId) {
        if (!this.dbInitialized || !db) return null;
        
        return new Promise((resolve) => {
            try {
                const transaction = db.transaction([STORE_NAME], 'readonly');
                const store = transaction.objectStore(STORE_NAME);
                const request = store.get(fileId);
                
                request.onsuccess = () => resolve(request.result);
                request.onerror = () => resolve(null);
            } catch (error) {
                console.error('Error checking cache:', error);
                resolve(null);
            }
        });
    }
    
    async cacheTrack(fileId, blob) {
        if (!this.dbInitialized || !db) return;
        
        return new Promise((resolve, reject) => {
            try {
                const transaction = db.transaction([STORE_NAME], 'readwrite');
                const store = transaction.objectStore(STORE_NAME);
                const request = store.put({
                    fileId,
                    blob,
                    timestamp: Date.now()
                });
                
                request.onsuccess = () => resolve();
                request.onerror = () => reject(request.error);
            } catch (error) {
                console.error('Error caching track:', error);
                reject(error);
            }
        });
    }
    
    async loadTrack(fileId, title) {
        try {
            // Check local cache first
            const cached = await this.checkCache(fileId);
            if (cached) {
                console.log('Playing from cache');
                this.audio.src = URL.createObjectURL(cached.blob);
                await this.audio.play();
                return;
            }
            
            // Get streaming URL
            const streamUrl = `${API_URL}/api/stream/${fileId}`;
            const response = await fetch(streamUrl);
            if (!response.ok) throw new Error('Failed to stream track');
            
            const blob = await response.blob();
            
            // Cache the track if DB is initialized
            if (this.dbInitialized) {
                await this.cacheTrack(fileId, blob);
            }
            
            // Play the track
            this.audio.src = URL.createObjectURL(blob);
            await this.audio.play();
            
        } catch (error) {
            console.error('Error loading track:', error);
            throw error;
        }
    }
    
    async cleanCache(maxAge = 7 * 24 * 60 * 60 * 1000) {
        if (!this.dbInitialized || !db) return;
        
        try {
            const transaction = db.transaction([STORE_NAME], 'readwrite');
            const store = transaction.objectStore(STORE_NAME);
            const request = store.openCursor();
            
            request.onsuccess = (event) => {
                const cursor = event.target.result;
                if (cursor) {
                    if (Date.now() - cursor.value.timestamp > maxAge) {
                        store.delete(cursor.key);
                    }
                    cursor.continue();
                }
            };
        } catch (error) {
            console.error('Error cleaning cache:', error);
        }
    }
}

// Initialize the player
let directPlayer;
document.addEventListener('DOMContentLoaded', async () => {
    const audioElement = document.getElementById('audio-player');
    if (!audioElement) {
        console.error('Audio element not found');
        return;
    }
    
    directPlayer = new DirectStreamPlayer(audioElement);
    initializeAudioPlayer(audioElement);
    
    // Clean old cache entries
    try {
        await directPlayer.cleanCache();
    } catch (error) {
        console.error('Error cleaning cache:', error);
    }
});






// Update playTrack function
async function playTrack(fileId, title) {
    try {
        const playerContainer = document.getElementById('player-container');
        const nowPlaying = document.getElementById('now-playing');
        const playPauseBtn = document.getElementById('play-pause');
        
        if (!playerContainer || !nowPlaying || !playPauseBtn) {
            console.error('Required elements not found');
            return;
        }
        
        playerContainer.classList.remove('hidden');
        nowPlaying.textContent = title;
        playPauseBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
        
        await directPlayer.loadTrack(fileId, title);
        playPauseBtn.innerHTML = '<i class="fas fa-pause"></i>';
        
    } catch (error) {
        console.error('Error playing track:', error);
        alert('Error playing track. Please try again.');
        const playPauseBtn = document.getElementById('play-pause');
        if (playPauseBtn) {
            playPauseBtn.innerHTML = '<i class="fas fa-play"></i>';
        }
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
