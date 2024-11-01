import { Data } from '../types/data';

export const createWebSocket = (onMessage: (data: Data) => void, onOpen?: () => void) => {
  if (typeof window === 'undefined') return null;

  const { protocol, pathname, host } = window.location;
  const wsHost = host.includes('localhost') ? 'localhost:8000' : host;
  const ws_uri = `${protocol === 'https:' ? 'wss:' : 'ws:'}//${wsHost}${pathname}ws`;

  const socket = new WebSocket(ws_uri);
  
  socket.onmessage = (event) => {
    const data = JSON.parse(event.data) as Data;
    onMessage(data);
  };

  if (onOpen) {
    socket.onopen = onOpen;
  }

  return socket;
}; 