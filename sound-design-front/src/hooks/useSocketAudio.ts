import { useEffect, useRef, useState } from 'react';
import { Howl, Howler } from 'howler';
import type { Frame } from '../types/frame';
import { useWebSocket } from '../contexts/WebSocketContext';

// On map les sons ici
const SOUNDS: Record<string, string> = {
  'background': '/sounds/background.mp3',
  '01-rain-toggle': '/sounds/01-rain-toggle.mp3',
  '01-shroom-forest-lighten': '/sounds/01-shroom-forest-lighten.mp3',
  '01-wind-toggle': '/sounds/01-wind-toggle.mp3',
  '01-interaction-done': '/sounds/01-interaction-done.mp3',
  '02-rover-toggle': '/sounds/02-rover-toggle.mp3',
  '02-grass-increment': '/sounds/tic.mp3',
  '02-grass-decrement': '/sounds/tic.mp3',
  '02-water-flow-toggle': '/sounds/02-water-flow-toggle.mp3',
  '03-grow-mycelium': '/sounds/tic.mp3',
  '03-shrink-mycelium': '/sounds/tic.mp3',
  '03-grow-shroom': '/sounds/03-grow-shroom.mp3',
  '03-nutrient-start-animation': '/sounds/03-nutrient-start-animation.mp3',
  '03-interaction-done': '/sounds/03-interaction-done.mp3',
  '03-interaction-done-background': '/sounds/03-interaction-done-background.mp3',
  'special-tac': '/sounds/tac.mp3',
  'stop-sound': '',
};

export const useSocketAudio = () => {
  const { isConnected, lastFrame, logs } = useWebSocket();
  const soundInstances = useRef<Record<string, Howl>>({});
  const actionCounters = useRef<Record<string, number>>({});
  
  // 1. Initialisation des sons
  useEffect(() => {
    Object.entries(SOUNDS).forEach(([action, src]) => {
      if (src) {
        soundInstances.current[action] = new Howl({
          src: [src],
          preload: true,
          volume: 1.0,
        });
      }
    });
  }, []);

  // 2. Gestion Playback via lastFrame du contexte
  useEffect(() => {
    if (lastFrame) {
        handleAction(lastFrame);
    }
  }, [lastFrame]);

  // 3. Lancement des sons
  const handleAction = (frame: Frame) => {
    console.log(`Action reçue: ${frame.action}`);

    if (frame.action === 'stop-sound') {
        Howler.stop(); 
        return;
    }

    let playStandardSound = true;

    // Gestion du délai pour 02-rover-toggle après 01-interaction-done
    if (frame.action === '01-interaction-done') {
      console.log('Planification de 02-rover-toggle dans 12 secondes...');
      setTimeout(() => {
        const roverSound = soundInstances.current['02-rover-toggle'];
        if (roverSound) {
          console.log('Lancement différé du son: 02-rover-toggle');
          roverSound.play();
        }
      }, 12000);
    }

    // Gestion du son "tac" tous les 4 coups pour certaines actions
    if (frame.action === '02-grass-increment' || frame.action === '03-grow-shroom') {
      actionCounters.current[frame.action] = (actionCounters.current[frame.action] || 0) + 1;
      
      if (actionCounters.current[frame.action] % 4 === 0) {
        const tacSound = soundInstances.current['special-tac'];
        if (tacSound) {
          console.log(`Lancement du son special: tac (count: ${actionCounters.current[frame.action]})`);
          tacSound.play();
          playStandardSound = false;
        }
      }
    }

    if (playStandardSound) {
      const sound = soundInstances.current[frame.action];
      if (sound) {
        if (frame.value === true || frame.value === null) {
            console.log(`Lancement du son: ${frame.action}`);
            sound.play();
        }
      }
    }
  };

  const [volume, setVolume] = useState(1.0);
  const [isMuted, setIsMuted] = useState(false);

  // 4. Gestion Volume & Mute Global
  useEffect(() => {
    Howler.volume(volume);
  }, [volume]);

  useEffect(() => {
    Howler.mute(isMuted);
  }, [isMuted]);

  return { 
    isConnected, 
    lastFrame, 
    logs,
    volume,
    setVolume,
    isMuted,
    setIsMuted 
  };
};