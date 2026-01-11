# VP Front - Video Player with Chapters

A simple, full-page video player with WebSocket integration for chapter control.

## Features

- **Full-page video display** with fullscreen support
- **Chapter sidebar** with easy chapter navigation
- **WebSocket integration** for remote chapter control
- **Auto-repeat chapters** until next chapter is called
- **Responsive design** that works on mobile and desktop

## Configuration

Edit `config.json` to define your video, chapters, and WebSocket server:

```json
{
  "videoSource": "path/to/your/video.mp4",
  "websocketUrl": "ws://custom-server.com/ws",
  "chapters": [
    {
      "slug": "01-chapt-night",
      "title": "Chapter 1 - Night",
      "startTime": 0,
      "endTime": 30
    },
    {
      "slug": "02-chapt-dawn",
      "title": "Chapter 2 - Dawn",
      "startTime": 30,
      "endTime": 60
    }
  ]
}
```

### Configuration Notes

- **videoSource**: Path to your video file
- **websocketUrl**: Optional custom WebSocket server URL (defaults to `ws://current-host/ws`)
- **chapters**: Array of chapter definitions
  - **slug**: Unique identifier for the chapter (e.g., `01-chapt-night`)
  - **title**: Display name for the chapter
  - **startTime**: Start time in **seconds**
  - **endTime**: End time in **seconds** (when the next chapter should start)

## WebSocket Control

The frontend connects to a WebSocket server and listens for chapter commands:

```json
{
  "action": "01-chapt-night",
  "value": null
}
```

When a chapter slug is received, the video automatically switches to that chapter's start time.

## Usage

1. Update `config.json` with your video source, chapters, and optionally a custom WebSocket server URL
2. Serve the files over HTTP/HTTPS with WebSocket support
3. The player will automatically:
   - Load the video and chapters
   - Connect to the WebSocket server
   - Handle chapter navigation both via UI and WebSocket messages
   - Repeat the current chapter until the next one is triggered

## Controls

- **Fullscreen button** (top-right): Toggle fullscreen mode
- **Chapters button** (top-right): Toggle the chapters sidebar
- **Chapter buttons** (sidebar): Click to jump to any chapter
- **WebSocket messages**: Receive remote chapter control commands

## Chapter Repeat Behavior

When a chapter is playing:
- The video will loop at the chapter boundary (until the next chapter's start time)
- If no next chapter exists, it repeats at the video duration
- When a new chapter is called (via UI or WebSocket), the repeat is cancelled
- The repeat continues until the next chapter is triggered
