'use client';

import { useRef, useState } from 'react';
import { Play, Pause, Maximize2, Download, Film, RefreshCw } from 'lucide-react';

interface VideoPlayerProps {
  src: string;
  title?: string;
  onGenerateAnother?: () => void;
}

export default function VideoPlayer({ src, title = 'Generated Video', onGenerateAnother }: VideoPlayerProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [showControls, setShowControls] = useState(true);

  const togglePlay = () => {
    const video = videoRef.current;
    if (!video) return;

    if (isPlaying) {
      video.pause();
    } else {
      video.play();
    }
    setIsPlaying(!isPlaying);
  };

  const handleFullscreen = () => {
    const video = videoRef.current;
    if (!video) return;
    
    if (video.requestFullscreen) {
      video.requestFullscreen();
    }
  };

  const handleDownload = async () => {
    try {
      const response = await fetch(src);
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'sales-video.mp4';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Download failed:', error);
      // Fallback: open in new tab
      window.open(src, '_blank');
    }
  };

  return (
    <div className="card overflow-hidden">
      {/* Header */}
      <div className="p-4 border-b border-white/10 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Film className="w-5 h-5 text-accent" />
          <span className="font-medium text-white">{title}</span>
        </div>
        <div className="flex items-center gap-2">
          {onGenerateAnother && (
            <button
              onClick={onGenerateAnother}
              className="flex items-center gap-2 px-4 py-2 text-sm bg-card hover:bg-card-hover rounded-lg transition-colors"
            >
              <RefreshCw className="w-4 h-4" />
              Generate Another
            </button>
          )}
          <button
            onClick={handleDownload}
            className="flex items-center gap-2 px-4 py-2 text-sm btn-gradient rounded-lg"
          >
            <Download className="w-4 h-4" />
            Download
          </button>
        </div>
      </div>

      {/* Video Container */}
      <div 
        className="relative aspect-video bg-black"
        onMouseEnter={() => setShowControls(true)}
        onMouseLeave={() => setShowControls(!isPlaying)}
      >
        <video
          ref={videoRef}
          src={src}
          className="w-full h-full object-contain"
          onEnded={() => setIsPlaying(false)}
          onClick={togglePlay}
          playsInline
        />

        {/* Overlay Controls */}
        {showControls && (
          <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent flex items-center justify-center transition-opacity">
            <button
              onClick={togglePlay}
              className="w-20 h-20 rounded-full bg-white/20 backdrop-blur-sm flex items-center justify-center hover:bg-white/30 transition-all hover:scale-110"
            >
              {isPlaying ? (
                <Pause className="w-10 h-10 text-white" />
              ) : (
                <Play className="w-10 h-10 text-white ml-1" />
              )}
            </button>

            {/* Fullscreen button */}
            <button
              onClick={handleFullscreen}
              className="absolute bottom-4 right-4 w-10 h-10 rounded-lg bg-black/40 backdrop-blur-sm flex items-center justify-center hover:bg-black/60 transition-colors"
            >
              <Maximize2 className="w-5 h-5 text-white" />
            </button>
          </div>
        )}
      </div>

      {/* Success Message */}
      <div className="p-4 bg-green-500/10 border-t border-green-500/20">
        <p className="text-sm text-green-400 text-center">
          ✨ Your personalized video is ready! Download or share it with your prospect.
        </p>
      </div>
    </div>
  );
}
