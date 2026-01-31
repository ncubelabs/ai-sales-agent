'use client';

import { useState } from 'react';
import { Zap, ArrowRight } from 'lucide-react';
import ProspectForm from '@/components/ProspectForm';
import ProgressSteps from '@/components/ProgressSteps';
import ResearchCard from '@/components/ResearchCard';
import ScriptEditor from '@/components/ScriptEditor';
import AudioPlayer from '@/components/AudioPlayer';
import VideoPlayer from '@/components/VideoPlayer';
import { GenerateRequest, GenerateResponse, generateVideo } from '@/lib/api';

type Step = 'research' | 'script' | 'voice' | 'video' | 'done' | 'error' | 'idle';

export default function Home() {
  const [currentStep, setCurrentStep] = useState<Step>('idle');
  const [statusMessage, setStatusMessage] = useState('');
  const [result, setResult] = useState<GenerateResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (data: GenerateRequest) => {
    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      // Simulate step progression (backend will eventually support streaming)
      setCurrentStep('research');
      setStatusMessage('Analyzing company website...');

      const response = await generateVideo(data);

      if (!response.success) {
        throw new Error(response.error || 'Generation failed');
      }

      // Update with results
      setResult(response);
      setCurrentStep('done');
      setStatusMessage('Video generated successfully!');
    } catch (err) {
      console.error('Generation error:', err);
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
        </header>

        {/* Main Content */}
        <div className="space-y-8">
          {/* Form Card */}
          {currentStep === 'idle' && (
            <div className="card p-8 glow-accent">
              <ProspectForm onSubmit={handleSubmit} isLoading={isLoading} />
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

          {/* Loading Skeletons */}
          {isLoading && (
            <div className="space-y-4">
              <div className="card p-4">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 rounded-lg skeleton" />
                  <div className="space-y-2">
                    <div className="w-32 h-4 skeleton rounded" />
                    <div className="w-24 h-3 skeleton rounded" />
                  </div>
                </div>
              </div>
              <div className="card p-4">
                <div className="w-full h-48 skeleton rounded-lg" />
              </div>
            </div>
          )}

          {/* Results */}
          {result && currentStep === 'done' && (
            <div className="space-y-6 animate-in fade-in-0 slide-in-from-bottom-4 duration-500">
              {/* Research Card */}
              {result.research && (
                <ResearchCard research={result.research} />
              )}

              {/* Script Editor */}
              {result.script && (
                <ScriptEditor script={result.script} readonly />
              )}

              {/* Audio Player */}
              {result.audio_url && (
                <AudioPlayer src={result.audio_url} title="AI Voiceover" />
              )}

              {/* Video Player */}
              {result.video_url && (
                <VideoPlayer
                  src={result.video_url}
                  title="Your Sales Video"
                  onGenerateAnother={handleGenerateAnother}
                />
              )}

              {/* No video but generation complete - show generate another */}
              {!result.video_url && (
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
