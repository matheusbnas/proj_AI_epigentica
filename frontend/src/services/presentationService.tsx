import { SlideData, SlideSection } from '../types';

export const createGooglePresentation = async (slides: SlideData[]): Promise<string> => {
  try {
    const response = await fetch('http://localhost:8000/create-google-slides', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ slides }),
    });

    if (!response.ok) {
      throw new Error('Failed to create Google Slides presentation');
    }

    const data = await response.json();
    return data.presentationUrl;
  } catch (error) {
    console.error('Error creating Google Slides:', error);
    throw error;
  }
};

export const loadLocalSlides = async (): Promise<SlideSection[]> => {
  try {
    const response = await fetch('http://localhost:8000/slides-data');
    if (!response.ok) {
      throw new Error('Failed to load local slides data');
    }
    return await response.json();
  } catch (error) {
    console.error('Error loading local slides:', error);
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