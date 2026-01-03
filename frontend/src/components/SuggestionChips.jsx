import React from 'react';
import { Lightbulb } from 'lucide-react';

const SUGGESTIONS = [
    "Combien y a-t-il de lignes dans ce fichier ?",
    "Montre-moi les 5 premières entrées.",
    "Quel est le résumé de ces données ?",
    "Liste les colonnes disponibles.",
];

const SuggestionChips = ({ onSelect }) => {
    return (
        <div className="flex flex-wrap gap-2 mt-4 animate-in slide-in-from-bottom-4 duration-500">
            <div className="w-full flex items-center gap-2 text-xs text-slate-500 mb-1">
                <Lightbulb className="w-3 h-3 text-yellow-500" />
                Suggestions :
            </div>
            {SUGGESTIONS.map((suggestion, idx) => (
                <button
                    key={idx}
                    onClick={() => onSelect(suggestion)}
                    className="px-3 py-1.5 bg-white border border-slate-200 hover:border-indigo-300 hover:bg-indigo-50 text-slate-600 text-xs rounded-full transition-all shadow-sm"
                >
                    {suggestion}
                </button>
            ))}
        </div>
    );
};

export default SuggestionChips;
