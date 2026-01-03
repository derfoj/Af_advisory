import React, { useState, useRef, useEffect } from 'react';
import { Database, Send, Plus, Loader2, Upload } from 'lucide-react';
import { Toaster, toast } from 'sonner';

import Sidebar from './components/Sidebar';
import ChatMessage from './components/ChatMessage';
import DataPreview from './components/DataPreview';
import ThinkingIndicator from './components/ThinkingIndicator';
import SuggestionChips from './components/SuggestionChips';

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

  useEffect(scrollToBottom, [messages, isLoading]); // Scroll on loading state change too (for thinking indicator)

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
      toast.error("Impossible de charger l'aperçu des données.");
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const toastId = toast.loading("Chargement du fichier...");
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
        toast.success("Fichier importé avec succès !", { id: toastId });
      } else {
        throw new Error("Upload failed");
      }
    } catch (err) {
      console.error('Upload failed:', err);
      toast.error("Échec de l'importation du fichier.", { id: toastId });
    } finally {
      setIsLoading(false);
    }
  };

  const handleSuggestionSelect = (suggestion) => {
    setInput(suggestion);
    // Optional: Auto-submit needed? Let's just fill input for now so user can confirm.
    // handleSubmit(new Event('submit')); 
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim() || isLoading || !activeSession) return;

    const userMessage = { role: 'user', content: { text: input } };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);
    setShowPreview(false);

    try {
      const response = await fetch('http://localhost:8000/query/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: userMessage.content.text,
          db_path: activeSession.dbPath,
          chat_history: messages.map(m => {
            if (typeof m.content === 'string') return { role: m.role, content: m.content };

            let textContent = m.content.text || m.content.intro || "";
            if (m.content.process?.sql) {
              textContent += `\nSQL: ${m.content.process.sql}`;
            }
            if (m.content.data?.rows) {
              textContent += `\n(Returned ${m.content.data.rows.length} rows)`;
            }
            return { role: m.role, content: textContent };
          })
        }),
      });

      const rawData = await response.json();

      let assistantMessage = {
        role: 'assistant',
        content: {
          intro: "Voici les résultats de votre requête :",
          data: null,
          process: null,
          error: null
        }
      };

      if (rawData.result) {
        // Handle Data
        if (rawData.result.data) {
          const columns = rawData.result.columns || Object.keys(rawData.result.data[0] || {});
          const rows = rawData.result.data.map(row => columns.map(col => row[col]));

          assistantMessage.content.data = { columns, rows };

          if (rows.length === 1 && columns.length === 1) {
            assistantMessage.content.intro = `Le résultat est : ${rows[0][0]}`;
          } else {
            assistantMessage.content.intro = `J'ai trouvé ${rows.length} résultats correspondants :`;
          }

          // Override intro if the backend provided a specific explanation
          if (rawData.result.message) {
            assistantMessage.content.intro = rawData.result.message;
          }

        } else if (rawData.result.message) {
          assistantMessage.content.intro = rawData.result.message;
        }

        // Handle Process (SQL)
        if (rawData.sql) {
          assistantMessage.content.process = {
            sql: rawData.sql,
            schema_summary: "Table principale"
          };
        }

      } else if (rawData.error) {
        assistantMessage.content.error = rawData.error;
        assistantMessage.content.intro = "Je n'ai pas pu exécuter cette requête.";
      }

      setMessages(prev => [...prev, assistantMessage]);

    } catch (error) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: { error: "Erreur de communication avec le serveur.", intro: "Oups !" }
      }]);
      toast.error("Erreur de connexion au serveur.");
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
    toast.info("Session supprimée.");
  };

  return (
    <div className="h-screen flex flex-col bg-slate-50 font-sans">
      <Toaster position="top-right" richColors />

      {/* Header */}
      <header className="bg-white border-b border-slate-200 py-3 px-6 flex items-center justify-between sticky top-0 z-10">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center shadow-lg shadow-indigo-200">
            <Database className="w-5 h-5 text-white" />
          </div>
          <h1 className="text-lg font-bold text-slate-800 tracking-tight">
            AF-Advisory <span className="text-slate-400 font-normal text-xs ml-2">NL2SQL Assistant</span>
          </h1>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        <Sidebar
          sessions={sessions}
          activeSession={activeSession}
          setActiveSession={setActiveSession}
          setMessages={setMessages}
          setShowPreview={setShowPreview}
          deleteSession={deleteSession}
        />

        {/* Main Workspace */}
        <main className="flex-1 flex flex-col overflow-hidden bg-slate-50/50 relative">

          {/* Content Area */}
          <div className="flex-1 overflow-y-auto p-4 md:p-8 scroll-smooth">
            {!activeSession ? (
              <div className="h-full flex flex-col items-center justify-center text-slate-400 space-y-4 animate-in fade-in duration-500">
                <div className="w-20 h-20 bg-white rounded-3xl flex items-center justify-center shadow-xl shadow-slate-200 mb-4 border border-slate-100">
                  <Upload className="w-10 h-10 text-indigo-500" />
                </div>
                <h3 className="text-xl font-semibold text-slate-700">Aucun fichier sélectionné</h3>
                <p className="text-sm text-slate-400 max-w-md text-center">
                  Importez un fichier CSV ou Excel via la barre latérale ou le bouton ci-dessous pour commencer l'analyse.
                </p>
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="mt-4 px-6 py-2 bg-indigo-600 text-white rounded-full hover:bg-indigo-700 transition-all shadow-lg shadow-indigo-200 font-medium text-sm flex items-center gap-2"
                >
                  <Plus className="w-4 h-4" /> Sélectionner un fichier
                </button>
              </div>
            ) : showPreview ? (
              <DataPreview dataPreview={dataPreview} dataSummary={dataSummary} />
            ) : (
              /* Chat Messages */
              <div className="space-y-8 max-w-4xl mx-auto pb-12">
                {messages.map((msg, idx) => (
                  <ChatMessage key={idx} message={msg} />
                ))}

                {isLoading && (
                  <div className="pl-2">
                    <ThinkingIndicator />
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>
            )}
          </div>

          {/* Bottom Input Area */}
          <div className="p-4 bg-white border-t border-slate-200 shadow-[0_-4px_6px_-1px_rgba(0,0,0,0.02)] z-20">
            <div className="max-w-4xl mx-auto space-y-4">

              {/* Suggestions (Only show when not loading and session active) */}
              {!isLoading && activeSession && messages.length === 0 && (
                <SuggestionChips onSelect={(text) => setInput(text)} />
              )}

              <form onSubmit={handleSubmit} className="flex gap-3 items-center relative">
                <input type="file" ref={fileInputRef} onChange={handleFileUpload} accept=".csv,.xlsx,.xls" className="hidden" />

                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  className="p-3 rounded-xl bg-slate-50 text-slate-500 hover:bg-slate-100 hover:text-indigo-600 transition-all border border-slate-200"
                  title="Ajouter un nouveau fichier"
                >
                  <Plus className="w-5 h-5" />
                </button>

                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder={activeSession ? "Posez votre question (ex: 'Top 5 des ventes')..." : "Chargez d'abord un fichier..."}
                  className="flex-1 px-5 py-3.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 bg-white shadow-sm text-slate-700 placeholder:text-slate-400 transition-all"
                  disabled={!activeSession || isLoading}
                />

                <button
                  type="submit"
                  disabled={!input.trim() || isLoading || !activeSession}
                  className="absolute right-2 p-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-md shadow-indigo-200"
                >
                  {isLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Send className="w-5 h-5" />}
                </button>
              </form>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}

export default App;
