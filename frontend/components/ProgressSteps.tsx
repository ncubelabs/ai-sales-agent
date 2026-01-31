'use client';

import { useEffect, useState } from 'react';
import { Check, Search, FileText, Mic, Video, Loader2, Sparkles } from 'lucide-react';

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

// Fun messages for each step
const stepMessages: Record<string, string[]> = {
  research: [
    "Scanning the interwebs...",
    "Reading their website...",
    "Learning about the company...",
    "Gathering intel...",
    "Doing my homework...",
  ],
  script: [
    "Channeling my inner Shakespeare...",
    "Writing your masterpiece...",
    "Crafting the perfect pitch...",
    "Making words do magic...",
    "Putting pen to digital paper...",
  ],
  voice: [
    "Warming up my vocal cords...",
    "Clearing my throat...",
    "Recording the voiceover...",
    "Adding some pizzazz...",
    "Making it sound human...",
  ],
  video: [
    "Lights, camera, AI-ction!",
    "Directing the scene...",
    "This is the fun part...",
    "Creating movie magic...",
    "Rendering pixels with love...",
    "Almost there, promise!",
    "Good things take time...",
    "Making it cinematic...",
    "Adding final touches...",
    "Worth the wait!",
  ],
};

// Robot SVG component
function RobotCharacter({ isActive, currentStep }: { isActive: boolean; currentStep: Step }) {
  const eyeAnimation = isActive ? 'animate-pulse' : '';
  const isVideo = currentStep === 'video';

  return (
    <div className={`relative ${isActive ? 'animate-bounce-slow' : ''}`}>
      <svg
        width="120"
        height="120"
        viewBox="0 0 120 120"
        className={`transition-transform duration-300 ${isActive ? 'scale-110' : 'scale-100'}`}
      >
        {/* Antenna */}
        <line x1="60" y1="15" x2="60" y2="25" stroke="#6366f1" strokeWidth="3" strokeLinecap="round" />
        <circle cx="60" cy="12" r="5" fill="#8b5cf6" className={isActive ? 'animate-ping-slow' : ''} />

        {/* Head */}
        <rect x="30" y="25" width="60" height="45" rx="10" fill="#1a1a25" stroke="#6366f1" strokeWidth="2" />

        {/* Eyes */}
        <circle cx="45" cy="45" r="8" fill="#0a0a0f" />
        <circle cx="75" cy="45" r="8" fill="#0a0a0f" />
        <circle cx="45" cy="45" r="5" fill={isActive ? "#22c55e" : "#6366f1"} className={eyeAnimation} />
        <circle cx="75" cy="45" r="5" fill={isActive ? "#22c55e" : "#6366f1"} className={eyeAnimation} />

        {/* Mouth */}
        <rect x="45" y="55" width="30" height="6" rx="3" fill={isActive ? "#22c55e" : "#6366f1"} className={isActive ? 'animate-pulse' : ''} />

        {/* Body */}
        <rect x="35" y="72" width="50" height="35" rx="8" fill="#1a1a25" stroke="#6366f1" strokeWidth="2" />

        {/* Chest light */}
        <circle cx="60" cy="88" r="8" fill={isActive ? "#8b5cf6" : "#252533"} className={isActive ? 'animate-pulse' : ''} />

        {/* Arms */}
        <rect x="15" y="78" width="18" height="8" rx="4" fill="#1a1a25" stroke="#6366f1" strokeWidth="2" className={isVideo ? 'animate-wave-left' : ''} />
        <rect x="87" y="78" width="18" height="8" rx="4" fill="#1a1a25" stroke="#6366f1" strokeWidth="2" className={isVideo ? 'animate-wave-right' : ''} />
      </svg>

      {/* Sparkles around robot when active */}
      {isActive && (
        <>
          <Sparkles className="absolute -top-2 -left-2 w-5 h-5 text-yellow-400 animate-sparkle" />
          <Sparkles className="absolute -top-2 -right-2 w-5 h-5 text-purple-400 animate-sparkle delay-150" />
          <Sparkles className="absolute -bottom-2 left-4 w-4 h-4 text-blue-400 animate-sparkle delay-300" />
        </>
      )}
    </div>
  );
}

