const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface GenerateRequest {
  company_url: string;
  sender_name: string;
  voice_id: string;
}

export interface PersonalizedGenerateRequest {
  company_url: string;
  our_product: string;
  person_image: File;
  voice_sample?: File;
  voice_profile_id?: string;
}

export interface GenerateResponse {
  success: boolean;
  research?: Record<string, unknown>; // Flexible structure from backend
  script?: string;
  audio_url?: string;
  video_url?: string;
  error?: string;
}

export interface GenerationStatus {
  step: 'research' | 'script' | 'voice' | 'video' | 'done' | 'error';
  progress: number;
  message: string;
  // Intermediate results as they become available
  research?: Record<string, unknown>;
  script?: string;
  audio_url?: string;
  video_url?: string;
}

export interface VoiceProfile {
  id: string;
  name: string;
  voice_id: string;
  created_at: string;
  audio_duration_estimate?: number;
}

// Map frontend voice IDs to backend voice IDs
const VOICE_ID_MAP: Record<string, string> = {
  'male-1': 'male-qn-qingse',
  'male-2': 'male-qn-jingying',
  'female-1': 'female-shaonv',
  'female-2': 'female-yujie',
};

export async function generateVideo(
  request: GenerateRequest,
  onProgress?: (status: GenerationStatus) => void
): Promise<GenerateResponse> {
  try {
    // Map voice ID
    const backendVoiceId = VOICE_ID_MAP[request.voice_id] || request.voice_id;

    // Start generation
    const response = await fetch(`${API_BASE}/api/generate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        company_url: request.company_url,
        our_product: `AI consulting services from ${request.sender_name}`,
        voice_id: backendVoiceId,
        skip_video: false, // Enable full video generation
      }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: 'Request failed' }));
      throw new Error(error.error || `HTTP error ${response.status}`);
    }

    const data = await response.json();
    const jobId = data.job_id;

    if (!jobId) {
      throw new Error('No job ID returned');
    }

    // Poll for completion
    const result = await pollForCompletion(jobId, onProgress);
    return result;
  } catch (error) {
    console.error('Generate video error:', error);
    throw error;
  }
}

async function pollForCompletion(
  jobId: string,
  onProgress?: (status: GenerationStatus) => void
): Promise<GenerateResponse> {
  const maxAttempts = 360; // 6 minutes max (video takes 3-5 min)
  const pollInterval = 1000; // 1 second

  for (let i = 0; i < maxAttempts; i++) {
    const response = await fetch(`${API_BASE}/api/generate/status/${jobId}`);

    if (!response.ok) {
      throw new Error('Failed to check status');
    }

    const status = await response.json();

    // Map backend status to frontend step
    const stepMap: Record<string, GenerationStatus['step']> = {
      'pending': 'research',
      'researching': 'research',
      'scripting': 'script',
      'generating_voice': 'voice',
      'generating_video': 'video',
      'merging': 'video',
      'completed': 'done',
      'failed': 'error',
    };

    const step = stepMap[status.status] || 'research';

    // Build intermediate results
    const audio_url = status.audio_path
      ? `${API_BASE}/outputs/${status.audio_path.split('/').pop()}`
      : undefined;
    const video_url = status.final_path
      ? `${API_BASE}/outputs/${status.final_path.split('/').pop()}`
      : undefined;

    if (onProgress) {
      onProgress({
        step,
        progress: status.progress,
        message: `${status.status}...`,
        // Pass intermediate results as they become available
        research: status.research || undefined,
        script: status.script || undefined,
        audio_url,
        video_url,
      });
    }

    if (status.status === 'completed') {
      return {
        success: true,
        research: status.research || undefined,
        script: status.script,
        audio_url,
        video_url,
      };
    }

    if (status.status === 'failed') {
      throw new Error(status.error || 'Generation failed');
    }

    await new Promise(resolve => setTimeout(resolve, pollInterval));
  }

  throw new Error('Generation timed out');
}

// Polling-based status check (if backend supports it)
export async function checkStatus(jobId: string): Promise<GenerationStatus> {
  const response = await fetch(`${API_BASE}/api/generate/status/${jobId}`);
  if (!response.ok) {
    throw new Error('Failed to check status');
  }
  return response.json();
}

// Health check
export async function healthCheck(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE}/health`, {
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

// Personalized video generation with face + voice cloning
export async function generatePersonalizedVideo(
  request: PersonalizedGenerateRequest,
  onProgress?: (status: GenerationStatus) => void
): Promise<GenerateResponse> {
  try {
    // Create FormData for file uploads
    const formData = new FormData();
    formData.append('company_url', request.company_url);
    formData.append('our_product', request.our_product);
    formData.append('person_image', request.person_image);

    if (request.voice_sample) {
      formData.append('voice_sample', request.voice_sample);
    } else if (request.voice_profile_id) {
      formData.append('voice_profile_id', request.voice_profile_id);
    }

    // Start personalized generation
    const response = await fetch(`${API_BASE}/api/personalized/generate`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Request failed' }));
      throw new Error(error.detail || `HTTP error ${response.status}`);
    }

    const data = await response.json();
    const jobId = data.job_id;

    if (!jobId) {
      throw new Error('No job ID returned');
    }

    // Poll for completion
    const result = await pollPersonalizedCompletion(jobId, onProgress);
    return result;
  } catch (error) {
    console.error('Generate personalized video error:', error);
    throw error;
  }
}

async function pollPersonalizedCompletion(
  jobId: string,
  onProgress?: (status: GenerationStatus) => void
): Promise<GenerateResponse> {
  const maxAttempts = 600; // 10 minutes max (personalized takes longer)
  const pollInterval = 1000; // 1 second

  for (let i = 0; i < maxAttempts; i++) {
    const response = await fetch(`${API_BASE}/api/personalized/status/${jobId}`);

    if (!response.ok) {
      throw new Error('Failed to check status');
    }

    const status = await response.json();

    // Map backend status to frontend step
    const stepMap: Record<string, GenerationStatus['step']> = {
      'pending': 'research',
      'researching': 'research',
      'scripting': 'script',
      'cloning_voice': 'voice',
      'generating_voice': 'voice',
      'uploading_image': 'video',
      'generating_video': 'video',
      'merging': 'video',
      'completed': 'done',
      'failed': 'error',
    };

    const step = stepMap[status.status] || 'research';

    // Build intermediate results
    const audio_url = status.audio_path
      ? `${API_BASE}/outputs/${status.audio_path.split('/').pop()}`
      : undefined;
    const video_url = status.final_path
      ? `${API_BASE}/outputs/${status.final_path.split('/').pop()}`
      : undefined;

    if (onProgress) {
      onProgress({
        step,
        progress: status.progress,
        message: `${status.status}...`,
        // Pass intermediate results as they become available
        research: status.research || undefined,
        script: status.script || undefined,
        audio_url,
        video_url,
      });
    }

    if (status.status === 'completed') {
      return {
        success: true,
        research: status.research || undefined,
        script: status.script,
        audio_url,
        video_url,
      };
    }

    if (status.status === 'failed') {
      throw new Error(status.error || 'Generation failed');
    }

    await new Promise(resolve => setTimeout(resolve, pollInterval));
  }

  throw new Error('Generation timed out');
}

// Voice profile management
export async function getVoiceProfiles(): Promise<VoiceProfile[]> {
  const response = await fetch(`${API_BASE}/api/voice/profiles`);
  if (!response.ok) {
    throw new Error('Failed to fetch voice profiles');
  }
  const data = await response.json();
  return data.profiles || [];
}

export async function cloneVoice(audio: File, name: string): Promise<VoiceProfile> {
  const formData = new FormData();
  formData.append('audio', audio);
  formData.append('name', name);

  const response = await fetch(`${API_BASE}/api/voice/clone`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Clone failed' }));
    throw new Error(error.detail || 'Voice cloning failed');
  }

  const data = await response.json();
  return {
    id: data.profile_id,
    name: data.name,
    voice_id: data.voice_id,
    created_at: new Date().toISOString(),
  };
}

export async function deleteVoiceProfile(profileId: string): Promise<void> {
  const response = await fetch(`${API_BASE}/api/voice/profiles/${profileId}`, {
    method: 'DELETE',
  });

  if (!response.ok) {
    throw new Error('Failed to delete voice profile');
  }
}
