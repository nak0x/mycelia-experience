import { useState, useRef, useEffect } from 'react';
import { useSocketAudio } from './hooks/useSocketAudio';
import { useSendAction } from './hooks/useSendAction';
import { WebSocketProvider } from './contexts/WebSocketContext';
import type { Frame } from './types/frame';
import type { Client } from './types/client';

// Components
import { VideoBackground } from './components/VideoBackground';
import { Header } from './components/Header';
import { LatestFrame } from './components/LatestFrame';
import { Footer } from './components/Footer';
import { StartOverlay } from './components/StartOverlay';
import { ClientsDrawer } from './components/drawers/ClientsDrawer';
import { CommandsDrawer } from './components/drawers/CommandsDrawer';
import { LogsDrawer } from './components/drawers/LogsDrawer';

function AppContent() {
  const { isConnected, lastFrame, logs, volume, setVolume, isMuted, setIsMuted } = useSocketAudio();
  const [hasInteracted, setHasInteracted] = useState(false);
  const [isLogsOpen, setIsLogsOpen] = useState(false);
  const [isClientsOpen, setIsClientsOpen] = useState(false);
  const [isCommandsOpen, setIsCommandsOpen] = useState(false);
  const [isUIHidden, setIsUIHidden] = useState(false);
  const [selectedAction, setSelectedAction] = useState<string | null>(null);
  const [isVideoDone, setIsVideoDone] = useState(false);  
  const videoRef = useRef<HTMLVideoElement>(null);
  const playTimeoutRef = useRef<number | null>(null);
  const lastProcessedFrameRef = useRef<Frame | null>(null);
  const growCountRef = useRef(0);
  const { sendAction } = useSendAction();

  const [clients, setClients] = useState<Client[]>([]);
  
  let videoPlayTime = 2000/60;

  const handleStart = () => {
    setHasInteracted(true);
    if (videoRef.current) {
        videoRef.current.pause();
        videoRef.current.currentTime = 0;
    }
  };

  useEffect(() => {
    if (!lastFrame || lastFrame === lastProcessedFrameRef.current) return;
    lastProcessedFrameRef.current = lastFrame;

    if (lastFrame.action === '03-grow-mycelium') {
        if (videoRef.current) {
            if (isVideoDone) return;
            
            growCountRef.current += 1;
            
            if (growCountRef.current === 8) {
                const stepTime = videoPlayTime / 1000;
                videoRef.current.currentTime += stepTime * 12;
            }

            if (videoRef.current.ended) {
                setIsVideoDone(true);
                sendAction('03-nutrient-start-animation');
                return;
            }

            if (playTimeoutRef.current) {
                clearTimeout(playTimeoutRef.current);
            }

            videoRef.current.play().catch(e => console.error("Video play failed", e));
            
            playTimeoutRef.current = setTimeout(() => {
                if (videoRef.current) {
                    videoRef.current.pause();
                }
            }, videoPlayTime);
        }
    } else if (lastFrame.action === '03-reset') {
        if (videoRef.current) {
            videoRef.current.pause();
            videoRef.current.currentTime = 0;
        }
        growCountRef.current = 0;
        setIsVideoDone(false);
        if (playTimeoutRef.current) {
            clearTimeout(playTimeoutRef.current);
            playTimeoutRef.current = null;
        }
    } else if (lastFrame.action === '03-shrink-mycelium') {
        if (videoRef.current) {
            // Ensure we are paused so we don't fight with native playback
            videoRef.current.pause();

            // Clear any forward playback timeout if it exists
            if (playTimeoutRef.current) {
                clearTimeout(playTimeoutRef.current);
                playTimeoutRef.current = null;
            }

            // Step backward
            const stepTime = videoPlayTime / 1000; // convert ms to seconds
            videoRef.current.currentTime = Math.max(0, videoRef.current.currentTime - stepTime);
            
            // Allow growing again if we moved back
            setIsVideoDone(false);
        }
    } else if (lastFrame.action === 'connected-clients') {
        if (Array.isArray(lastFrame.value)) {
            setClients(lastFrame.value as unknown as Client[]);
        }
    } else if (lastFrame.action === '00-new-client') {
        if (lastFrame.value) {
            setClients(prev => {
                const exists = prev.find(c => c.clientId === lastFrame.value);
                if (exists) {
                    return prev.map(c => c.clientId === lastFrame.value ? { ...c, isConnected: true } : c);
                } else {
                    return [...prev, { clientId: lastFrame.value, isConnected: true }];
                }
            });
        }
    } else if (lastFrame.action === '00-lost-client') {
        if (lastFrame.value) {
            setClients(prev => prev.map(c => c.clientId === lastFrame.value ? { ...c, isConnected: false } : c));
        }
    }
    
    return () => {
        if (playTimeoutRef.current) {
            clearTimeout(playTimeoutRef.current);
        }
    };
  }, [lastFrame, sendAction, isVideoDone]);

  const handleActionClick = (action: string) => {
    setSelectedAction(action);
  };

  const handleValueSend = (value: boolean | null) => {
    if (selectedAction) {
        sendAction(selectedAction, value);
    }
  };

  return (
    <div className="relative w-screen h-svh overflow-hidden bg-black font-mono text-white selection:bg-white selection:text-black">
      
      <VideoBackground 
        videoRef={videoRef}
        isUIHidden={isUIHidden}
        hasInteracted={hasInteracted}
        onInteract={() => setIsUIHidden(false)}
      />

      {!isUIHidden && (
        <div className="relative z-10 w-full h-full flex flex-col justify-between p-6 animate-in fade-in duration-300">
            
            <Header 
                isConnected={isConnected}
                isMuted={isMuted}
                volume={volume}
                setIsMuted={setIsMuted}
                setVolume={setVolume}
                isClientsOpen={isClientsOpen}
                setIsClientsOpen={setIsClientsOpen}
            />

            <main className="flex-1 flex items-start justify-center p-4 pt-20">
                <LatestFrame lastFrame={lastFrame} />
            </main>

            <Footer 
                isCommandsOpen={isCommandsOpen}
                setIsCommandsOpen={setIsCommandsOpen}
                isLogsOpen={isLogsOpen}
                setIsLogsOpen={setIsLogsOpen}
                setIsUIHidden={setIsUIHidden}
            />
        </div>
      )}

      <ClientsDrawer 
        isOpen={isClientsOpen}
        setIsClientsOpen={setIsClientsOpen}
        isUIHidden={isUIHidden}
        clients={clients}
        sendAction={sendAction}
      />

      <CommandsDrawer 
        isOpen={isCommandsOpen}
        setIsCommandsOpen={setIsCommandsOpen}
        isUIHidden={isUIHidden}
        selectedAction={selectedAction}
        setSelectedAction={setSelectedAction}
        handleActionClick={handleActionClick}
        handleValueSend={handleValueSend}
      />

      <LogsDrawer 
        isOpen={isLogsOpen}
        setIsLogsOpen={setIsLogsOpen}
        isUIHidden={isUIHidden}
        logs={logs}
      />

      {!hasInteracted && (
        <StartOverlay handleStart={handleStart} />
      )}
    </div>
  );
}

function App() {
    return (
        <WebSocketProvider url="ws://192.168.10.163:8000/ws">
            <AppContent />
        </WebSocketProvider>
    );
}

export default App;