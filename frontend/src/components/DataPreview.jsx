import React from 'react';
import { Table, Info, Loader2 } from 'lucide-react';

const DataPreview = ({ dataPreview, dataSummary }) => {

    // If we are waiting for data
    if (!dataPreview && !dataSummary) {
        return (
            <div className="flex items-center justify-center p-8">
                <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
                <span className="ml-2 text-slate-600">Loading data...</span>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Summary Cards */}
            {dataSummary && (
                <div className="grid grid-cols-3 gap-4">
                    <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm animate-in zoom-in-50 duration-300">
                        <div className="flex items-center gap-2 text-slate-500 text-sm mb-1">
                            <Table className="w-4 h-4" />
                            Table
                        </div>
                        <p className="text-xl font-semibold text-slate-800">{dataSummary.table_name || 'N/A'}</p>
                    </div>
                    <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm animate-in zoom-in-50 duration-300 delay-75">
                        <div className="flex items-center gap-2 text-slate-500 text-sm mb-1">
                            <Info className="w-4 h-4" />
                            Lignes
                        </div>
                        <p className="text-xl font-semibold text-slate-800">{dataSummary.row_count?.toLocaleString() || 0}</p>
                    </div>
                    <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm animate-in zoom-in-50 duration-300 delay-150">
                        <div className="flex items-center gap-2 text-slate-500 text-sm mb-1">
                            <Info className="w-4 h-4" />
                            Colonnes
                        </div>
                        <p className="text-xl font-semibold text-slate-800">{dataSummary.column_count || 0}</p>
                    </div>
                </div>
            )}

            {/* Data Table */}
            {dataPreview && dataPreview.columns?.length > 0 && (
                <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden animate-in slide-in-from-bottom-4 duration-500">
                    <div className="p-4 border-b border-slate-100 bg-slate-50">
                        <h3 className="font-semibold text-slate-800">Aperçu des données (5 premières lignes)</h3>
                    </div>
                    <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                            <thead className="bg-slate-50 border-b border-slate-100">
                                <tr>
                                    {dataPreview.columns.map((col, idx) => (
                                        <th key={idx} className="px-4 py-3 text-left font-medium text-slate-600">
                                            {col}
                                        </th>
                                    ))}
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-100">
                                {dataPreview.rows.map((row, rowIdx) => (
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
