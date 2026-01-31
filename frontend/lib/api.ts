const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface GenerateRequest {
  company_url: string;
  sender_name: string;
  voice_id: string;
}

export interface GenerateResponse {
  success: boolean;
  research?: {
    company_name: string;
    industry: string;
    description: string;
    key_points: string[];
    pain_points: string[];
  };
  script?: string;
  audio_url?: string;
  video_url?: string;
  error?: string;
}

export interface GenerationStatus {
  step: 'research' | 'script' | 'voice' | 'video' | 'done' | 'error';
  progress: number;
  message: string;
  data?: Partial<GenerateResponse>;
}

export async function generateVideo(
  request: GenerateRequest,
  onProgress?: (status: GenerationStatus) => void
): Promise<GenerateResponse> {
  try {
    // Start generation
    const response = await fetch(`${API_BASE}/api/generate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: 'Request failed' }));
      throw new Error(error.error || `HTTP error ${response.status}`);
    }

    const data = await response.json();
    
    // If the API returns a streaming response or job ID, we'd handle polling here
    // For now, assuming direct response
    return data;
  } catch (error) {
    console.error('Generate video error:', error);
    throw error;
  }
}

// Polling-based status check (if backend supports it)
export async function checkStatus(jobId: string): Promise<GenerationStatus> {
  const response = await fetch(`${API_BASE}/api/status/${jobId}`);
  if (!response.ok) {
    throw new Error('Failed to check status');
  }
  return response.json();
}

// Health check
export async function healthCheck(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE}/api/health`, {
      method: 'GET',
    });
    return response.ok;
  } catch {
    return false;
  }
}

// Voice options
export const VOICE_OPTIONS = [
  { id: 'male-1', name: 'James', gender: 'male', description: 'Professional & confident' },
  { id: 'male-2', name: 'Marcus', gender: 'male', description: 'Warm & friendly' },
  { id: 'female-1', name: 'Sarah', gender: 'female', description: 'Energetic & dynamic' },
  { id: 'female-2', name: 'Emma', gender: 'female', description: 'Calm & trustworthy' },
];
