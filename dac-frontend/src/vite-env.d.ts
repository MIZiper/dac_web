/// <reference types="svelte" />
/// <reference types="vite/client" />

interface Window {
    mpl: {
        get_websocket_type: () => new (...args: any[]) => WebSocket;
        figure: new (...args: any[]) => {
            _resize_canvas: (w: number, h: number, b: boolean) => void;
            id: number;
        };
    };
}
