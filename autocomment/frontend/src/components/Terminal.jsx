import React, { useRef, useEffect, useState } from 'react';
import { Terminal as TerminalIcon, Copy, Trash2, ArrowDownCircle, Check, Maximize2, Minimize2 } from 'lucide-react';

export default function Terminal({ logs = [], isRunning = false, onClear }) {
  const terminalBodyRef = useRef(null);
  const [autoScroll, setAutoScroll] = useState(true);
  const [copied, setCopied] = useState(false);
  const [isFullScreen, setIsFullScreen] = useState(false);

  // Auto-scroll to bottom if autoScroll is enabled
  useEffect(() => {
    if (autoScroll && terminalBodyRef.current) {
      terminalBodyRef.current.scrollTop = terminalBodyRef.current.scrollHeight;
    }
  }, [logs, autoScroll]);

  const handleCopy = () => {
    const text = logs.join('\n');
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  const formatLine = (line, index) => {
    let colorClass = 'text-slate-300';

    if (line.includes('❌') || line.includes('[ERROR]') || line.includes('Error') || line.includes('Traceback') || line.includes('[STDERR]')) {
      colorClass = 'text-rose-400 font-medium';
    } else if (line.includes('✅') || line.includes('berhasil') || line.includes('Selesai')) {
      colorClass = 'text-emerald-400 font-medium';
    } else if (line.includes('⚠️') || line.includes('[WARNING]') || line.includes('⏳')) {
      colorClass = 'text-amber-300';
    } else if (line.includes('🤖') || line.includes('🔗') || line.includes('👤') || line.includes('💬')) {
      colorClass = 'text-sky-300';
    } else if (line.startsWith('[RUNNER]')) {
      colorClass = 'text-indigo-300';
    } else if (line.startsWith('---') || line.startsWith('===')) {
      colorClass = 'text-slate-500';
    }

    return (
      <div key={index} className="flex items-start hover:bg-slate-800/40 px-2 py-0.5 rounded leading-relaxed">
        <span className="text-slate-600 select-none mr-3 text-xs w-7 text-right font-mono flex-shrink-0 pt-0.5">
          {index + 1}
        </span>
        <span className={`break-all font-mono text-xs sm:text-sm whitespace-pre-wrap ${colorClass}`}>
          {line}
        </span>
      </div>
    );
  };

  return (
    <div className={`flex flex-col bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-2xl transition-all duration-200 ${isFullScreen ? 'fixed inset-4 z-50 shadow-black' : 'h-[460px] sm:h-[520px]'}`}>
      {/* Terminal Header */}
      <div className="flex items-center justify-between px-4 py-3 bg-slate-950/80 border-b border-slate-800 backdrop-blur">
        <div className="flex items-center space-x-2">
          <div className="flex space-x-1.5 mr-2">
            <span className="w-3 h-3 rounded-full bg-rose-500/80 inline-block"></span>
            <span className="w-3 h-3 rounded-full bg-amber-500/80 inline-block"></span>
            <span className="w-3 h-3 rounded-full bg-emerald-500/80 inline-block"></span>
          </div>
          <TerminalIcon className="w-4 h-4 text-sky-400" />
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-300 font-mono">
            Virtual Console Output
          </span>
          {isRunning && (
            <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium bg-amber-500/10 text-amber-400 border border-amber-500/20 animate-pulse">
              <span className="w-1.5 h-1.5 rounded-full bg-amber-400"></span>
              Live Running
            </span>
          )}
        </div>

        {/* Header Action Buttons */}
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setAutoScroll(!autoScroll)}
            title={autoScroll ? "Nonaktifkan Auto-scroll" : "Aktifkan Auto-scroll"}
            className={`p-1.5 rounded-lg text-xs flex items-center gap-1 border transition-colors ${
              autoScroll 
                ? 'bg-sky-500/10 text-sky-400 border-sky-500/30' 
                : 'bg-slate-800 text-slate-400 border-slate-700 hover:text-slate-200'
            }`}
          >
            <ArrowDownCircle className="w-3.5 h-3.5" />
            <span className="hidden sm:inline font-mono">Scroll</span>
          </button>

          <button
            onClick={handleCopy}
            disabled={logs.length === 0}
            title="Salin semua log"
            className="p-1.5 rounded-lg text-xs flex items-center gap-1 bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 disabled:opacity-40 transition-colors"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
            <span className="hidden sm:inline font-mono">{copied ? 'Tersalin' : 'Copy'}</span>
          </button>

          <button
            onClick={onClear}
            disabled={logs.length === 0 || isRunning}
            title="Bersihkan Terminal"
            className="p-1.5 rounded-lg text-xs flex items-center gap-1 bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 disabled:opacity-40 transition-colors"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span className="hidden sm:inline font-mono">Clear</span>
          </button>

          <button
            onClick={() => setIsFullScreen(!isFullScreen)}
            title={isFullScreen ? "Kecilkan Terminal" : "Layar Penuh"}
            className="p-1.5 rounded-lg text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition-colors"
          >
            {isFullScreen ? <Minimize2 className="w-3.5 h-3.5" /> : <Maximize2 className="w-3.5 h-3.5" />}
          </button>
        </div>
      </div>

      {/* Terminal Body */}
      <div
        ref={terminalBodyRef}
        className="flex-1 overflow-y-auto p-4 bg-slate-950 font-mono text-xs sm:text-sm space-y-0.5 select-text"
      >
        {logs.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-slate-500 space-y-2 select-none">
            <TerminalIcon className="w-10 h-10 stroke-[1.5] text-slate-700" />
            <p className="text-sm font-medium">Terminal siap menerima output.</p>
            <p className="text-xs text-slate-600">
              Klik tombol <strong className="text-slate-400">"Jalankan Auto Comment"</strong> untuk memulai eksekusi auto.py.
            </p>
          </div>
        ) : (
          <>
            {logs.map((line, idx) => formatLine(line, idx))}
            {isRunning && (
              <div className="flex items-center text-sky-400 px-2 py-1 font-mono text-xs animate-pulse">
                <span className="w-2 h-4 bg-sky-400 inline-block mr-2 animate-bounce"></span>
                <span>Menunggu output berikutnya dari Selenium / auto.py...</span>
              </div>
            )}
          </>
        )}
      </div>

      {/* Terminal Footer Info Bar */}
      <div className="px-4 py-2 bg-slate-950 border-t border-slate-800/80 text-[11px] font-mono text-slate-400 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <span>Baris: <strong className="text-slate-200">{logs.length}</strong></span>
          <span>•</span>
          <span>Status Buffer: <strong className="text-emerald-400">Siap</strong></span>
        </div>
        <div className="text-slate-500">
          stdout / stderr captured via subprocess
        </div>
      </div>
    </div>
  );
}
