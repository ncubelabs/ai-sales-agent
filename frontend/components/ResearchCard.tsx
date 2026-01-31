'use client';

import { useState } from 'react';
import { ChevronDown, ChevronUp, Building2, Target, AlertTriangle, Lightbulb } from 'lucide-react';

// Match the actual backend response structure
interface Research {
  company?: {
    name?: string;
    url?: string;
    tagline?: string;
    overview?: string;
  };
  industry?: {
    primary?: string;
    secondary?: string[];
    market_segment?: string;
  };
  pain_points?: {
    primary?: string;
    secondary?: string[];
    ai_specific?: string;
  };
  ai_opportunities?: {
    immediate?: string;
    strategic?: string;
    specific_use_case?: string;
  };
  outreach_strategy?: {
    opening_hook?: string;
    value_prop_angle?: string;
  };
  // Legacy flat structure support
  company_name?: string;
  description?: string;
  key_points?: string[];
}

interface ResearchCardProps {
  research: Research;
}

export default function ResearchCard({ research }: ResearchCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  // Handle both nested and flat structures
  const companyName = research.company?.name || research.company_name || 'Unknown Company';
  const industry = research.industry?.primary || (typeof research.industry === 'string' ? research.industry : 'Unknown Industry');
  const description = research.company?.overview || research.description || '';

  // Build pain points array from nested structure
  const painPoints: string[] = [];
  if (research.pain_points?.primary) painPoints.push(research.pain_points.primary);
  if (research.pain_points?.secondary) painPoints.push(...research.pain_points.secondary);
  if (research.pain_points?.ai_specific) painPoints.push(`AI Opportunity: ${research.pain_points.ai_specific}`);

  // Build opportunities array
  const opportunities: string[] = [];
  if (research.ai_opportunities?.immediate) opportunities.push(research.ai_opportunities.immediate);
  if (research.ai_opportunities?.strategic) opportunities.push(research.ai_opportunities.strategic);
  if (research.ai_opportunities?.specific_use_case) opportunities.push(research.ai_opportunities.specific_use_case);

  return (
    <div className="card p-4">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between text-left"
      >
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-accent to-accent-light flex items-center justify-center">
            <Building2 className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 className="font-semibold text-white">{companyName}</h3>
            <p className="text-sm text-gray-400">{industry}</p>
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
          {description && (
            <div>
              <p className="text-sm text-gray-300">{description}</p>
            </div>
          )}

          {/* Tagline */}
          {research.company?.tagline && (
            <div className="text-sm text-accent italic">
              "{research.company.tagline}"
            </div>
          )}

          {/* AI Opportunities */}
          {opportunities.length > 0 && (
            <div>
              <div className="flex items-center gap-2 mb-2">
                <Lightbulb className="w-4 h-4 text-green-400" />
                <span className="text-sm font-medium text-white">AI Opportunities</span>
              </div>
              <ul className="space-y-1">
                {opportunities.map((point, index) => (
                  <li key={index} className="flex items-start gap-2 text-sm text-gray-400">
                    <span className="text-green-400 mt-1">•</span>
                    {point}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Pain Points */}
          {painPoints.length > 0 && (
            <div>
              <div className="flex items-center gap-2 mb-2">
                <AlertTriangle className="w-4 h-4 text-yellow-400" />
                <span className="text-sm font-medium text-white">Pain Points to Address</span>
              </div>
              <ul className="space-y-1">
                {painPoints.map((point, index) => (
                  <li key={index} className="flex items-start gap-2 text-sm text-gray-400">
                    <span className="text-yellow-400 mt-1">•</span>
                    {point}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Outreach Strategy */}
          {research.outreach_strategy?.opening_hook && (
            <div>
              <div className="flex items-center gap-2 mb-2">
                <Target className="w-4 h-4 text-blue-400" />
                <span className="text-sm font-medium text-white">Suggested Opening</span>
              </div>
              <p className="text-sm text-gray-400 italic">
                "{research.outreach_strategy.opening_hook}"
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
