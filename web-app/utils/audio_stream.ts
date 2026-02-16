export class AudioStreamer {
    private mediaStream: MediaStream | null = null;
    private audioContext: AudioContext | null = null;
    private processor: ScriptProcessorNode | null = null;
    private source: MediaStreamAudioSourceNode | null = null;
    private websocket: WebSocket | null = null;
    private isRecording = false;

    constructor(private wsUrl: string, private onMessage: (data: any) => void) { }

    async start(useSystemAudio: boolean = false) {
        if (this.isRecording) return;

        try {
            this.websocket = new WebSocket(this.wsUrl);
            this.websocket.binaryType = 'arraybuffer';

            this.websocket.onopen = () => {
                console.log("WebSocket connected");
                this.startAudioCapture(useSystemAudio);
            };

            this.websocket.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.onMessage(data);
            };

            this.websocket.onerror = (error) => {
                console.error("WebSocket error:", error);
            };

            this.websocket.onclose = () => {
                console.log("WebSocket disconnected");
                this.stop();
            };
        } catch (error) {
            console.error("Error starting stream:", error);
        }
    }

    private async startAudioCapture(useSystemAudio: boolean) {
        try {
            if (useSystemAudio) {
                // Capture system audio (screen share with audio)
                this.mediaStream = await navigator.mediaDevices.getDisplayMedia({
                    video: true, // Video is required for getDisplayMedia, we'll ignore it
                    audio: {
                        echoCancellation: false,
                        noiseSuppression: false,
                        autoGainControl: false,
                    }
                });
            } else {
                // Capture microphone
                this.mediaStream = await navigator.mediaDevices.getUserMedia({
                    audio: {
                        echoCancellation: true,
                        noiseSuppression: true,
                        sampleRate: 16000,
                    }
                });
            }

            this.audioContext = new AudioContext({ sampleRate: 16000 });
            this.source = this.audioContext.createMediaStreamSource(this.mediaStream);

            // Use ScriptProcessor for raw data access (Action: consider AudioWorklet for prod)
            this.processor = this.audioContext.createScriptProcessor(4096, 1, 1);

            this.processor.onaudioprocess = (e) => {
                if (!this.websocket || this.websocket.readyState !== WebSocket.OPEN) return;

                const inputData = e.inputBuffer.getChannelData(0);
                // Convert float32 to int16
                const pcmData = new Int16Array(inputData.length);
                for (let i = 0; i < inputData.length; i++) {
                    pcmData[i] = Math.max(-1, Math.min(1, inputData[i])) * 0x7FFF; // 32767
                }

                this.websocket.send(pcmData.buffer);
            };

            this.source.connect(this.processor);
            this.processor.connect(this.audioContext.destination);
            this.isRecording = true;

        } catch (error) {
            console.error("Error capturing audio:", error);
            this.stop();
        }
    }

    stop() {
        if (!this.isRecording) return;

        if (this.websocket) {
            this.websocket.close();
            this.websocket = null;
        }

        if (this.mediaStream) {
            this.mediaStream.getTracks().forEach(track => track.stop());
            this.mediaStream = null;
        }

        if (this.processor) {
            this.processor.disconnect();
            this.processor = null;
        }

        if (this.source) {
            this.source.disconnect();
            this.source = null;
        }

        if (this.audioContext) {
            this.audioContext.close();
            this.audioContext = null;
        }

        this.isRecording = false;
    }

    sendConfig(sourceLang: string, targetLang: string) {
        if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
            this.websocket.send(JSON.stringify({
                text: JSON.stringify({
                    type: "config",
                    source_lang: sourceLang,
                    target_lang: targetLang
                })
            }));
        }
    }
}
