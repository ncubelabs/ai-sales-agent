'use client';

import { Check, Search, FileText, Mic, Video, Loader2 } from 'lucide-react';

type Step = 'research' | 'script' | 'voice' | 'video' | 'done' | 'error' | 'idle';

interface ProgressStepsProps {
  currentStep: Step;
  message?: string;
}

const steps = [
  { id: 'research', label: 'Research', icon: Search },
  { id: 'script', label: 'Script', icon: FileText },
  { id: 'voice', label: 'Voice', icon: Mic },
  { id: 'video', label: 'Video', icon: Video },
];

export default function ProgressSteps({ currentStep, message }: ProgressStepsProps) {
  const getStepStatus = (stepId: string) => {
    const stepOrder = ['research', 'script', 'voice', 'video', 'done'];
    const currentIndex = stepOrder.indexOf(currentStep);
    const stepIndex = stepOrder.indexOf(stepId);

    if (currentStep === 'done') return 'complete';
    if (currentStep === 'error') {
      if (stepIndex < currentIndex) return 'complete';
      if (stepIndex === currentIndex) return 'error';
      return 'pending';
    }
    if (stepIndex < currentIndex) return 'complete';
    if (stepIndex === currentIndex) return 'active';
    return 'pending';
  };

  if (currentStep === 'idle') return null;

  return (
    <div className="py-6">
      {/* Progress bar */}
      <div className="flex items-center justify-between mb-4">
        {steps.map((step, index) => {
          const status = getStepStatus(step.id);
          const Icon = step.icon;

          return (
            <div key={step.id} className="flex items-center flex-1">
              <div className="flex flex-col items-center">
                <div
                  className={`w-12 h-12 rounded-full flex items-center justify-center transition-all duration-300 ${
                    status === 'complete'
                      ? 'bg-green-500 text-white'
                      : status === 'active'
                      ? 'btn-gradient text-white glow-accent'
                      : status === 'error'
                      ? 'bg-red-500 text-white'
                      : 'bg-card text-gray-500 border border-white/10'
                  }`}
                >
                  {status === 'complete' ? (
                    <Check className="w-5 h-5" />
                  ) : status === 'active' ? (
                    <Loader2 className="w-5 h-5 animate-spin" />
                  ) : (
                    <Icon className="w-5 h-5" />
                  )}
                </div>
                <span
                  className={`mt-2 text-xs font-medium ${
                    status === 'active' || status === 'complete'
                      ? 'text-white'
                      : 'text-gray-500'
                  }`}
                >
                  {step.label}
                </span>
              </div>
              {index < steps.length - 1 && (
                <div className="flex-1 mx-4">
                  <div
                    className={`h-1 rounded-full transition-all duration-500 ${
                      getStepStatus(steps[index + 1].id) !== 'pending'
                        ? 'bg-gradient-to-r from-accent to-accent-light'
                        : 'bg-card'
                    }`}
                  />
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Status message */}
      {message && (
        <div className="text-center">
          <p className="text-sm text-gray-400 animate-pulse">{message}</p>
        </div>
      )}
    </div>
  );
}
