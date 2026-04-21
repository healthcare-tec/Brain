import React, { useState, useRef, useCallback } from 'react';
import { Mic, MicOff, Send, Inbox, Loader2, AlertCircle, CheckCircle2 } from 'lucide-react';
import { voiceApi } from '../services/api';

export default function VoiceCapturePage() {
  const [isRecording, setIsRecording] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [interimTranscript, setInterimTranscript] = useState('');
  const [processing, setProcessing] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);
  const recognitionRef = useRef(null);

  const speechSupported = typeof window !== 'undefined' &&
    ('SpeechRecognition' in window || 'webkitSpeechRecognition' in window);

  const startRecording = useCallback(() => {
    if (!speechSupported) {
      setError('Web Speech API nao suportada neste navegador. Use Chrome ou Edge.');
      return;
    }

    setError(null);
    setResults(null);

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'pt-BR';

    recognition.onresult = (event) => {
      let interim = '';
      let final = '';
      for (let i = 0; i < event.results.length; i++) {
        const result = event.results[i];
        if (result.isFinal) {
          final += result[0].transcript + ' ';
        } else {
          interim += result[0].transcript;
        }
      }
      if (final) setTranscript(prev => prev + final);
      setInterimTranscript(interim);
    };

    recognition.onerror = (event) => {
      if (event.error !== 'no-speech') {
        setError(`Speech recognition error: ${event.error}`);
      }
      setIsRecording(false);
    };

    recognition.onend = () => {
      setIsRecording(false);
      setInterimTranscript('');
    };

    recognitionRef.current = recognition;
    recognition.start();
    setIsRecording(true);
  }, [speechSupported]);

  const stopRecording = useCallback(() => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
    }
    setIsRecording(false);
  }, []);

  const handleSubmit = async () => {
    const text = transcript.trim();
    if (!text) return;

    setProcessing(true);
    setError(null);
    try {
      const data = await voiceApi.capture(text);
      setResults(data);
      setTranscript('');
    } catch (err) {
      setError(err.message);
    } finally {
      setProcessing(false);
    }
  };

  const handleManualSubmit = async () => {
    await handleSubmit();
  };

  return (
    <div className="max-w-2xl mx-auto">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 rounded-xl bg-rose-100 dark:bg-rose-900/30 flex items-center justify-center">
          <Mic className="w-5 h-5 text-rose-600 dark:text-rose-400" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Voice Capture</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Fale livremente — a IA separa em multiplas entradas no Inbox
          </p>
        </div>
      </div>

      {/* Recording area */}
      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6 mb-6">
        {/* Mic button */}
        <div className="flex justify-center mb-6">
          <button
            onClick={isRecording ? stopRecording : startRecording}
            className={`w-24 h-24 rounded-full flex items-center justify-center transition-all ${
              isRecording
                ? 'bg-red-500 hover:bg-red-600 animate-pulse shadow-lg shadow-red-500/30'
                : 'bg-charlie-600 hover:bg-charlie-700 shadow-lg shadow-charlie-500/30'
            }`}
          >
            {isRecording ? (
              <MicOff className="w-10 h-10 text-white" />
            ) : (
              <Mic className="w-10 h-10 text-white" />
            )}
          </button>
        </div>

        <p className="text-center text-sm text-gray-500 dark:text-gray-400 mb-4">
          {isRecording
            ? 'Gravando... Fale naturalmente. Clique para parar.'
            : speechSupported
              ? 'Clique no microfone para comecar a gravar'
              : 'Digite o texto abaixo (Speech API nao disponivel)'}
        </p>

        {/* Transcript area */}
        <div className="relative">
          <textarea
            value={transcript + interimTranscript}
            onChange={(e) => { setTranscript(e.target.value); setInterimTranscript(''); }}
            placeholder="O texto transcrito aparecera aqui... Ou digite manualmente."
            rows={5}
            className="w-full px-4 py-3 rounded-xl border border-gray-200 dark:border-gray-600 bg-gray-50 dark:bg-gray-700 dark:text-gray-100 text-sm resize-none outline-none focus:ring-2 focus:ring-charlie-500"
          />
          {interimTranscript && (
            <div className="absolute bottom-3 right-3">
              <span className="text-xs text-gray-400 dark:text-gray-500 animate-pulse">transcrevendo...</span>
            </div>
          )}
        </div>

        {/* Submit button */}
        <div className="flex justify-end mt-4">
          <button
            onClick={handleManualSubmit}
            disabled={!transcript.trim() || processing}
            className="px-6 py-2.5 bg-charlie-600 text-white rounded-xl text-sm font-medium hover:bg-charlie-700 disabled:opacity-50 transition-colors flex items-center gap-2"
          >
            {processing ? (
              <><Loader2 className="w-4 h-4 animate-spin" />Processando com IA...</>
            ) : (
              <><Send className="w-4 h-4" />Enviar para Inbox</>
            )}
          </button>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="mb-6 flex items-start gap-2 px-4 py-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-700 rounded-xl text-sm text-red-700 dark:text-red-300">
          <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
          {error}
        </div>
      )}

      {/* Results */}
      {results && (
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center gap-2 mb-4">
            <CheckCircle2 className="w-5 h-5 text-green-500" />
            <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300">
              {results.items_created} {results.items_created === 1 ? 'item criado' : 'itens criados'} no Inbox
            </h3>
          </div>
          <div className="space-y-2">
            {results.items.map((item, i) => (
              <div
                key={item.id || i}
                className="flex items-center gap-3 px-4 py-3 bg-gray-50 dark:bg-gray-700 rounded-lg"
              >
                <Inbox className="w-4 h-4 text-charlie-500 flex-shrink-0" />
                <div className="flex-1">
                  <p className="text-sm text-gray-900 dark:text-gray-100">{item.content}</p>
                  {item.type_hint && (
                    <span className="text-xs text-gray-400 dark:text-gray-500">{item.type_hint}</span>
                  )}
                </div>
              </div>
            ))}
          </div>
          <button
            onClick={() => setResults(null)}
            className="mt-4 text-xs text-charlie-600 dark:text-charlie-400 hover:underline"
          >
            Capturar mais
          </button>
        </div>
      )}

      {/* How it works */}
      <div className="mt-8 bg-gray-50 dark:bg-gray-800/50 rounded-xl p-5">
        <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">Como funciona</h3>
        <div className="space-y-2 text-xs text-gray-500 dark:text-gray-400">
          <p>1. Fale livremente sobre tudo que esta na sua cabeca</p>
          <p>2. A IA analisa o texto e identifica cada item separadamente</p>
          <p>3. Cada item e criado como uma entrada individual no Inbox</p>
          <p className="italic mt-2">
            Exemplo: "preciso comprar leite, tambem tenho que ligar pro Joao sobre o projeto X
            e nao posso esquecer de revisar o relatorio" → 3 itens no Inbox
          </p>
        </div>
      </div>
    </div>
  );
}
