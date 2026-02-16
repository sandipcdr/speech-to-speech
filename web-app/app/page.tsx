'use client';

import { useState, useRef } from 'react';
import { Mic, Globe, Play, Square, Monitor } from 'lucide-react';

export default function Home() {
    const [isRecording, setIsRecording] = useState(false);
    const [sourceLang, setSourceLang] = useState('en');
    const [targetLang, setTargetLang] = useState('ja');
    const [transcript, setTranscript] = useState('');
    const [translation, setTranslation] = useState('');
    const [mode, setMode] = useState<'mic' | 'system'>('mic');

    const audioContextRef = useRef<AudioContext | null>(null);
    const mediaStreamRef = useRef<MediaStream | null>(null);
    const processorRef = useRef<ScriptProcessorNode | null>(null);
    const socketRef = useRef<WebSocket | null>(null);

    const startRecording = async () => {
        try {
            // 1. Connect WebSocket
            const ws = new WebSocket('ws://localhost:8001/ws');
            socketRef.current = ws;

            ws.onopen = () => {
                console.log('Connected to backend');
                // Send initial config
                ws.send(JSON.stringify({
                    type: 'config',
                    source_lang: sourceLang,
                    target_lang: targetLang
                }));
            };

            ws.onmessage = async (event) => {
                const data = JSON.parse(event.data);

                if (data.type === 'transcript') {
                    setTranscript(prev => prev + ' ' + data.text);
                } else if (data.type === 'translation') {
                    setTranslation(prev => prev + ' ' + data.text);
                } else if (data.type === 'audio') {
                    // Play audio
                    const audio = new Audio(`data:audio/wav;base64,${data.payload}`);
                    try {
                        await audio.play();
                    } catch (e) {
                        console.error("Autoplay failed:", e);
                    }
                }
            };

            ws.onerror = (error) => console.error('WS Error:', error);

            // 2. Capture Audio
            let stream;
            if (mode === 'system') {
                stream = await navigator.mediaDevices.getDisplayMedia({
                    video: true,
                    audio: {
                        echoCancellation: false,
                        noiseSuppression: false,
                        autoGainControl: false,
                    }
                });
            } else {
                stream = await navigator.mediaDevices.getUserMedia({
                    audio: {
                        echoCancellation: true,
                        noiseSuppression: true,
                        sampleRate: 16000
                    }
                });
            }
            mediaStreamRef.current = stream;

            const audioCtx = new (window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext)({ sampleRate: 16000 });
            audioContextRef.current = audioCtx;

            const source = audioCtx.createMediaStreamSource(stream);
            const processor = audioCtx.createScriptProcessor(4096, 1, 1);
            processorRef.current = processor;

            processor.onaudioprocess = (e) => {
                if (ws.readyState === WebSocket.OPEN) {
                    const inputData = e.inputBuffer.getChannelData(0);
                    // Convert to 16-bit PCM
                    const buffer = new Int16Array(inputData.length);
                    for (let i = 0; i < inputData.length; i++) {
                        buffer[i] = Math.max(-1, Math.min(1, inputData[i])) * 0x7FFF;
                    }
                    ws.send(buffer.buffer);
                }
            };

            source.connect(processor);
            processor.connect(audioCtx.destination);

            setIsRecording(true);

        } catch (err) {
            console.error('Error starting recording:', err);
            alert('Could not start recording. Check console for details.');
        }
    };

    const stopRecording = () => {
        if (socketRef.current) {
            socketRef.current.close();
        }
        if (mediaStreamRef.current) {
            mediaStreamRef.current.getTracks().forEach(track => track.stop());
        }
        if (processorRef.current) {
            processorRef.current.disconnect();
        }
        if (audioContextRef.current) {
            audioContextRef.current.close();
        }
        setIsRecording(false);
    };

    const toggleLanguage = () => {
        const newSource = targetLang;
        const newTarget = sourceLang;
        setSourceLang(newSource);
        setTargetLang(newTarget);

        // Clear previous sessions
        setTranscript('');
        setTranslation('');

        // Update live config if running
        if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
            socketRef.current.send(JSON.stringify({
                type: 'config',
                source_lang: newSource,
                target_lang: newTarget
            }));
        }
    };

    return (
        <main className="flex min-h-screen flex-col items-center justify-center p-24 bg-slate-950 text-white">
            <div className="z-10 max-w-5xl w-full items-center justify-between font-mono text-sm lg:flex">
                <p className="fixed left-0 top-0 flex w-full justify-center border-b border-gray-800 bg-gradient-to-b from-zinc-200 pb-6 pt-8 backdrop-blur-2xl dark:border-neutral-800 dark:bg-zinc-800/30 dark:from-inherit lg:static lg:w-auto  lg:rounded-xl lg:border lg:bg-gray-200 lg:p-4 lg:dark:bg-zinc-800/30">
                    Speech-to-Speech Translator (MVP)
                </p>
            </div>

            <div className="flex flex-col gap-8 mt-10 w-full max-w-3xl">

                {/* Controls */}
                <div className="flex justify-between items-center bg-gray-900 p-6 rounded-xl border border-gray-800">
                    <div className="flex gap-4">
                        <button
                            onClick={() => setMode('mic')}
                            className={`p-3 rounded-lg flex items-center gap-2 ${mode === 'mic' ? 'bg-blue-600' : 'bg-gray-700 hover:bg-gray-600'}`}
                        >
                            <Mic size={20} /> Microphone
                        </button>
                        <button
                            onClick={() => setMode('system')}
                            className={`p-3 rounded-lg flex items-center gap-2 ${mode === 'system' ? 'bg-blue-600' : 'bg-gray-700 hover:bg-gray-600'}`}
                        >
                            <Monitor size={20} /> System Audio
                        </button>
                    </div>

                    <div className="flex items-center gap-4">
                        <div className="text-xl font-bold">{sourceLang.toUpperCase()}</div>
                        <button onClick={toggleLanguage} className="p-2 hover:bg-gray-700 rounded-full transition">
                            <Globe size={24} />
                        </button>
                        <div className="text-xl font-bold">{targetLang.toUpperCase()}</div>
                    </div>
                </div>

                {/* Start/Stop Interaction */}
                <div className="flex justify-center">
                    {!isRecording ? (
                        <button
                            onClick={startRecording}
                            className="bg-green-600 hover:bg-green-500 text-white font-bold py-4 px-8 rounded-full flex items-center gap-2 text-xl shadow-lg shadow-green-900/50 transition-all hover:scale-105"
                        >
                            <Play fill="currentColor" /> Start {mode === 'mic' ? 'Speaking' : 'Capture'}
                        </button>
                    ) : (
                        <button
                            onClick={stopRecording}
                            className="bg-red-600 hover:bg-red-500 text-white font-bold py-4 px-8 rounded-full flex items-center gap-2 text-xl shadow-lg shadow-red-900/50 transition-all hover:scale-105 animate-pulse"
                        >
                            <Square fill="currentColor" /> Stop Connection
                        </button>
                    )}
                </div>

                {/* Display Areas */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* Source */}
                    <div className="bg-gray-900 p-6 rounded-xl border border-gray-800 min-h-[200px]">
                        <h3 className="text-gray-400 mb-2 uppercase tracking-wide text-xs font-semibold">Live Transcript ({sourceLang})</h3>
                        <p className="text-lg leading-relaxed whitespace-pre-wrap">{transcript || "Waiting for audio..."}</p>
                    </div>

                    {/* Translation */}
                    <div className="bg-gray-900 p-6 rounded-xl border border-blue-900/30 min-h-[200px] shadow-inner shadow-black/50">
                        <h3 className="text-blue-400 mb-2 uppercase tracking-wide text-xs font-semibold">Translated ({targetLang})</h3>
                        <p className="text-lg leading-relaxed whitespace-pre-wrap text-blue-100">{translation || "Waiting for translation..."}</p>
                    </div>
                </div>

            </div>
        </main>
    );
}
