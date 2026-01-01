import React, { useState, useEffect } from 'react';
import { Table, Info, Loader2 } from 'lucide-react';

const DataPreview = ({ dbPath }) => {
    const [preview, setPreview] = useState(null);
    const [summary, setSummary] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchData = async () => {
            if (!dbPath) return;

            setLoading(true);
            setError(null);

            try {
                const [previewRes, summaryRes] = await Promise.all([
                    fetch(`http://localhost:8000/data/preview?db_path=${encodeURIComponent(dbPath)}&limit=5`),
                    fetch(`http://localhost:8000/data/summary?db_path=${encodeURIComponent(dbPath)}`)
                ]);

                if (!previewRes.ok || !summaryRes.ok) {
                    throw new Error('Failed to load data');
                }

                setPreview(await previewRes.json());
                setSummary(await summaryRes.json());
            } catch (err) {
                setError(err.message);
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, [dbPath]);

    if (loading) {
        return (
            <div className="flex items-center justify-center p-8">
                <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
                <span className="ml-2 text-slate-600">Loading data preview...</span>
            </div>
        );
    }

    if (error) {
        return (
            <div className="p-4 bg-red-50 text-red-600 rounded-lg">
                Error: {error}
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Summary Cards */}
            {summary && (
                <div className="grid grid-cols-3 gap-4">
                    <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
                        <div className="flex items-center gap-2 text-slate-500 text-sm mb-1">
                            <Table className="w-4 h-4" />
                            Table
                        </div>
                        <p className="text-xl font-semibold text-slate-800">{summary.table_name || 'N/A'}</p>
                    </div>
                    <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
                        <div className="flex items-center gap-2 text-slate-500 text-sm mb-1">
                            <Info className="w-4 h-4" />
                            Rows
                        </div>
                        <p className="text-xl font-semibold text-slate-800">{summary.row_count?.toLocaleString() || 0}</p>
                    </div>
                    <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
                        <div className="flex items-center gap-2 text-slate-500 text-sm mb-1">
                            <Info className="w-4 h-4" />
                            Columns
                        </div>
                        <p className="text-xl font-semibold text-slate-800">{summary.column_count || 0}</p>
                    </div>
                </div>
            )}

            {/* Data Table */}
            {preview && preview.columns?.length > 0 && (
                <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
                    <div className="p-4 border-b border-slate-100 bg-slate-50">
                        <h3 className="font-semibold text-slate-800">Data Preview (First 5 rows)</h3>
                    </div>
                    <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                            <thead className="bg-slate-50 border-b border-slate-100">
                                <tr>
                                    {preview.columns.map((col, idx) => (
                                        <th key={idx} className="px-4 py-3 text-left font-medium text-slate-600">
                                            {col}
                                        </th>
                                    ))}
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-100">
                                {preview.rows.map((row, rowIdx) => (
                                    <tr key={rowIdx} className="hover:bg-slate-50 transition-colors">
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
            )}
        </div>
    );
};

export default DataPreview;
