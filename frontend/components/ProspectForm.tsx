'use client';

import { useState } from 'react';
import { Globe, User, Mic, Sparkles, Loader2 } from 'lucide-react';
import { VOICE_OPTIONS, GenerateRequest } from '@/lib/api';

interface ProspectFormProps {
  onSubmit: (data: GenerateRequest) => void;
  isLoading: boolean;
}

export default function ProspectForm({ onSubmit, isLoading }: ProspectFormProps) {
  const [companyUrl, setCompanyUrl] = useState('');
  const [senderName, setSenderName] = useState('');
  const [voiceId, setVoiceId] = useState(VOICE_OPTIONS[0].id);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!companyUrl || !senderName) return;
    
    onSubmit({
      company_url: companyUrl,
      sender_name: senderName,
      voice_id: voiceId,
    });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Company URL Input */}
      <div className="space-y-2">
        <label className="flex items-center gap-2 text-sm font-medium text-gray-300">
          <Globe className="w-4 h-4 text-accent" />
          Company Website
        </label>
        <input
          type="url"
          value={companyUrl}
          onChange={(e) => setCompanyUrl(e.target.value)}
          placeholder="https://example.com"
          className="w-full px-4 py-3 bg-background border border-white/10 rounded-xl text-white placeholder-gray-500 focus:border-accent focus:ring-2 focus:ring-accent/20 transition-all"
          required
          disabled={isLoading}
        />
        <p className="text-xs text-gray-500">We&apos;ll research this company to personalize your outreach</p>
      </div>

      {/* Sender Name Input */}
      <div className="space-y-2">
        <label className="flex items-center gap-2 text-sm font-medium text-gray-300">
          <User className="w-4 h-4 text-accent" />
          Your Name
        </label>
        <input
          type="text"
          value={senderName}
          onChange={(e) => setSenderName(e.target.value)}
          placeholder="John Smith"
          className="w-full px-4 py-3 bg-background border border-white/10 rounded-xl text-white placeholder-gray-500 focus:border-accent focus:ring-2 focus:ring-accent/20 transition-all"
          required
          disabled={isLoading}
        />
      </div>

      {/* Voice Selector */}
      <div className="space-y-2">
        <label className="flex items-center gap-2 text-sm font-medium text-gray-300">
          <Mic className="w-4 h-4 text-accent" />
          Voice
        </label>
        <div className="grid grid-cols-2 gap-3">
          {VOICE_OPTIONS.map((voice) => (
            <button
              key={voice.id}
              type="button"
              onClick={() => setVoiceId(voice.id)}
              disabled={isLoading}
              className={`p-4 rounded-xl border transition-all text-left ${
                voiceId === voice.id
                  ? 'border-accent bg-accent/10 ring-2 ring-accent/30'
                  : 'border-white/10 bg-background hover:border-white/20 hover:bg-white/5'
              }`}
            >
              <div className="flex items-center gap-2">
                <div className={`w-2 h-2 rounded-full ${
                  voice.gender === 'male' ? 'bg-blue-500' : 'bg-pink-500'
                }`} />
                <span className="font-medium text-white">{voice.name}</span>
              </div>
              <p className="text-xs text-gray-400 mt-1">{voice.description}</p>
            </button>
          ))}
        </div>
      </div>

      {/* Submit Button */}
      <button
        type="submit"
        disabled={isLoading || !companyUrl || !senderName}
        className="w-full py-4 px-6 btn-gradient rounded-xl font-semibold text-white flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
      >
        {isLoading ? (
          <>
            <Loader2 className="w-5 h-5 animate-spin" />
            Generating...
          </>
        ) : (
          <>
            <Sparkles className="w-5 h-5" />
            Generate Video
          </>
        )}
      </button>
    </form>
  );
}
