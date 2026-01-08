import React from 'react';
import { ChevronDown, Bot } from 'lucide-react';

const ModelSelector = ({ provider, setProvider, model, setModel }) => {
    const models = {
        groq: [
            { id: 'llama-3.3-70b-versatile', name: 'Llama 3.3 70B' },
            { id: 'mixtral-8x7b-32768', name: 'Mixtral 8x7B' },
            { id: 'gemma2-9b-it', name: 'Gemma 2 9B' }
        ],
        openai: [
            { id: 'gpt-4o', name: 'GPT-4o' },
            { id: 'gpt-3.5-turbo', name: 'GPT-3.5 Turbo' }
        ],
        gemini: [
            { id: 'gemini-2.0-flash-exp', name: 'Gemini 2.0' },
            { id: 'gemini-1.5-pro', name: 'Gemini 1.5 Pro' }
        ],
        mistral: [
            { id: 'mistral-large-latest', name: 'Mistral Large' },
            { id: 'mistral-small-latest', name: 'Mistral Small' }
        ]
    };

    const currentModels = models[provider] || [];

    return (
        <div className="flex items-center gap-2">
            {/* Provider Selector */}
            <div className="relative group">
                <select
                    value={provider}
                    onChange={(e) => {
                        setProvider(e.target.value);
                        setModel(models[e.target.value][0].id);
                    }}
                    className="appearance-none w-full pl-8 pr-7 py-2 rounded-lg bg-slate-50 text-slate-600 font-medium text-xs hover:bg-slate-100 hover:text-indigo-600 border border-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all cursor-pointer"
                >
                    <option value="groq">Groq</option>
                    <option value="openai">OpenAI</option>
                    <option value="gemini">Gemini</option>
                    <option value="mistral">Mistral</option>
                </select>
                <Bot className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-1/2 -translate-y-1/2 pointer-events-none group-hover:text-indigo-500 transition-colors" />
                <ChevronDown className="w-3 h-3 text-slate-400 absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
            </div>

            {/* Model Selector */}
            <div className="relative group hidden md:block">
                <select
                    value={model}
                    onChange={(e) => setModel(e.target.value)}
                    className="appearance-none w-40 pl-3 pr-7 py-2 rounded-lg bg-slate-50 text-slate-600 font-medium text-xs hover:bg-slate-100 hover:text-indigo-600 border border-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all cursor-pointer truncate"
                >
                    {currentModels.map((m) => (
                        <option key={m.id} value={m.id}>
                            {m.name}
                        </option>
                    ))}
                </select>
                <ChevronDown className="w-3 h-3 text-slate-400 absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
            </div>
        </div>
    );
};

export default ModelSelector;
