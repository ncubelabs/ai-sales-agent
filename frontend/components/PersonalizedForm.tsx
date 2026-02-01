'use client';

import { useState, useRef, useEffect } from 'react';
import { Globe, User, Mic, Sparkles, Loader2, Upload, X, Image as ImageIcon } from 'lucide-react';
import { PersonalizedGenerateRequest, VoiceProfile, getVoiceProfiles } from '@/lib/api';

interface PersonalizedFormProps {
  onSubmit: (data: PersonalizedGenerateRequest) => void;
  isLoading: boolean;
}

export default function PersonalizedForm({ onSubmit, isLoading }: PersonalizedFormProps) {
  const [companyUrl, setCompanyUrl] = useState('');
  const [productDescription, setProductDescription] = useState('');
  const [personImage, setPersonImage] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [voiceSample, setVoiceSample] = useState<File | null>(null);
  const [voiceProfiles, setVoiceProfiles] = useState<VoiceProfile[]>([]);
  const [selectedProfileId, setSelectedProfileId] = useState<string>('');
  const [useNewVoice, setUseNewVoice] = useState(true);

  const imageInputRef = useRef<HTMLInputElement>(null);
  const audioInputRef = useRef<HTMLInputElement>(null);

  // Load saved voice profiles
  useEffect(() => {
    getVoiceProfiles()
      .then(setVoiceProfiles)
      .catch(console.error);
  }, []);

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setPersonImage(file);
      const reader = new FileReader();
      reader.onloadend = () => {
        setImagePreview(reader.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleAudioChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setVoiceSample(file);
    }
  };

  const clearImage = () => {
    setPersonImage(null);
    setImagePreview(null);
    if (imageInputRef.current) {
      imageInputRef.current.value = '';
    }
  };

  const clearAudio = () => {
    setVoiceSample(null);
    if (audioInputRef.current) {
      audioInputRef.current.value = '';
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!companyUrl || !personImage) return;
    if (useNewVoice && !voiceSample) return;
    if (!useNewVoice && !selectedProfileId) return;

    onSubmit({
      company_url: companyUrl,
      our_product: productDescription || 'AI-powered business solutions',
      person_image: personImage,
      voice_sample: useNewVoice && voiceSample ? voiceSample : undefined,
      voice_profile_id: !useNewVoice ? selectedProfileId : undefined,
    });
  };

  const canSubmit = companyUrl && personImage && (useNewVoice ? voiceSample : selectedProfileId);

  // Validation messages
  const getMissingFields = () => {
    const missing: string[] = [];
    if (!companyUrl) missing.push('Company URL');
    if (!personImage) missing.push('Photo');
    if (useNewVoice && !voiceSample) missing.push('Voice sample');
    if (!useNewVoice && !selectedProfileId) missing.push('Voice profile');
    return missing;
  };

  const missingFields = getMissingFields();

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
      </div>

      {/* Product Description */}
      <div className="space-y-2">
        <label className="flex items-center gap-2 text-sm font-medium text-gray-300">
          <User className="w-4 h-4 text-accent" />
          Your Product/Service
        </label>
        <input
          type="text"
          value={productDescription}
          onChange={(e) => setProductDescription(e.target.value)}
          placeholder="AI consulting services"
          className="w-full px-4 py-3 bg-background border border-white/10 rounded-xl text-white placeholder-gray-500 focus:border-accent focus:ring-2 focus:ring-accent/20 transition-all"
          disabled={isLoading}
        />
        <p className="text-xs text-gray-500">Describe what you&apos;re selling</p>
      </div>

      {/* Person Image Upload */}
      <div className="space-y-2">
        <label className="flex items-center gap-2 text-sm font-medium text-gray-300">
          <ImageIcon className="w-4 h-4 text-accent" />
          Your Photo
        </label>

        {imagePreview ? (
          <div className="relative w-32 h-32 rounded-xl overflow-hidden border border-white/10">
            <img src={imagePreview} alt="Preview" className="w-full h-full object-cover" />
            <button
              type="button"
              onClick={clearImage}
              disabled={isLoading}
              className="absolute top-1 right-1 p-1 bg-black/50 rounded-full hover:bg-black/70 transition-colors"
            >
              <X className="w-4 h-4 text-white" />
            </button>
          </div>
        ) : (
          <div
            onClick={() => !isLoading && imageInputRef.current?.click()}
            className="w-full p-8 border-2 border-dashed border-white/10 rounded-xl text-center cursor-pointer hover:border-accent/50 hover:bg-accent/5 transition-all"
          >
            <Upload className="w-8 h-8 mx-auto mb-2 text-gray-500" />
            <p className="text-sm text-gray-400">Click to upload your photo</p>
            <p className="text-xs text-gray-500 mt-1">JPEG or PNG, min 512x512</p>
          </div>
        )}
        <input
          ref={imageInputRef}
          type="file"
          accept="image/jpeg,image/png"
          onChange={handleImageChange}
          className="hidden"
          disabled={isLoading}
        />
      </div>

      {/* Voice Section */}
      <div className="space-y-4">
        <label className="flex items-center gap-2 text-sm font-medium text-gray-300">
          <Mic className="w-4 h-4 text-accent" />
          Your Voice
        </label>

        {/* Toggle between new voice and saved profile */}
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => setUseNewVoice(true)}
            disabled={isLoading}
            className={`flex-1 py-2 px-4 rounded-lg text-sm font-medium transition-all ${
              useNewVoice
                ? 'bg-accent text-white'
                : 'bg-white/5 text-gray-400 hover:bg-white/10'
            }`}
          >
            Upload New
          </button>
          <button
            type="button"
            onClick={() => setUseNewVoice(false)}
            disabled={isLoading || voiceProfiles.length === 0}
            className={`flex-1 py-2 px-4 rounded-lg text-sm font-medium transition-all ${
              !useNewVoice
                ? 'bg-accent text-white'
                : 'bg-white/5 text-gray-400 hover:bg-white/10'
            } ${voiceProfiles.length === 0 ? 'opacity-50 cursor-not-allowed' : ''}`}
          >
            Saved Voices ({voiceProfiles.length})
          </button>
        </div>

        {useNewVoice ? (
          /* Voice Sample Upload */
          <div>
            {voiceSample ? (
              <div className="flex items-center gap-3 p-4 bg-white/5 rounded-xl border border-white/10">
                <div className="w-10 h-10 rounded-lg bg-accent/20 flex items-center justify-center">
                  <Mic className="w-5 h-5 text-accent" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-white truncate">{voiceSample.name}</p>
                  <p className="text-xs text-gray-500">
                    {(voiceSample.size / 1024 / 1024).toFixed(2)} MB
                  </p>
                </div>
                <button
                  type="button"
                  onClick={clearAudio}
                  disabled={isLoading}
                  className="p-2 hover:bg-white/10 rounded-lg transition-colors"
                >
                  <X className="w-4 h-4 text-gray-400" />
                </button>
              </div>
            ) : (
              <div
                onClick={() => !isLoading && audioInputRef.current?.click()}
                className="w-full p-6 border-2 border-dashed border-white/10 rounded-xl text-center cursor-pointer hover:border-accent/50 hover:bg-accent/5 transition-all"
              >
                <Upload className="w-6 h-6 mx-auto mb-2 text-gray-500" />
                <p className="text-sm text-gray-400">Upload voice sample</p>
                <p className="text-xs text-gray-500 mt-1">MP3, WAV, or M4A (10s-5min)</p>
              </div>
            )}
            <input
              ref={audioInputRef}
              type="file"
              accept="audio/mpeg,audio/wav,audio/mp4,audio/x-m4a"
              onChange={handleAudioChange}
              className="hidden"
              disabled={isLoading}
            />
          </div>
        ) : (
          /* Saved Voice Profiles */
          <div className="grid grid-cols-1 gap-2">
            {voiceProfiles.map((profile) => (
              <button
                key={profile.id}
                type="button"
                onClick={() => setSelectedProfileId(profile.id)}
                disabled={isLoading}
                className={`p-4 rounded-xl border transition-all text-left ${
                  selectedProfileId === profile.id
                    ? 'border-accent bg-accent/10 ring-2 ring-accent/30'
                    : 'border-white/10 bg-background hover:border-white/20 hover:bg-white/5'
                }`}
              >
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-accent/20 flex items-center justify-center">
                    <Mic className="w-4 h-4 text-accent" />
                  </div>
                  <div>
                    <p className="font-medium text-white">{profile.name}</p>
                    <p className="text-xs text-gray-500">
                      Created {new Date(profile.created_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Missing fields warning */}
      {missingFields.length > 0 && (
        <div className="p-3 bg-yellow-500/10 border border-yellow-500/30 rounded-lg">
          <p className="text-sm text-yellow-400">
            Missing required fields: {missingFields.join(', ')}
          </p>
        </div>
      )}

      {/* Submit Button */}
      <button
        type="submit"
        disabled={isLoading || !canSubmit}
        className="w-full py-4 px-6 btn-gradient rounded-xl font-semibold text-white flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
      >
        {isLoading ? (
          <>
            <Loader2 className="w-5 h-5 animate-spin" />
            Generating Personalized Video...
          </>
        ) : (
          <>
            <Sparkles className="w-5 h-5" />
            Generate Personalized Video
          </>
        )}
      </button>

      <p className="text-xs text-gray-500 text-center">
        Your face and voice will be used to create a personalized talking head video
      </p>
    </form>
  );
}
