'use client';

import { FileText, Copy, Check } from 'lucide-react';
import { useState } from 'react';

interface ScriptEditorProps {
  script: string;
  onScriptChange?: (script: string) => void;
  readonly?: boolean;
}

export default function ScriptEditor({ script, onScriptChange, readonly = false }: ScriptEditorProps) {
  const [copied, setCopied] = useState(false);
  const [editedScript, setEditedScript] = useState(script);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(editedScript);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleChange = (value: string) => {
    setEditedScript(value);
    onScriptChange?.(value);
  };

  // Calculate word count
  const wordCount = editedScript.trim().split(/\s+/).filter(Boolean).length;
  const estimatedDuration = Math.ceil(wordCount / 150); // ~150 words per minute

  return (
    <div className="card p-4 space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <FileText className="w-5 h-5 text-accent" />
          <span className="font-medium text-white">Script</span>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-xs text-gray-500">
            {wordCount} words • ~{estimatedDuration} min
          </span>
          <button
            onClick={handleCopy}
            className="flex items-center gap-1 text-sm text-gray-400 hover:text-white transition-colors"
          >
            {copied ? (
              <>
                <Check className="w-4 h-4 text-green-400" />
                <span className="text-green-400">Copied</span>
              </>
            ) : (
              <>
                <Copy className="w-4 h-4" />
                <span>Copy</span>
              </>
            )}
          </button>
        </div>
      </div>

      <textarea
        value={editedScript}
        onChange={(e) => handleChange(e.target.value)}
        readOnly={readonly}
        className={`w-full h-48 p-4 bg-background border border-white/10 rounded-xl text-gray-200 text-sm leading-relaxed resize-none focus:border-accent focus:ring-2 focus:ring-accent/20 transition-all ${
          readonly ? 'cursor-default' : ''
        }`}
        placeholder="Your personalized sales script will appear here..."
      />

      {!readonly && (
        <p className="text-xs text-gray-500">
          ✏️ Feel free to edit the script before generating the video
        </p>
      )}
    </div>
  );
}
