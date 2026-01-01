import React, { useState, useRef, useEffect } from 'react';
import { Database, MessageSquare, Upload, Send, FileSpreadsheet, Trash2, Plus, Bot, User, Loader2 } from 'lucide-react';

function App() {
  const [sessions, setSessions] = useState([]);
  const [activeSession, setActiveSession] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [dataPreview, setDataPreview] = useState(null);
  const [dataSummary, setDataSummary] = useState(null);
  const [showPreview, setShowPreview] = useState(true);
  const fileInputRef = useRef(null);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(scrollToBottom, [messages]);

  // Load data preview when session changes
  useEffect(() => {
    if (activeSession?.dbPath) {
      loadDataPreview(activeSession.dbPath);
    } else {
      setDataPreview(null);
      setDataSummary(null);
    }
  }, [activeSession]);

  const loadDataPreview = async (dbPath) => {
    try {
      const [previewRes, summaryRes] = await Promise.all([
        fetch(`http://localhost:8000/data/preview?db_path=${encodeURIComponent(dbPath)}&limit=10`),
        fetch(`http://localhost:8000/data/summary?db_path=${encodeURIComponent(dbPath)}`)
      ]);
      if (previewRes.ok) setDataPreview(await previewRes.json());
      if (summaryRes.ok) setDataSummary(await summaryRes.json());
    } catch (err) {
      console.error('Failed to load preview:', err);
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsLoading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('http://localhost:8000/upload/', {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        const data = await response.json();
        const newSession = {
          id: Date.now(),
          filename: data.filename,
          dbPath: data.db_path,
          timestamp: new Date().toLocaleString(),
          messages: []
        };
        setSessions(prev => [newSession, ...prev]);
        setActiveSession(newSession);
        setMessages([]);
        setShowPreview(true);
      }
    } catch (err) {
      console.error('Upload failed:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim() || isLoading || !activeSession) return;

    const userMessage = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);
    setShowPreview(false);

    try {
      const response = await fetch('http://localhost:8000/query/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: userMessage.content,
          db_path: activeSession.dbPath,
          chat_history: messages
        }),
      });

      const data = await response.json();
      console.log('API Response:', data);
      let assistantContent = "Je n'ai pas pu traiter cette requête.";

      if (data.result) {
        // Format the result based on what we got
        if (data.result.data && Array.isArray(data.result.data)) {
          if (data.result.data.length === 0) {
            assistantContent = "Aucun résultat trouvé.";
          } else {
            // Format as a nice table-like output
            const columns = data.result.columns || Object.keys(data.result.data[0]);
            const rows = data.result.data.slice(0, 20); // Limit display

            let output = `📊 Résultats (${data.result.data.length} lignes):\n\n`;
            output += columns.join(' | ') + '\n';
            output += columns.map(() => '---').join(' | ') + '\n';
            rows.forEach(row => {
              output += columns.map(col => row[col] ?? 'null').join(' | ') + '\n';
            });
            if (data.result.data.length > 20) {
              output += `\n... et ${data.result.data.length - 20} lignes de plus`;
            }
            assistantContent = output;
          }
        } else if (data.result.message) {
          assistantContent = data.result.message;
        } else {
          // Fallback: stringify the result
          assistantContent = JSON.stringify(data.result, null, 2);
        }
      } else if (data.error) {
        assistantContent = `❌ Erreur: ${data.error}`;
      }

      setMessages(prev => [...prev, { role: 'assistant', content: assistantContent }]);
    } catch (error) {
      setMessages(prev => [...prev, { role: 'assistant', content: "Erreur réseau. Veuillez réessayer." }]);
    } finally {
      setIsLoading(false);
    }
  };

  const deleteSession = (id) => {
    setSessions(prev => prev.filter(s => s.id !== id));
    if (activeSession?.id === id) {
      setActiveSession(null);
      setMessages([]);
    }
  };

  return (
    <div className="h-screen flex flex-col bg-slate-100">
      {/* Header */}
      <header className="bg-gradient-to-r from-indigo-600 to-blue-600 text-white py-4 px-6 shadow-lg">
        <h1 className="text-2xl font-bold text-center tracking-wide">
          Natural Language to SQL Query
        </h1>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* Left Sidebar */}
        <aside className="w-72 bg-white border-r border-slate-200 flex flex-col">
          <div className="p-4 border-b border-slate-200">
            <h2 className="text-sm font-semibold text-slate-600 uppercase tracking-wider flex items-center gap-2">
              <FileSpreadsheet className="w-4 h-4" />
              Historique des fichiers
            </h2>
          </div>

          <div className="flex-1 overflow-y-auto p-2 space-y-2">
            {sessions.length === 0 ? (
              <p className="text-sm text-slate-400 text-center py-8">
                Aucun fichier chargé
              </p>
            ) : (
              sessions.map(session => (
                <div
                  key={session.id}
                  onClick={() => { setActiveSession(session); setMessages(session.messages || []); setShowPreview(true); }}
                  className={`p-3 rounded-lg cursor-pointer transition-all group ${activeSession?.id === session.id
                    ? 'bg-indigo-50 border border-indigo-200'
                    : 'hover:bg-slate-50 border border-transparent'
                    }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-slate-800 truncate text-sm">{session.filename}</p>
                      <p className="text-xs text-slate-400 mt-1">{session.timestamp}</p>
                    </div>
                    <button
                      onClick={(e) => { e.stopPropagation(); deleteSession(session.id); }}
                      className="opacity-0 group-hover:opacity-100 p-1 text-slate-400 hover:text-red-500 transition-all"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        </aside>

        {/* Main Workspace */}
        <main className="flex-1 flex flex-col overflow-hidden">
          {/* Content Area */}
          <div className="flex-1 overflow-y-auto p-6">
            {!activeSession ? (
              <div className="h-full flex flex-col items-center justify-center text-slate-400">
                <Database className="w-16 h-16 mb-4 opacity-50" />
                <p className="text-lg">Chargez un fichier pour commencer</p>
                <p className="text-sm mt-2">Utilisez le bouton ci-dessous pour ajouter un fichier CSV ou Excel</p>
              </div>
            ) : showPreview && dataPreview ? (
              <div className="space-y-6">
                {/* Summary Cards */}
                {dataSummary && (
                  <div className="grid grid-cols-3 gap-4">
                    <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
                      <p className="text-sm text-slate-500">Table</p>
                      <p className="text-xl font-semibold text-slate-800">{dataSummary.table_name}</p>
                    </div>
                    <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
                      <p className="text-sm text-slate-500">Lignes</p>
                      <p className="text-xl font-semibold text-slate-800">{dataSummary.row_count?.toLocaleString()}</p>
                    </div>
                    <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
                      <p className="text-sm text-slate-500">Colonnes</p>
                      <p className="text-xl font-semibold text-slate-800">{dataSummary.column_count}</p>
                    </div>
                  </div>
                )}

                {/* Data Table */}
                <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
                  <div className="p-4 border-b border-slate-100 bg-slate-50">
                    <h3 className="font-semibold text-slate-800">Aperçu des données</h3>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead className="bg-slate-50 border-b border-slate-100">
                        <tr>
                          {dataPreview.columns?.map((col, idx) => (
                            <th key={idx} className="px-4 py-3 text-left font-medium text-slate-600">{col}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100">
                        {dataPreview.rows?.map((row, rowIdx) => (
                          <tr key={rowIdx} className="hover:bg-slate-50">
                            {row.map((cell, cellIdx) => (
                              <td key={cellIdx} className="px-4 py-3 text-slate-700">
                                {cell !== null ? String(cell) : <span className="text-slate-400 italic">null</span>}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            ) : (
              /* Chat Messages */
              <div className="space-y-4">
                {messages.map((msg, idx) => (
                  <div key={idx} className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${msg.role === 'user' ? 'bg-indigo-600' : 'bg-emerald-600'
                      }`}>
                      {msg.role === 'user' ? <User className="w-5 h-5 text-white" /> : <Bot className="w-5 h-5 text-white" />}
                    </div>
                    <div className={`max-w-[70%] rounded-2xl p-4 shadow-sm ${msg.role === 'user'
                      ? 'bg-indigo-600 text-white rounded-tr-none'
                      : 'bg-white text-slate-800 border border-slate-100 rounded-tl-none'
                      }`}>
                      <pre className="whitespace-pre-wrap font-sans text-sm">{msg.content}</pre>
                    </div>
                  </div>
                ))}
                {isLoading && (
                  <div className="flex gap-3">
                    <div className="w-8 h-8 rounded-full bg-emerald-600 flex items-center justify-center">
                      <Bot className="w-5 h-5 text-white" />
                    </div>
                    <div className="bg-white p-4 rounded-2xl rounded-tl-none border border-slate-100 shadow-sm">
                      <div className="flex gap-1">
                        <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce"></div>
                        <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                        <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                      </div>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>
            )}
          </div>

          {/* Bottom Input Area */}
          <div className="p-4 bg-white border-t border-slate-200">
            <form onSubmit={handleSubmit} className="flex gap-3 items-center">
              <input type="file" ref={fileInputRef} onChange={handleFileUpload} accept=".csv,.xlsx,.xls" className="hidden" />

              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                className="p-3 rounded-xl bg-slate-100 text-slate-600 hover:bg-slate-200 transition-colors"
                title="Ajouter un fichier"
              >
                <Plus className="w-5 h-5" />
              </button>

              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder={activeSession ? "Posez votre question sur les données..." : "Chargez d'abord un fichier..."}
                className="flex-1 px-4 py-3 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 bg-slate-50 disabled:opacity-50"
                disabled={!activeSession || isLoading}
              />

              <button
                type="submit"
                disabled={!input.trim() || isLoading || !activeSession}
                className="p-3 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors shadow-lg shadow-indigo-600/20"
              >
                {isLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Send className="w-5 h-5" />}
              </button>
            </form>
          </div>
        </main>
      </div>
    </div>
  );
}

export default App;
