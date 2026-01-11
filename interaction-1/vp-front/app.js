/**
 * Video Player with WebSocket Chapter Control
 * 
 * Features:
 * - Full-page video player
 * - Sidebar with chapters
 * - WebSocket integration for remote chapter control
 * - Auto-repeat current chapter until next chapter is called
 * - Fullscreen support
 */

class VideoPlayer {
    constructor() {
        this.video = document.getElementById('video');
        this.sidebar = document.getElementById('sidebar');
        this.chaptersList = document.getElementById('chaptersList');
        this.fullscreenBtn = document.getElementById('fullscreenBtn');
        this.toggleSidebarBtn = document.getElementById('toggleSidebarBtn');

        // Chapter management
        this.chapters = [];
        this.currentChapterIndex = -1;
        this.currentChapterSlug = null;
        this.repeatTimeoutId = null;

        // WebSocket
        this.ws = null;
        this.wsUrl = null;

        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadChaptersConfig();
    }

    setupEventListeners() {
        // Fullscreen button
        this.fullscreenBtn.addEventListener('click', () => {
            this.toggleFullscreen();
        });

        // Sidebar toggle
        this.toggleSidebarBtn.addEventListener('click', () => {
            this.sidebar.classList.toggle('active');
        });

        // Video events
        this.video.addEventListener('timeupdate', () => {
            this.handleVideoTimeUpdate();
        });

        this.video.addEventListener('play', () => {
            this.handleVideoPlay();
        });

        this.video.addEventListener('pause', () => {
            this.clearRepeatTimeout();
        });
    }

    connectWebSocket() {
        try {
            this.ws = new WebSocket(this.wsUrl);

            this.ws.onopen = () => {
                console.log('WebSocket connected');
                this.sendNewConnectionMessage();
            };

            this.ws.onmessage = (event) => {
                this.handleWebSocketMessage(event.data);
            };

            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
            };

            this.ws.onclose = () => {
                console.log('WebSocket disconnected');
                // Attempt to reconnect after 3 seconds
                setTimeout(() => this.connectWebSocket(), 3000);
            };
        } catch (error) {
            console.error('Failed to connect WebSocket:', error);
            setTimeout(() => this.connectWebSocket(), 3000);
        }
    }

    handleWebSocketMessage(data) {
        try {
            const message = JSON.parse(data);
            if (message.action && message.value === null) {
                const slug = message.action;
                this.switchToChapterBySlug(slug);
            }
        } catch (error) {
            console.error('Failed to parse WebSocket message:', error);
        }
    }

    sendNewConnectionMessage() {
        const message = {
            metadata: {
                senderId: "UI-010101",
                timestamp: Date.now()
            },
            action: "00-new-connection",
            value: null
        };
        this.ws.send(JSON.stringify(message));
    }

    async loadChaptersConfig() {
        try {
            const response = await fetch('config.json');
            const config = await response.json();

            this.chapters = config.chapters || [];
            this.video.src = config.videoSource || '';
            
            // Initialize WebSocket after loading config
            this.wsUrl = config.websocketUrl || await this.getDefaultWebSocketUrl();
            this.connectWebSocket();

            this.renderChapters();

            // Auto-play first chapter after video is ready
            if (this.chapters.length > 0) {
                const playFirstChapter = () => {
                    this.switchToChapter(0);
                    this.video.removeEventListener('loadedmetadata', playFirstChapter);
                };
                this.video.addEventListener('loadedmetadata', playFirstChapter);
            }
        } catch (error) {
            console.error('Failed to load config:', error);
        }
    }

    getDefaultWebSocketUrl() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.host;
        return `${protocol}//${host}/ws`;
    }

    renderChapters() {
        this.chaptersList.innerHTML = '';

        this.chapters.forEach((chapter, index) => {
            const button = document.createElement('button');
            button.className = 'chapter-btn';
            button.textContent = chapter.title;
            button.dataset.index = index;
            button.dataset.slug = chapter.slug;

            button.addEventListener('click', () => {
                this.switchToChapter(index);
            });

            this.chaptersList.appendChild(button);
        });
    }

    switchToChapter(index) {
        if (index < 0 || index >= this.chapters.length) {
            return;
        }

        const chapter = this.chapters[index];
        this.currentChapterIndex = index;
        this.currentChapterSlug = chapter.slug;

        // Set video time
        this.video.currentTime = chapter.startTime;

        // Update active button
        this.updateActiveChapter();

        // Play video
        if (this.video.paused) {
            this.video.play();
        }
    }

    switchToChapterBySlug(slug) {
        const index = this.chapters.findIndex(ch => ch.slug === slug);
        if (index !== -1) {
            this.switchToChapter(index);
        }
    }

    updateActiveChapter() {
        const buttons = this.chaptersList.querySelectorAll('.chapter-btn');
        buttons.forEach((btn, index) => {
            btn.classList.toggle('active', index === this.currentChapterIndex);
        });
    }

    handleVideoPlay() {
        // Video looping is handled in handleVideoTimeUpdate
    }

    handleVideoTimeUpdate() {
        if (this.currentChapterIndex === -1) {
            return;
        }

        const currentChapter = this.chapters[this.currentChapterIndex];
        const nextChapter = this.chapters[this.currentChapterIndex + 1];
        const chapterEndTime = nextChapter ? nextChapter.startTime : currentChapter.endTime;

        // Prevent video from going past chapter boundary
        if (this.video.currentTime >= chapterEndTime) {
            this.video.currentTime = currentChapter.startTime;
        }
    }

    setupRepeat() {
        // Video looping is handled in handleVideoTimeUpdate
    }

    clearRepeatTimeout() {
        if (this.repeatTimeoutId) {
            clearTimeout(this.repeatTimeoutId);
            this.repeatTimeoutId = null;
        }
    }

    toggleFullscreen() {
        if (!document.fullscreenElement) {
            this.video.requestFullscreen().catch(err => {
                console.error(`Error attempting to enable fullscreen: ${err.message}`);
            });
        } else {
            document.exitFullscreen().catch(err => {
                console.error(`Error attempting to exit fullscreen: ${err.message}`);
            });
        }
    }
}

// Initialize player when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new VideoPlayer();
});