export default function ProgressSteps({ currentStep, message }: ProgressStepsProps) {
  const [funMessage, setFunMessage] = useState('');
  const [dots, setDots] = useState('');

  // Rotate through fun messages
  useEffect(() => {
    if (currentStep === 'idle' || currentStep === 'done' || currentStep === 'error') return;

    const messages = stepMessages[currentStep] || [];
    let index = 0;

    setFunMessage(messages[0] || '');

    const interval = setInterval(() => {
      index = (index + 1) % messages.length;
      setFunMessage(messages[index]);
    }, currentStep === 'video' ? 8000 : 4000); // Slower rotation for video step

    return () => clearInterval(interval);
  }, [currentStep]);

  // Animated dots
  useEffect(() => {
    if (currentStep === 'idle' || currentStep === 'done') return;

    const interval = setInterval(() => {
      setDots(prev => prev.length >= 3 ? '' : prev + '.');
    }, 500);

    return () => clearInterval(interval);
  }, [currentStep]);

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

  const getProgressPercentage = () => {
    const stepOrder = ['research', 'script', 'voice', 'video', 'done'];
    const currentIndex = stepOrder.indexOf(currentStep);
    if (currentStep === 'done') return 100;
    return Math.min(((currentIndex + 1) / (stepOrder.length - 1)) * 100, 100);
  };

  if (currentStep === 'idle') return null;

  const isActive = !['done', 'error', 'idle'].includes(currentStep);

  return (
    <div className="card p-8">
      {/* Robot and message area */}
      <div className="flex flex-col items-center mb-8">
        <RobotCharacter isActive={isActive} currentStep={currentStep} />

        {/* Fun message bubble */}
        <div className="mt-4 px-6 py-3 bg-card-hover rounded-2xl border border-white/10 relative">
          <div className="absolute -top-2 left-1/2 transform -translate-x-1/2 w-4 h-4 bg-card-hover border-l border-t border-white/10 rotate-45" />
          <p className="text-lg font-medium text-white text-center min-w-[200px]">
            {currentStep === 'done' ? (
              <span className="text-green-400">All done! 🎉</span>
            ) : currentStep === 'error' ? (
              <span className="text-red-400">Oops! Something went wrong 😅</span>
            ) : (
              <span className="gradient-text">{funMessage}{dots}</span>
            )}
          </p>
        </div>
      </div>

      {/* Progress bar */}
      <div className="relative mb-6">
        <div className="h-3 bg-card rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-accent via-purple-500 to-accent-light transition-all duration-1000 ease-out relative"
            style={{ width: `${getProgressPercentage()}%` }}
          >
            {/* Animated shine effect */}
            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent animate-shine" />
          </div>
        </div>
        <div className="absolute -right-2 top-1/2 -translate-y-1/2 text-sm font-bold text-accent">
          {Math.round(getProgressPercentage())}%
        </div>
      </div>

      {/* Step indicators */}
      <div className="flex items-center justify-between">
        {steps.map((step, index) => {
          const status = getStepStatus(step.id);
          const Icon = step.icon;

          return (
            <div key={step.id} className="flex items-center flex-1">
              <div className="flex flex-col items-center">
                <div
                  className={`w-12 h-12 rounded-full flex items-center justify-center transition-all duration-300 ${
                    status === 'complete'
                      ? 'bg-green-500 text-white scale-100'
                      : status === 'active'
                      ? 'bg-gradient-to-br from-accent to-purple-500 text-white scale-110 shadow-lg shadow-accent/50'
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
                  className={`mt-2 text-xs font-medium transition-colors ${
                    status === 'active'
                      ? 'text-accent'
                      : status === 'complete'
                      ? 'text-green-400'
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
                        ? 'bg-gradient-to-r from-accent to-purple-500'
                        : 'bg-card'
                    }`}
                  />
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Video step special message */}
      {currentStep === 'video' && (
        <div className="mt-6 text-center">
          <p className="text-sm text-gray-400">
            Video generation takes 3-5 minutes. Grab a coffee! ☕
          </p>
          <div className="mt-2 flex justify-center gap-1">
            {[...Array(5)].map((_, i) => (
              <div
                key={i}
                className="w-2 h-2 bg-accent rounded-full animate-bounce"
                style={{ animationDelay: `${i * 0.15}s` }}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
