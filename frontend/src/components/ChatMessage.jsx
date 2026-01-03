import React, { useState } from 'react';
import { User, Bot, ChevronDown, ChevronRight, Terminal, BarChart2 } from 'lucide-react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';

const ChatMessage = ({ message }) => {
    const [isProcessOpen, setIsProcessOpen] = useState(false);
    const isUser = message.role === 'user';

    if (isUser) {
        return (
            <div className="flex flex-row-reverse gap-3 animate-in slide-in-from-right-4 duration-300">
                <div className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 bg-indigo-600 shadow-lg shadow-indigo-200">
                    <User className="w-5 h-5 text-white" />
                </div>
                <div className="max-w-[80%] rounded-2xl p-4 shadow-sm bg-indigo-600 text-white rounded-tr-none">
                    <p className="whitespace-pre-wrap font-sans text-sm">{message.content.text || message.content}</p>
                </div>
            </div>
        );
    }

    // Assistant Message Logic
    const { intro, data, process, error } = message.content;

    // Improved heuristic for chart viability:
    // 1. Must have at least 2 columns and 2 rows.
    // 2. The second column (Y-axis candidate) MUST be numeric.
    const hasData = data?.columns?.length >= 2 && data?.rows?.length > 1;
    const isNumericY = hasData && typeof data.rows[0][1] === 'number';

    // Also skip chart if the intro text suggests a simple explanation/list (heuristic)
    // For now, strict numeric check is the best filter.
    const canShowChart = hasData && isNumericY;

    const chartData = canShowChart ? data.rows.slice(0, 10).map(row => {
        let obj = {};
        data.columns.forEach((col, i) => obj[col] = row[i]);
        return obj;
    }) : [];

    return (
        <div className="flex gap-3 animate-in slide-in-from-left-4 duration-300">
            <div className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 bg-emerald-600 shadow-lg shadow-emerald-200">
                <Bot className="w-5 h-5 text-white" />
            </div>
            <div className="flex-1 max-w-[90%] space-y-2">
                <div className="rounded-2xl p-5 shadow-sm bg-white text-slate-800 border border-slate-200 rounded-tl-none space-y-4">

                    {/* 1. Intro Text */}
                    <p className="font-medium text-slate-800">
                        {intro || (error ? "Une erreur est survenue." : "Voici les résultats :")}
                    </p>

                    {/* 2. Data Table / Result / Charts */}
                    {error ? (
                        <div className="p-3 bg-red-50 text-red-700 rounded-lg text-sm border border-red-200">
                            {error}
                        </div>
                    ) : data && data.columns && data.rows ? (
                        <div className="space-y-4">
                            {/* Optional Chart - VERY BASIC IMPLEMENTATION for now */}
                            {canShowChart && (
                                <div className="h-64 w-full bg-slate-50 rounded-lg border border-slate-100 p-2">
                                    <div className="flex items-center gap-2 mb-2 text-xs text-slate-400 uppercase font-bold">
                                        <BarChart2 className="w-3 h-3" /> Visualisation Rapide
                                    </div>
                                    <ResponsiveContainer width="100%" height="90%">
                                        <BarChart data={chartData}>
                                            <CartesianGrid strokeDasharray="3 3" />
                                            {/* Heuristics: XAxis = 1st col, YAxis = 2nd col (if numeric) */}
                                            <XAxis dataKey={data.columns[0]} tick={{ fontSize: 10 }} />
                                            <YAxis tick={{ fontSize: 10 }} />
                                            <Tooltip />
                                            <Bar dataKey={data.columns[1]} fill="#4f46e5" radius={[4, 4, 0, 0]} />
                                        </BarChart>
                                    </ResponsiveContainer>
                                </div>
                            )}

                            {/* Table */}
                            <div className="border border-slate-200 rounded-lg overflow-hidden">
                                <div className="overflow-x-auto">
                                    <table className="w-full text-sm text-left">
                                        <thead className="bg-slate-50 border-b border-slate-200 text-slate-600">
                                            <tr>
                                                {data.columns.map((col, idx) => (
                                                    <th key={idx} className="px-4 py-2 font-semibold whitespace-nowrap">{col}</th>
                                                ))}
                                            </tr>
                                        </thead>
                                        <tbody className="divide-y divide-slate-100">
                                            {data.rows.slice(0, 10).map((row, rIdx) => (
                                                <tr key={rIdx} className="hover:bg-slate-50 transition-colors">
                                                    {row.map((cell, cIdx) => (
                                                        <td key={cIdx} className="px-4 py-2 text-slate-700 whitespace-nowrap">
                                                            {cell !== null ? String(cell) : <span className="text-slate-400 italic">null</span>}
                                                        </td>
                                                    ))}
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                                {data.rows.length > 10 && (
                                    <div className="bg-slate-50 p-2 text-xs text-center text-slate-500 border-t border-slate-200">
                                        Affichage des 10 premières lignes sur {data.rows.length}
                                    </div>
                                )}
                            </div>
                        </div>
                    ) : (
                        <div className="text-slate-500 italic">Aucune donnée à afficher.</div>
                    )}

                </div>

                {/* 3. Collapsible Process View */}
                {process && (
                    <div className="border border-slate-200 rounded-lg bg-slate-50 overflow-hidden">
                        <button
                            onClick={() => setIsProcessOpen(!isProcessOpen)}
                            className="w-full flex items-center gap-2 p-2 text-xs text-slate-500 hover:text-slate-700 hover:bg-slate-100 transition-colors"
                        >
                            {isProcessOpen ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
                            <Terminal className="w-3 h-3" />
                            Voir le processus de raisonnement
                        </button>

                        {isProcessOpen && (
                            <div className="p-3 border-t border-slate-200 space-y-3 animate-in slide-in-from-top-2 duration-200">

                                {process.sql && (
                                    <div>
                                        <p className="text-[10px] uppercase font-bold text-slate-400 mb-1">SQL Généré</p>
                                        <div className="bg-slate-900 rounded-md p-3 overflow-x-auto group relative">
                                            <code className="text-xs font-mono text-emerald-400 whitespace-pre">{process.sql}</code>
                                        </div>
                                    </div>
                                )}

                                {process.schema && (
                                    <div>
                                        <p className="text-[10px] uppercase font-bold text-slate-400 mb-1">Table Utilisée</p>
                                        <code className="text-xs bg-white border border-slate-200 px-1 py-0.5 rounded text-slate-600">
                                            {process.schema_summary || "Schéma complet"}
                                        </code>
                                    </div>
                                )}

                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
};

export default ChatMessage;
