import React from 'react';
import { FileSpreadsheet, Trash2 } from 'lucide-react';

const Sidebar = ({ sessions, activeSession, setActiveSession, setMessages, setShowPreview, deleteSession }) => {
    return (
        <aside className="w-72 bg-white border-r border-slate-200 flex flex-col h-full">
            <div className="p-4 border-b border-slate-200 bg-slate-50/50">
                <h2 className="text-xs font-bold text-slate-500 uppercase tracking-widest flex items-center gap-2">
                    <FileSpreadsheet className="w-4 h-4 text-indigo-500" />
                    Historique
                </h2>
            </div>

            <div className="flex-1 overflow-y-auto p-3 space-y-2">
                {sessions.length === 0 ? (
                    <div className="flex flex-col items-center justify-center h-48 text-center p-4">
                        <div className="w-12 h-12 bg-slate-100 rounded-full flex items-center justify-center mb-3">
                            <FileSpreadsheet className="w-6 h-6 text-slate-300" />
                        </div>
                        <p className="text-sm font-medium text-slate-500">Aucun fichier</p>
                        <p className="text-xs text-slate-400 mt-1">Importez un document pour commencer une session.</p>
                    </div>
                ) : (
                    sessions.map(session => (
                        <div
                            key={session.id}
                            onClick={() => { setActiveSession(session); setMessages(session.messages || []); setShowPreview(true); }}
                            className={`p-3 rounded-xl cursor-pointer transition-all group border relative ${activeSession?.id === session.id
                                    ? 'bg-white border-indigo-200 shadow-sm ring-1 ring-indigo-50'
                                    : 'hover:bg-slate-50 border-transparent hover:border-slate-200'
                                }`}
                        >
                            <div className="flex items-start justify-between gap-2">
                                <div className="flex-1 min-w-0">
                                    <p className={`font-medium truncate text-sm ${activeSession?.id === session.id ? 'text-indigo-700' : 'text-slate-700'}`}>
                                        {session.filename}
                                    </p>
                                    <p className="text-xs text-slate-400 mt-1 flex items-center gap-1">
                                        {session.timestamp}
                                    </p>
                                </div>
                                <button
                                    onClick={(e) => { e.stopPropagation(); deleteSession(session.id); }}
                                    className="opacity-0 group-hover:opacity-100 p-1.5 text-slate-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-all absolute top-2 right-2"
                                    title="Supprimer"
                                >
                                    <Trash2 className="w-3.5 h-3.5" />
                                </button>
                            </div>
                        </div>
                    ))
                )}
            </div>

            <div className="p-4 border-t border-slate-200 bg-slate-50/30">
                <p className="text-xs text-center text-slate-400">
                    AF-Advisory v1.0
                </p>
            </div>
        </aside>
    );
};

export default Sidebar;
