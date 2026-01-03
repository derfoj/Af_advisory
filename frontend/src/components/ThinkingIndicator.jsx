import React, { useState, useEffect } from 'react';
import { Loader2, CheckCircle2, Circle, ArrowRight } from 'lucide-react';

const steps = [
    { id: 1, label: "Analyse de la demande..." },
    { id: 2, label: "Exploration du schéma de la base de données..." },
    { id: 3, label: "Génération de la requête SQL..." },
    { id: 4, label: "Exécution et validation..." },
    { id: 5, label: "Finalisation de la réponse..." }
];

const ThinkingIndicator = () => {
    const [currentStep, setCurrentStep] = useState(0);

    useEffect(() => {
        const interval = setInterval(() => {
            setCurrentStep((prev) => (prev < steps.length - 1 ? prev + 1 : prev));
        }, 1500); // Change step every 1.5s to simulate thinking

        return () => clearInterval(interval);
    }, []);

    return (
        <div className="flex gap-3 animate-in fade-in duration-300">
            <div className="w-8 h-8 rounded-full bg-emerald-600 flex items-center justify-center flex-shrink-0 animate-pulse">
                <Loader2 className="w-5 h-5 text-white animate-spin" />
            </div>

            <div className="bg-white p-4 rounded-2xl rounded-tl-none border border-slate-100 shadow-sm min-w-[300px]">
                <h3 className="text-sm font-semibold text-slate-700 mb-3 flex items-center gap-2">
                    <span className="relative flex h-3 w-3">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                        <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
                    </span>
                    Traitement en cours...
                </h3>

                <div className="space-y-3">
                    {steps.map((step, idx) => {
                        const isActive = idx === currentStep;
                        const isCompleted = idx < currentStep;

                        return (
                            <div
                                key={step.id}
                                className={`flex items-center gap-3 text-xs transition-all duration-300 ${isActive ? 'text-indigo-600 scale-105 font-medium' :
                                        isCompleted ? 'text-emerald-600' : 'text-slate-300'
                                    }`}
                            >
                                {isCompleted ? (
                                    <CheckCircle2 className="w-4 h-4" />
                                ) : isActive ? (
                                    <Loader2 className="w-4 h-4 animate-spin" />
                                ) : (
                                    <Circle className="w-4 h-4" />
                                )}
                                <span>{step.label}</span>
                            </div>
                        );
                    })}
                </div>
            </div>
        </div>
    );
};

export default ThinkingIndicator;
