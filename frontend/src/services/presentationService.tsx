import { SlideData } from '../types';

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