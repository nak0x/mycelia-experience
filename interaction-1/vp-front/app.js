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
        this.autoplayModal = document.getElementById('autoplayModal');
        this.playButton = document.getElementById('playButton');

        // Chapter management
        this.chapters = [];
        this.currentChapterIndex = -1;
        this.currentChapterSlug = null;
        this.repeatTimeoutId = null;
        this.chapterPlayCount = {}; // Track how many times each chapter has played
        this.autoPlaySequence = null; // Define auto-play sequence with play counts

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

        // Play button in modal
        this.playButton.addEventListener('click', () => {
            this.hideAutoplayModal();
            this.video.play()
                .then(() => {
                    console.log("Video started playing.");
                })
                .catch(error => {
                    console.error("Error attempting to play video:", error);
                });
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
            console.log('[WebSocket Message Received]', data);
            const message = JSON.parse(data);
            console.log('[WebSocket Parsed]', message);
            if (message.action) {
                const slug = message.action;
                const value = message.value !== undefined ? message.value : 'not specified';
                console.log(`[WebSocket Action] Processing chapter change to: ${slug} (value: ${value})`);
                // Process if value is true, null, undefined, or not specified. Skip only if value is explicitly false.
                if (message.value !== false) {
                    this.switchToChapterBySlug(slug);
                } else {
                    console.log(`[WebSocket Action] Skipped - value is false`);
                }
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
            this.autoPlaySequence = config.autoPlaySequence || null;
            
            // Initialize play count for each chapter
            this.chapters.forEach(chapter => {
                this.chapterPlayCount[chapter.slug] = 0;
            });
            
            // Initialize WebSocket after loading config
            this.wsUrl = config.websocketUrl || await this.getDefaultWebSocketUrl();
            this.connectWebSocket();

            this.renderChapters();

            // Auto-play from the first chapter in autoPlaySequence if defined
            const playFirstChapter = () => {
                if (this.autoPlaySequence && this.autoPlaySequence.length > 0) {
                    const firstSlug = this.autoPlaySequence[0].slug;
                    this.switchToChapterBySlug(firstSlug);
                } else if (this.chapters.length > 0) {
                    this.switchToChapter(0);
                }
                this.video.removeEventListener('loadedmetadata', playFirstChapter);
            };
            this.video.addEventListener('loadedmetadata', playFirstChapter);
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

        // Reset play count for this chapter if it's in the autoPlaySequence
        if (this.autoPlaySequence) {
            const sequenceEntry = this.autoPlaySequence.find(entry => entry.slug === chapter.slug);
            if (sequenceEntry) {
                this.chapterPlayCount[chapter.slug] = 0;
                console.log(`[Reset Play Count] Reset "${chapter.title}" play count to 0`);
            }
        }

        console.log(`[Chapter Changed] Switching to chapter ${index + 1}: "${chapter.title}" (${chapter.slug})`);
        console.log(`  - Start time: ${chapter.startTime}s | End time: ${chapter.endTime}s`);

        // Set video time
        this.video.currentTime = chapter.startTime;

        // Update active button
        this.updateActiveChapter();

        // Play video
        if (this.video.paused) {
            this.video.play()
                .then(() => {
                    console.log("Video started playing.");
                })
                .catch(error => {
                    // Autoplay was prevented
                    if (error.name === "NotAllowedError") {
                        console.warn("Autoplay was prevented. User interaction required.", error);
                        this.showAutoplayModal();
                    } else {
                        console.error("Error attempting to play video:", error);
                    }
                });
        }
    }

    switchToChapterBySlug(slug) {
        const index = this.chapters.findIndex(ch => ch.slug === slug);
        if (index !== -1) {
            console.log(`[WebSocket] Chapter requested via WebSocket: ${slug}`);
            this.switchToChapter(index);
        } else {
            console.warn(`[WebSocket] Chapter not found: ${slug}`);
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
            // Check if we should auto-advance to next chapter
            if (this.autoPlaySequence) {
                const currentSlug = currentChapter.slug;
                const sequenceEntry = this.autoPlaySequence.find(entry => entry.slug === currentSlug);
                
                if (sequenceEntry) {
                    // If playCount is -1, loop indefinitely
                    if (sequenceEntry.playCount === -1) {
                        console.log(`[Auto-Loop] Looping chapter "${currentChapter.title}" (infinite loop)`);
                        this.video.currentTime = currentChapter.startTime;
                    }
                    // If playCount is 1, play once without looping - advance immediately
                    else if (sequenceEntry.playCount === 1) {
                        if (nextChapter) {
                            console.log(`[Auto-Advance] Chapter "${currentChapter.title}" finished. Auto-advancing to next chapter...`);
                            this.switchToChapter(this.currentChapterIndex + 1);
                        } else {
                            console.log(`[Loop] Looping chapter "${currentChapter.title}" (no next chapter)`);
                            this.video.currentTime = currentChapter.startTime;
                        }
                    }
                    // If playCount > 1, loop until we've looped enough times
                    else if (this.chapterPlayCount[currentSlug] < sequenceEntry.playCount - 1) {
                        this.chapterPlayCount[currentSlug]++;
                        console.log(`[Auto-Loop] Looping chapter "${currentChapter.title}" (${this.chapterPlayCount[currentSlug]}/${sequenceEntry.playCount - 1} loops)`);
                        this.video.currentTime = currentChapter.startTime;
                    }
                    else if (nextChapter) {
                        console.log(`[Auto-Advance] Chapter "${currentChapter.title}" finished. Auto-advancing to next chapter...`);
                        this.switchToChapter(this.currentChapterIndex + 1);
                    } else {
                        console.log(`[Loop] Looping chapter "${currentChapter.title}" (no next chapter)`);
                        this.video.currentTime = currentChapter.startTime;
                    }
                } else {
                    // Chapter not in sequence, just loop
                    console.log(`[Loop] Looping chapter "${currentChapter.title}" (not in sequence)`);
                    this.video.currentTime = currentChapter.startTime;
                }
            } else {
                // Default behavior: loop current chapter
                this.video.currentTime = currentChapter.startTime;
            }
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

    showAutoplayModal() {
        this.autoplayModal.classList.remove('hidden');
    }

    hideAutoplayModal() {
        this.autoplayModal.classList.add('hidden');
    }
}

// Initialize player when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new VideoPlayer();
});
