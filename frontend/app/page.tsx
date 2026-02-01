'use client';

import { useState } from 'react';
import { Zap, ArrowRight, User, Sparkles } from 'lucide-react';
import ProspectForm from '@/components/ProspectForm';
import PersonalizedForm from '@/components/PersonalizedForm';
import ProgressSteps from '@/components/ProgressSteps';
import ResearchCard from '@/components/ResearchCard';
import ScriptEditor from '@/components/ScriptEditor';
import AudioPlayer from '@/components/AudioPlayer';
import VideoPlayer from '@/components/VideoPlayer';
import {
  GenerateRequest,
  GenerateResponse,
  generateVideo,
  PersonalizedGenerateRequest,
  generatePersonalizedVideo,
} from '@/lib/api';

type Step = 'research' | 'script' | 'voice' | 'video' | 'done' | 'error' | 'idle';
type Mode = 'standard' | 'personalized';

export default function Home() {
  const [mode, setMode] = useState<Mode>('personalized');
  const [currentStep, setCurrentStep] = useState<Step>('idle');
  const [statusMessage, setStatusMessage] = useState('');
  const [result, setResult] = useState<GenerateResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (data: GenerateRequest) => {
    setIsLoading(true);
    setError(null);
    setResult(null);
    setCurrentStep('research');
    setStatusMessage('Starting pipeline...');

    try {
      const response = await generateVideo(data, (status) => {
        setCurrentStep(status.step);
        const messages: Record<string, string> = {
          'research': 'Analyzing company website...',
          'script': 'Generating personalized script...',
          'voice': 'Creating AI voiceover...',
          'video': 'Generating video...',
          'done': 'Complete!',
        };
        setStatusMessage(messages[status.step] || status.message);

        // Update results incrementally as they become available
        setResult(prev => ({
          success: true,
          research: status.research || prev?.research,
          script: status.script || prev?.script,
          audio_url: status.audio_url || prev?.audio_url,
          video_url: status.video_url || prev?.video_url,
        }));
      });

      if (!response.success) {
        throw new Error(response.error || 'Generation failed');
      }

      setResult(response);
      setCurrentStep('done');
      setStatusMessage('Generation complete!');
    } catch (err) {
      console.error('Generation error:', err);
      setCurrentStep('error');
      setError(err instanceof Error ? err.message : 'Something went wrong');
      setStatusMessage('Generation failed');
    } finally {
      setIsLoading(false);
    }
  };

  const handlePersonalizedSubmit = async (data: PersonalizedGenerateRequest) => {
    setIsLoading(true);
    setError(null);
    setResult(null);
    setCurrentStep('research');
    setStatusMessage('Starting personalized pipeline...');

    try {
      const response = await generatePersonalizedVideo(data, (status) => {
        setCurrentStep(status.step);
        const messages: Record<string, string> = {
          'research': 'Analyzing company website...',
          'script': 'Generating personalized script...',
          'voice': 'Cloning your voice...',
          'video': 'Creating your talking head video...',
          'done': 'Complete!',
        };
        setStatusMessage(messages[status.step] || status.message);

        // Update results incrementally as they become available
        setResult(prev => ({
          success: true,
          research: status.research || prev?.research,
          script: status.script || prev?.script,
          audio_url: status.audio_url || prev?.audio_url,
          video_url: status.video_url || prev?.video_url,
        }));
      });

      if (!response.success) {
        throw new Error(response.error || 'Generation failed');
      }

      setResult(response);
      setCurrentStep('done');
      setStatusMessage('Personalized video complete!');
    } catch (err) {
      console.error('Personalized generation error:', err);
      setCurrentStep('error');
      setError(err instanceof Error ? err.message : 'Something went wrong');
      setStatusMessage('Generation failed');
    } finally {
      setIsLoading(false);
    }
  };

  const handleGenerateAnother = () => {
    setCurrentStep('idle');
    setResult(null);
    setError(null);
    setStatusMessage('');
  };

  return (
    <div className="min-h-screen py-12 px-4">
      <div className="max-w-4xl mx-auto">
        {/* Hero Section */}
        <header className="text-center mb-12">
          {/* Logo/Brand */}
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-card rounded-full mb-6">
            <Zap className="w-5 h-5 text-accent" />
            <span className="text-sm font-medium text-gray-300">NCube Labs</span>
          </div>

          {/* Title */}
          <h1 className="text-5xl md:text-6xl font-bold mb-4">
            <span className="gradient-text">AI Sales Agent</span>
          </h1>

          {/* Tagline */}
          <p className="text-xl text-gray-400 mb-6">
            Personalized video outreach in seconds
          </p>

          {/* Features pill */}
          <div className="inline-flex items-center gap-3 text-sm text-gray-500">
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 bg-green-500 rounded-full" />
              Research
            </span>
            <ArrowRight className="w-4 h-4" />
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 bg-blue-500 rounded-full" />
              Script
            </span>
            <ArrowRight className="w-4 h-4" />
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 bg-purple-500 rounded-full" />
              Voice
            </span>
            <ArrowRight className="w-4 h-4" />
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 bg-pink-500 rounded-full" />
              Video
            </span>
          </div>

          {/* Mode Toggle */}
          {currentStep === 'idle' && (
            <div className="flex justify-center gap-2 mt-8">
              <button
                onClick={() => setMode('standard')}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  mode === 'standard'
                    ? 'bg-accent text-white'
                    : 'bg-white/5 text-gray-400 hover:bg-white/10'
                }`}
              >
                <Sparkles className="w-4 h-4" />
                Standard
              </button>
              <button
                onClick={() => setMode('personalized')}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  mode === 'personalized'
                    ? 'bg-gradient-to-r from-purple-500 to-pink-500 text-white'
                    : 'bg-white/5 text-gray-400 hover:bg-white/10'
                }`}
              >
                <User className="w-4 h-4" />
                Personalized (Your Face + Voice)
              </button>
            </div>
          )}
        </header>

        {/* Main Content */}
        <div className="space-y-8">
          {/* Form Card */}
          {currentStep === 'idle' && (
            <div className={`card p-8 ${mode === 'personalized' ? 'glow-purple' : 'glow-accent'}`}>
              {mode === 'standard' ? (
                <ProspectForm onSubmit={handleSubmit} isLoading={isLoading} />
              ) : (
                <PersonalizedForm onSubmit={handlePersonalizedSubmit} isLoading={isLoading} />
              )}
            </div>
          )}

          {/* Progress Steps */}
          {currentStep !== 'idle' && (
            <ProgressSteps currentStep={currentStep} message={statusMessage} />
          )}

          {/* Error State */}
          {error && (
            <div className="card p-6 border-red-500/50 bg-red-500/10">
              <div className="flex items-start gap-4">
                <div className="w-10 h-10 rounded-full bg-red-500/20 flex items-center justify-center flex-shrink-0">
                  <span className="text-red-400 text-xl">!</span>
                </div>
                <div className="flex-1">
                  <h3 className="font-semibold text-red-400 mb-1">Generation Failed</h3>
                  <p className="text-sm text-gray-400 mb-4">{error}</p>
                  <button
                    onClick={handleGenerateAnother}
                    className="px-4 py-2 text-sm bg-red-500/20 text-red-400 rounded-lg hover:bg-red-500/30 transition-colors"
                  >
                    Try Again
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Intermediate and Final Results */}
          {(result || isLoading) && currentStep !== 'idle' && (
            <div className="space-y-6">
              {/* Research Card - show as soon as available */}
              {result?.research && (
                <div className="animate-in fade-in-0 slide-in-from-bottom-4 duration-500">
                  <ResearchCard research={result.research} />
                </div>
              )}

              {/* Script Editor - show as soon as available */}
              {result?.script && (
                <div className="animate-in fade-in-0 slide-in-from-bottom-4 duration-500">
                  <ScriptEditor script={result.script} readonly />
                </div>
              )}

              {/* Audio Player - show as soon as available */}
              {result?.audio_url && (
                <div className="animate-in fade-in-0 slide-in-from-bottom-4 duration-500">
                  <AudioPlayer src={result.audio_url} title="AI Voiceover" />
                </div>
              )}

              {/* Loading placeholder for next step */}
              {isLoading && !result?.video_url && (
                <div className="card p-6">
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 rounded-lg skeleton" />
                    <div className="flex-1">
                      <div className="w-48 h-4 skeleton rounded mb-2" />
                      <div className="w-32 h-3 skeleton rounded" />
                    </div>
                  </div>
                </div>
              )}

              {/* Video Player - show when complete */}
              {result?.video_url && (
                <div className="animate-in fade-in-0 slide-in-from-bottom-4 duration-500">
                  <VideoPlayer
                    src={result.video_url}
                    title="Your Sales Video"
                    onGenerateAnother={handleGenerateAnother}
                  />
                </div>
              )}

              {/* Generation complete without video */}
              {currentStep === 'done' && !result?.video_url && (
                <div className="card p-6 text-center">
                  <p className="text-gray-400 mb-4">Generation complete but video not available.</p>
                  <button
                    onClick={handleGenerateAnother}
                    className="px-6 py-3 btn-gradient rounded-lg font-medium"
                  >
                    Generate Another
                  </button>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <footer className="mt-16 text-center text-sm text-gray-600">
          <p>Built with ❤️ by NCube Labs • Hackathon 2025</p>
        </footer>
      </div>
    </div>
  );
}
