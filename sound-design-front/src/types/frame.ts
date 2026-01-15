export interface FrameMetadata {
  senderId: string;
  timestamp: number;
}

export interface Frame {
  metadata: FrameMetadata;
  action: string; 
  value: string | number | boolean | null;
}

export interface LogFrame extends Frame {
  receivedAt: number;
}
