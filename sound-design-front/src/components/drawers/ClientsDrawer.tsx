import { useMemo } from 'react';
import type { Client } from '../../types/client';

interface ClientsDrawerProps {
    isOpen: boolean;
    setIsClientsOpen: (open: boolean) => void;
    isUIHidden: boolean;
    clients: Client[];
    sendAction: (action: string) => void;
}

export function ClientsDrawer({ isOpen, setIsClientsOpen, isUIHidden, clients, sendAction }: ClientsDrawerProps) {
    const sortedClients = useMemo(() => {
        return [...clients].sort((a, b) => {
            const extractId = (id: string) => {
                const match = id.match(/\d{6}/);
                return match ? parseInt(match[0]) : 0;
            };

            const idA = extractId(a.clientId);
            const idB = extractId(b.clientId);

            if (idA !== 0 && idB !== 0) {
                return idA - idB;
            }
            
            return a.clientId.localeCompare(b.clientId);
        });
    }, [clients]);

    return (
        <div 
            className={`fixed top-0 right-0 w-[300px] h-full bg-black/90 backdrop-blur-xl border-l border-white/20 transform transition-transform duration-300 ease-in-out z-50 flex flex-col ${
                isOpen && !isUIHidden ? 'translate-x-0' : 'translate-x-full'
            }`}
        >
            <div className="flex justify-between items-center p-4 border-b border-white/10 bg-white/5">
                <div className="flex items-center gap-4">
                    <h2 className="font-bold tracking-widest text-sm">CONNECTED CLIENTS</h2>
                    <button 
                        onClick={() => sendAction('00-get-connected-clients')}
                        className="p-1.5 bg-white/10 hover:bg-white/20 rounded border border-white/20 transition-colors group"
                        title="Refresh"
                    >
                        <svg 
                            xmlns="http://www.w3.org/2000/svg" 
                            width="14" 
                            height="14" 
                            viewBox="0 0 24 24" 
                            fill="none" 
                            stroke="currentColor" 
                            strokeWidth="2" 
                            strokeLinecap="round" 
                            strokeLinejoin="round" 
                            className="opacity-70 group-hover:opacity-100"
                        >
                            <path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8" />
                            <path d="M3 3v5h5" />
                            <path d="M3 12a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16" />
                            <path d="M16 16h5v5" />
                        </svg>
                    </button>
                </div>
                <button onClick={() => setIsClientsOpen(false)} className="text-gray-400 hover:text-white cursor-pointer px-2">
                    CLOSE [X]
                </button>
            </div>
            <div className="flex-1 overflow-y-auto p-4 font-mono">
                {sortedClients.length === 0 ? (
                    <div className="text-gray-600 italic p-4 text-center text-xs">No clients detected</div>
                ) : (
                    <div className="flex flex-col gap-2">
                        {sortedClients.map((client, index) => (
                            <div key={index} className="flex justify-between items-center p-3 border border-white/10 bg-white/5">
                                <span className="text-sm font-bold tracking-wider">{client.clientId}</span>
                                <div className={`w-3 h-3 rounded-full ${client.isConnected ? 'bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.6)]' : 'bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.6)]'}`}></div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}
