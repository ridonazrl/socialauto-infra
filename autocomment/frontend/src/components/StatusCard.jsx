import React from 'react';
import { Activity, Clock, Users, CheckCircle2, XCircle, AlertCircle, ShieldCheck } from 'lucide-react';

export default function StatusCard({ isRunning, lastResult, systemStatus, accountsCount }) {
  const getStatusBadge = () => {
    if (isRunning) {
      return (
        <div className="flex items-center space-x-2 text-amber-400 bg-amber-500/10 px-3 py-1 rounded-full border border-amber-500/20">
          <span className="w-2.5 h-2.5 rounded-full bg-amber-400 animate-ping"></span>
          <span className="text-xs font-semibold uppercase tracking-wider">Sedang Berjalan</span>
        </div>
      );
    }
    if (!lastResult) {
      return (
        <div className="flex items-center space-x-2 text-slate-400 bg-slate-800/60 px-3 py-1 rounded-full border border-slate-700">
          <span className="w-2.5 h-2.5 rounded-full bg-slate-500"></span>
          <span className="text-xs font-semibold uppercase tracking-wider">Standby / Idle</span>
        </div>
      );
    }
    if (lastResult.status === 'success') {
      return (
        <div className="flex items-center space-x-2 text-emerald-400 bg-emerald-500/10 px-3 py-1 rounded-full border border-emerald-500/20">
          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          <span className="text-xs font-semibold uppercase tracking-wider">Sukses (Code 0)</span>
        </div>
      );
    }
    return (
      <div className="flex items-center space-x-2 text-rose-400 bg-rose-500/10 px-3 py-1 rounded-full border border-rose-500/20">
        <XCircle className="w-4 h-4 text-rose-400" />
        <span className="text-xs font-semibold uppercase tracking-wider">Error (Code {lastResult.returncode})</span>
      </div>
    );
  };

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {/* Status Eksekusi */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 flex flex-col justify-between backdrop-blur shadow-sm">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-medium text-slate-400">Status Proses</span>
          <Activity className="w-4 h-4 text-sky-400" />
        </div>
        <div className="flex items-center justify-start mt-1">
          {getStatusBadge()}
        </div>
      </div>

      {/* Durasi Terakhir */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 flex flex-col justify-between backdrop-blur shadow-sm">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-medium text-slate-400">Waktu Eksekusi</span>
          <Clock className="w-4 h-4 text-indigo-400" />
        </div>
        <div className="mt-1">
          <div className="text-xl font-bold font-mono text-slate-100">
            {lastResult?.execution_time_seconds ? `${lastResult.execution_time_seconds}s` : '--'}
          </div>
          <p className="text-[11px] text-slate-500 mt-0.5">
            {lastResult?.timestamp ? new Date(lastResult.timestamp).toLocaleTimeString() : 'Belum dijalankan'}
          </p>
        </div>
      </div>

      {/* Total Akun Terdaftar */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 flex flex-col justify-between backdrop-blur shadow-sm">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-medium text-slate-400">Akun Facebook</span>
          <Users className="w-4 h-4 text-emerald-400" />
        </div>
        <div className="mt-1">
          <div className="text-xl font-bold font-mono text-slate-100">
            {accountsCount} <span className="text-xs font-normal text-slate-400">akun terdeteksi</span>
          </div>
          <p className="text-[11px] text-slate-500 mt-0.5">
            Dari file accounts.json
          </p>
        </div>
      </div>

      {/* Kesiapan Script / Gemini */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 flex flex-col justify-between backdrop-blur shadow-sm">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-medium text-slate-400">Kesiapan Script</span>
          <ShieldCheck className="w-4 h-4 text-violet-400" />
        </div>
        <div className="mt-1 flex items-center space-x-2">
          {systemStatus?.auto_py_exists ? (
            <span className="inline-flex items-center text-xs font-medium text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
              auto.py Tersedia
            </span>
          ) : (
            <span className="inline-flex items-center text-xs font-medium text-rose-400 bg-rose-500/10 px-2 py-0.5 rounded border border-rose-500/20">
              auto.py Hilang
            </span>
          )}
          <span className="text-[11px] text-slate-400">FastAPI Online</span>
        </div>
      </div>
    </div>
  );
}
