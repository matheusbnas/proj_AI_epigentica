import { SlideData, SlideSection } from '../types';

const API_BASE_URL = 'http://localhost:8000';

export const uploadPDFDocument = async (file: File): Promise<{ processId: string }> => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE_URL}/process-pdf`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    throw new Error('Falha ao enviar arquivo');
  }

  return response.json();
};

export const createGooglePresentation = async (slides: SlideData[]): Promise<string> => {
  try {
    // First create slides data
    const createResponse = await fetch(`${API_BASE_URL}/create-google-slides`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ slides }),
    });

    if (!createResponse.ok) {
      throw new Error('Failed to create Google Slides presentation');
    }

    const data = await createResponse.json();
    
    // Add slide ID to URL if present
    let presentationUrl = data.presentation_url;
    if (data.slide_id) {
      presentationUrl += `#slide=id.${data.slide_id}`;
    }
    
    return presentationUrl;
  } catch (error) {
    console.error('Error creating Google Slides:', error);
    throw error;
  }
};

export const loadLocalSlides = async (processId: string): Promise<SlideSection[]> => {
  try {
    // Try to load from local cache first
    const cachedData = localStorage.getItem(`slides_${processId}`);
    if (cachedData) {
      return JSON.parse(cachedData);
    }

    const response = await fetch(`${API_BASE_URL}/slides-data/${processId}`);
    if (!response.ok) {
      throw new Error('Failed to load slides data');
    }
    
    const data = await response.json();
    localStorage.setItem(`slides_${processId}`, JSON.stringify(data));
    return data;
  } catch (error) {
    console.error('Error loading slides:', error);
    throw error;
  }
};

export const createPresentation = async (slides: SlideData[]): Promise<string> => {
  // This would be a real API call to a backend that creates a Google Slides presentation
  // For now, we're simulating this with a timeout
  
  return new Promise((resolve) => {
    setTimeout(() => {
      // Usando o link real da apresentação
      resolve('https://docs.google.com/presentation/d/1JPoTUOgnbHAJfh8kuLzeWtcnwlLzX_QeLCM1wW649T0/edit?slide=id.p#slide=id.p');
    }, 2000);
  });
};

export const uploadJsonToBackend = async (file: File): Promise<{ processId: string }> => {
  // This would be a real API call to upload the JSON file
  // For now, we're simulating this with a timeout
  
  return new Promise((resolve) => {
    setTimeout(() => {
      // Return a mock process ID
      resolve({ processId: 'proc_' + Math.random().toString(36).substr(2, 9) });
    }, 1000);
  });
};

export const checkProcessStatus = async (processId: string): Promise<{
  status: string;
  progress: number;
  message?: string;
  result?: any;
}> => {
  const response = await fetch(`${API_BASE_URL}/process-status/${processId}`);
  if (!response.ok) {
    throw new Error('Falha ao verificar status do processo');
  }
  return response.json();
};