'use client';

import { createContext, useCallback, useContext, useEffect, useRef } from 'react';
import type { Finding } from './api';

type ScanEvent =
  | { type: 'scan_progress'; scan_id: number | string; progress: number }
  | { type: 'finding'; scan_id: number | string; finding: Finding }
  | { type: 'scan_complete'; scan_id: number | string };

type Listener = (message: ScanEvent) => void;
interface SocketContext { subscribe: (scanId: string, listener: Listener) => () => void }
interface Channel { listeners: Set<Listener>; active: boolean; socket?: WebSocket; reconnect?: ReturnType<typeof setTimeout> }

const Context = createContext<SocketContext | null>(null);

function closeChannel(channel: Channel) {
  channel.active = false;
  if (channel.reconnect) clearTimeout(channel.reconnect);
  channel.socket?.close();
}

export function WebSocketProvider({ children }: { children: React.ReactNode }) {
  const channels = useRef(new Map<string, Channel>());
  const subscribe = useCallback((scanId: string, listener: Listener) => {
    let channel = channels.current.get(scanId);
    if (!channel) {
      channel = { listeners: new Set(), active: true };
      channels.current.set(scanId, channel);
      const connection = channel;
      const base = process.env.NEXT_PUBLIC_WS_URL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const url = `${base.replace(/^http/, 'ws').replace(/\/$/, '')}/ws/scan/${encodeURIComponent(scanId)}`;
      const connect = () => {
        if (!connection.active) return;
        const socket = new WebSocket(url);
        connection.socket = socket;
        socket.onmessage = (event) => {
          try {
            const message = JSON.parse(event.data) as ScanEvent;
            if (String(message.scan_id) !== scanId) return;
            connection.listeners.forEach((callback) => callback(message));
          } catch {
            return;
          }
        };
        socket.onclose = () => {
          if (connection.active) connection.reconnect = setTimeout(connect, 3000);
        };
        socket.onerror = () => socket.close();
      };
      connect();
    }
    const current = channel;
    current.listeners.add(listener);
    return () => {
      current.listeners.delete(listener);
      if (!current.listeners.size) {
        closeChannel(current);
        channels.current.delete(scanId);
      }
    };
  }, []);

  useEffect(() => {
    const connections = channels.current;
    return () => {
      connections.forEach(closeChannel);
      connections.clear();
    };
  }, []);

  return <Context.Provider value={{ subscribe }}>{children}</Context.Provider>;
}

export function useWebSocket() {
  const context = useContext(Context);
  if (!context) throw new Error('WebSocket provider is required');
  return context;
}
