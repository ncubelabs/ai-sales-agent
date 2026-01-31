'use client';

import { useState } from 'react';
import { ChevronDown, ChevronUp, Building2, Target, AlertTriangle } from 'lucide-react';

interface Research {
  company_name: string;
  industry: string;
  description: string;
  key_points: string[];
  pain_points: string[];
}

interface ResearchCardProps {
  research: Research;
}

export default function ResearchCard({ research }: ResearchCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className="card p-4">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between text-left"
      >
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-gradient-accent flex items-center justify-center">
            <Building2 className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 className="font-semibold text-white">{research.company_name}</h3>
            <p className="text-sm text-gray-400">{research.industry}</p>
          </div>
        </div>
        <div className="flex items-center gap-2 text-gray-400">
          <span className="text-sm">Research Summary</span>
          {isExpanded ? (
            <ChevronUp className="w-5 h-5" />
          ) : (
            <ChevronDown className="w-5 h-5" />
          )}
        </div>
      </button>

      {isExpanded && (
        <div className="mt-4 pt-4 border-t border-white/10 space-y-4 animate-in slide-in-from-top-2">
          {/* Description */}
          <div>
            <p className="text-sm text-gray-300">{research.description}</p>
          </div>

          {/* Key Points */}
          {research.key_points && research.key_points.length > 0 && (
            <div>
              <div className="flex items-center gap-2 mb-2">
                <Target className="w-4 h-4 text-green-400" />
                <span className="text-sm font-medium text-white">Key Points</span>
              </div>
              <ul className="space-y-1">
                {research.key_points.map((point, index) => (
                  <li key={index} className="flex items-start gap-2 text-sm text-gray-400">
                    <span className="text-green-400 mt-1">•</span>
                    {point}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Pain Points */}
          {research.pain_points && research.pain_points.length > 0 && (
            <div>
              <div className="flex items-center gap-2 mb-2">
                <AlertTriangle className="w-4 h-4 text-yellow-400" />
                <span className="text-sm font-medium text-white">Pain Points to Address</span>
              </div>
              <ul className="space-y-1">
                {research.pain_points.map((point, index) => (
                  <li key={index} className="flex items-start gap-2 text-sm text-gray-400">
                    <span className="text-yellow-400 mt-1">•</span>
                    {point}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
