const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000/api'

export const analyzeVideo = async (
        url: string,
        onProgress: (msg: string, progress: number) => void
    ): Promise<any> => {
        const response = await fetch(`${API_BASE}/downloader/videos/from_url/`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({url, platform: 'youtube'}),
        });

        if (!response.ok || !response.body) throw new Error(response.statusText);

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
            const {done, value} = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, {stream: true});
            const lines = buffer.split('\n');
            buffer = lines.pop() || '';

            for (const line of lines) {
                if (!line.trim()) continue;

                let data
                try {
                    data = JSON.parse(line);
                } catch (e) {
                    console.error("Błąd parsowania JSON z backendu:", e);
                    continue;
                }
                if (data.type === 'progress') {
                    onProgress(data.message, data.progress || 0);
                } else if (data.type === 'complete') {
                    return data.data;
                } else if (data.type === 'error') {
                    throw new Error(data.message);
                }
            }
        }

        throw new Error("Połączenie przerwane przed otrzymaniem wyniku.");
    }
;