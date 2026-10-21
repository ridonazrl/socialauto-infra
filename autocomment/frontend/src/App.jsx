import React, { useState, useEffect, useRef } from 'react';
import { 
  Play, 
  Square, 
  RefreshCw, 
  ExternalLink, 
  CheckCircle, 
  AlertTriangle, 
  Clock, 
  Settings2, 
  Bot, 
  Layers, 
  MessageSquare,
  Globe,
  Sliders,
  Check
} from 'lucide-react';
import Terminal from './components/Terminal';
import StatusCard from './components/StatusCard';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

export default function App() {
  const [postUrl, setPostUrl] = useState('');
  const [headless, setHeadless] = useState(false);
  const [mode, setMode] = useState('direct'); // 'direct' or 'interactive'
  const [isRunning, setIsRunning] = useState(false);
  const [logs, setLogs] = useState([]);
  const [lastResult, setLastResult] = useState(null);
  const [systemStatus, setSystemStatus] = useState(null);
  const [accounts, setAccounts] = useState([]);
  const [history, setHistory] = useState([]);
  const [backendOnline, setBackendOnline] = useState(false);
  const [activeTab, setActiveTab] = useState('terminal'); // 'terminal' | 'accounts' | 'history'

  const eventSourceRef = useRef(null);

  // Load initial status & accounts
  const checkStatus = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/status`);
      if (res.ok) {
        const data = await res.json();
        setSystemStatus(data);
        setIsRunning(data.is_running);
        if (data.last_result && !lastResult) {
          setLastResult(data.last_result);
        }
        setBackendOnline(true);
      } else {
        setBackendOnline(false);
      }
    } catch (err) {
      setBackendOnline(false);
    }
  };

  const fetchAccounts = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/accounts`);
      if (res.ok) {
        const data = await res.json();
        setAccounts(data.accounts || []);
      }
    } catch (err) {
      console.error("Gagal mengambil akun:", err);
    }
  };

  const fetchHistory = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/results?limit=20`);
      if (res.ok) {
        const data = await res.json();
        setHistory(data.results || []);
      }
    } catch (err) {
      console.error("Gagal mengambil riwayat:", err);
    }
  };

  useEffect(() => {
    checkStatus();
    fetchAccounts();
    fetchHistory();
    const interval = setInterval(() => {
      checkStatus();
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  // Connect to SSE stream logs
  const startLogStream = () => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }
    const es = new EventSource(`${API_BASE_URL}/stream-logs`);
    eventSourceRef.current = es;

    es.onmessage = (event) => {
      if (event.data) {
        setLogs((prev) => [...prev, event.data]);
      }
    };

    es.onerror = () => {
      es.close();
      eventSourceRef.current = null;
    };
  };

  const stopLogStream = () => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
  };

  // Main trigger for running auto.py
  const handleRun = async () => {
    if (isRunning) return;

    setIsRunning(true);
    setActiveTab('terminal');

    // Add starting header
    const startTimeStr = new Date().toLocaleTimeString();
    setLogs([
      `[FE] ⚡ Memulai permintaan eksekusi auto.py pada ${startTimeStr}...`,
      `[FE] 🌐 Target API: ${API_BASE_URL}/run-autocomment`,
      postUrl ? `[FE] 🔗 Target Post: ${postUrl}` : `[FE] ℹ️ Menggunakan post URL default dari konfigurasi .env`,
      `[FE] ⚙️ Mode: ${mode}, Headless: ${headless}`,
      `------------------------------------------------------------`
    ]);

    // Open live log stream listener
    startLogStream();

    try {
      const response = await fetch(`${API_BASE_URL}/run-autocomment`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          post_url: postUrl.trim() || null,
          headless: headless,
          mode: mode,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || data.message || `Server returned code ${response.status}`);
      }

      setLastResult(data);

      // If SSE didn't populate logs or for completeness, append final confirmation
      setLogs((prev) => [
        ...prev,
        `[FE] 🏁 Response diterima dari Backend! (Status: ${data.status}, Exit Code: ${data.returncode}, Waktu: ${data.execution_time_seconds}s)`,
      ]);

      // Refresh accounts & results
      fetchHistory();
      checkStatus();
    } catch (err) {
      setLogs((prev) => [
        ...prev,
        `[FE] ❌ Gagal menjalankan script: ${err.message}`,
        `[FE] Periksa apakah server backend FastAPI aktif di ${API_BASE_URL}`,
      ]);
      setLastResult({
        status: 'error',
        message: err.message,
        returncode: -1,
        execution_time_seconds: 0,
      });
    } finally {
      setIsRunning(false);
      stopLogStream();
    }
  };

  // Stop script execution
  const handleStop = async () => {
    try {
      setLogs((prev) => [...prev, `[FE] ⛔ Mengirim sinyal STOP ke backend...`]);
      const res = await fetch(`${API_BASE_URL}/stop`, { method: 'POST' });
      const data = await res.json();
      setLogs((prev) => [...prev, `[FE] Hasil STOP: ${data.message}`]);
    } catch (err) {
      setLogs((prev) => [...prev, `[FE] Gagal menghentikan proses: ${err.message}`]);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      {/* Top Navigation Bar */}
      <header className="border-b border-slate-800 bg-slate-900/60 backdrop-blur sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-sky-600 to-indigo-600 flex items-center justify-center shadow-lg shadow-sky-500/20">
              <Bot className="w-6 h-6 text-white" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h1 className="text-base font-bold tracking-tight text-white">AutoComment Runner</h1>
                <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-sky-500/10 text-sky-400 border border-sky-500/20">v1.0</span>
              </div>
              <p className="text-xs text-slate-400 flex items-center gap-1">
                <span>Repository:</span>
                <a
                  href="https://github.com/Elang64/AutoComment_Python.git"
                  target="_blank"
                  rel="noreferrer"
                  className="text-slate-300 hover:text-sky-400 font-mono transition-colors flex items-center gap-0.5"
                >
                  Elang64/AutoComment_Python
                  <ExternalLink className="w-3 h-3 inline" />
                </a>
              </p>
            </div>
          </div>

          {/* Backend Connection Status Badge */}
          <div className="flex items-center space-x-3">
            <div className={`flex items-center space-x-2 px-3 py-1 rounded-full text-xs font-medium border ${
              backendOnline 
                ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' 
                : 'bg-rose-500/10 text-rose-400 border-rose-500/20'
            }`}>
              <span className={`w-2 h-2 rounded-full ${backendOnline ? 'bg-emerald-400 animate-pulse' : 'bg-rose-400'}`}></span>
              <span>{backendOnline ? 'FastAPI Connected' : 'FastAPI Offline'}</span>
            </div>

            <button
              onClick={() => { checkStatus(); fetchAccounts(); fetchHistory(); }}
              title="Refresh status data"
              className="p-2 text-slate-400 hover:text-slate-200 bg-slate-800/80 hover:bg-slate-700/80 rounded-lg border border-slate-700 transition-colors"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 flex-1 w-full space-y-6">
        {/* Status Metrics Cards */}
        <StatusCard
          isRunning={isRunning}
          lastResult={lastResult}
          systemStatus={systemStatus}
          accountsCount={accounts.length}
        />

        {/* Control Dashboard Panel */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-xl backdrop-blur space-y-5">
          <div className="flex items-center justify-between border-b border-slate-800/80 pb-4">
            <div className="flex items-center space-x-2">
              <Sliders className="w-5 h-5 text-sky-400" />
              <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-200">Panel Kontrol Eksekusi</h2>
            </div>
            <span className="text-xs text-slate-500">Memicu auto.py via FastAPI Subprocess</span>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-end">
            {/* Target Post URL Input */}
            <div className="lg:col-span-6 space-y-2">
              <label className="text-xs font-semibold text-slate-300 flex items-center justify-between">
                <span>Target Post URL Facebook</span>
                <span className="text-[11px] font-normal text-slate-500">Bisa dikosongkan jika menggunakan .env</span>
              </label>
              <div className="relative">
                <input
                  type="url"
                  placeholder="https://www.facebook.com/username/posts/123456789..."
                  value={postUrl}
                  onChange={(e) => setPostUrl(e.target.value)}
                  disabled={isRunning}
                  className="w-full bg-slate-950 border border-slate-700 focus:border-sky-500 focus:ring-1 focus:ring-sky-500 rounded-xl px-4 py-2.5 text-sm text-slate-100 placeholder-slate-600 disabled:opacity-50 transition-all font-mono"
                />
                {postUrl && (
                  <button
                    onClick={() => setPostUrl('')}
                    disabled={isRunning}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-slate-500 hover:text-slate-300"
                  >
                    Clear
                  </button>
                )}
              </div>
            </div>

            {/* Mode & Headless Options */}
            <div className="lg:col-span-3 flex items-center space-x-4 pb-1">
              <label className="flex items-center space-x-2 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={headless}
                  onChange={(e) => setHeadless(e.target.checked)}
                  disabled={isRunning}
                  className="w-4 h-4 rounded border-slate-700 text-sky-600 focus:ring-sky-500 bg-slate-950"
                />
                <span className="text-xs font-medium text-slate-300">Mode Headless</span>
              </label>

              <select
                value={mode}
                onChange={(e) => setMode(e.target.value)}
                disabled={isRunning}
                className="bg-slate-950 border border-slate-700 text-xs rounded-lg px-2.5 py-1.5 text-slate-300 focus:border-sky-500 font-mono disabled:opacity-50"
              >
                <option value="direct">Direct Mode (Fungsi)</option>
                <option value="interactive">Interactive (CLI Stdin)</option>
              </select>
            </div>

            {/* Action Buttons */}
            <div className="lg:col-span-3 flex space-x-3">
              <button
                onClick={handleRun}
                disabled={isRunning || !backendOnline}
                className={`flex-1 flex items-center justify-center space-x-2 px-5 py-3 rounded-xl font-semibold text-sm transition-all duration-200 shadow-lg ${
                  isRunning
                    ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30 cursor-not-allowed'
                    : 'bg-gradient-to-r from-sky-500 to-indigo-600 hover:from-sky-400 hover:to-indigo-500 text-white shadow-sky-500/25 active:scale-95'
                }`}
              >
                {isRunning ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin text-amber-300" />
                    <span>Menjalankan...</span>
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4 fill-white" />
                    <span>Jalankan Auto Comment</span>
                  </>
                )}
              </button>

              {isRunning && (
                <button
                  onClick={handleStop}
                  title="Hentikan Proses"
                  className="px-4 py-3 bg-rose-600/20 hover:bg-rose-600/30 text-rose-300 border border-rose-500/40 rounded-xl text-sm font-semibold flex items-center space-x-1.5 transition-colors"
                >
                  <Square className="w-4 h-4 fill-rose-300" />
                  <span className="hidden sm:inline">Stop</span>
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Tab Selector & Terminal Section */}
        <div className="space-y-4">
          <div className="flex border-b border-slate-800">
            <button
              onClick={() => setActiveTab('terminal')}
              className={`flex items-center space-x-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
                activeTab === 'terminal'
                  ? 'border-sky-500 text-sky-400 bg-sky-500/5'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              <Bot className="w-4 h-4" />
              <span>Virtual Terminal Log</span>
            </button>

            <button
              onClick={() => setActiveTab('accounts')}
              className={`flex items-center space-x-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
                activeTab === 'accounts'
                  ? 'border-sky-500 text-sky-400 bg-sky-500/5'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              <Layers className="w-4 h-4" />
              <span>Daftar Akun ({accounts.length})</span>
            </button>

            <button
              onClick={() => setActiveTab('history')}
              className={`flex items-center space-x-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
                activeTab === 'history'
                  ? 'border-sky-500 text-sky-400 bg-sky-500/5'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              <MessageSquare className="w-4 h-4" />
              <span>Riwayat Komentar ({history.length})</span>
            </button>
          </div>

          {/* Tab 1: Virtual Terminal Output */}
          {activeTab === 'terminal' && (
            <Terminal
              logs={logs}
              isRunning={isRunning}
              onClear={() => setLogs([])}
            />
          )}

          {/* Tab 2: Accounts Table */}
          {activeTab === 'accounts' && (
            <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-xl p-4">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-bold text-slate-200">Akun Tersimpan di accounts/accounts.json</h3>
                <span className="text-xs text-slate-500">Cookies tersimpan di folder cookies/</span>
              </div>
              {accounts.length === 0 ? (
                <div className="text-center py-8 text-slate-500 text-sm">
                  Tidak ada akun ditemukan di accounts.json
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs font-mono">
                    <thead className="bg-slate-950/80 text-slate-400 uppercase text-[11px] border-b border-slate-800">
                      <tr>
                        <th className="px-4 py-3">Nama</th>
                        <th className="px-4 py-3">Email</th>
                        <th className="px-4 py-3">Status Cookies</th>
                        <th className="px-4 py-3">Dibuat Pada</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800 text-slate-300">
                      {accounts.map((acc, idx) => (
                        <tr key={idx} className="hover:bg-slate-800/40">
                          <td className="px-4 py-3 font-semibold text-slate-100">{acc.name}</td>
                          <td className="px-4 py-3 text-slate-400">{acc.email}</td>
                          <td className="px-4 py-3">
                            {acc.has_cookies ? (
                              <span className="inline-flex items-center gap-1 text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                                <Check className="w-3 h-3" /> Cookies Tersedia
                              </span>
                            ) : (
                              <span className="inline-flex items-center gap-1 text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/20">
                                <AlertTriangle className="w-3 h-3" /> Cookies Belum Diimport
                              </span>
                            )}
                          </td>
                          <td className="px-4 py-3 text-slate-500">{acc.created_at || '-'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {/* Tab 3: Comment History Table */}
          {activeTab === 'history' && (
            <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-xl p-4">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-bold text-slate-200">Riwayat Hasil Komentar (results.json)</h3>
                <span className="text-xs text-slate-500">20 hasil terbaru</span>
              </div>
              {history.length === 0 ? (
                <div className="text-center py-8 text-slate-500 text-sm">
                  Belum ada riwayat hasil komentar di results.json
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-950/80 text-slate-400 uppercase text-[11px] border-b border-slate-800 font-mono">
                      <tr>
                        <th className="px-4 py-3">Waktu</th>
                        <th className="px-4 py-3">Akun</th>
                        <th className="px-4 py-3">Komentar</th>
                        <th className="px-4 py-3">Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800 text-slate-300">
                      {history.map((item, idx) => (
                        <tr key={idx} className="hover:bg-slate-800/40">
                          <td className="px-4 py-3 text-slate-500 font-mono text-[11px] whitespace-nowrap">
                            {item.timestamp}
                          </td>
                          <td className="px-4 py-3 font-semibold font-mono text-slate-200">
                            {item.account}
                          </td>
                          <td className="px-4 py-3 text-slate-300 max-w-md italic">
                            "{item.comment || item.error || '-'}"
                          </td>
                          <td className="px-4 py-3 whitespace-nowrap">
                            {item.success ? (
                              <span className="text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20 font-medium">
                                Sukses
                              </span>
                            ) : (
                              <span className="text-rose-400 bg-rose-500/10 px-2 py-0.5 rounded border border-rose-500/20 font-medium">
                                Gagal ({item.error || 'Unknown'})
                              </span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800 bg-slate-950 py-4 mt-auto">
        <div className="max-w-7xl mx-auto px-4 text-center text-xs text-slate-500">
          Facebook AutoComment Full-Stack Runner • FastAPI + React Vite • Powered by Google Gemini AI
        </div>
      </footer>
    </div>
  );
}
