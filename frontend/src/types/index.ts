export interface SlideSection {
    type: string;
    title: string;
    content: string;
    images?: {
      id: string;
      posicao: {
        top_left_x: number;
        top_left_y: number;
        bottom_right_x: number;
        bottom_right_y: number;
      };
    }[];
  }
  
  export interface SlideData {
    id: string;
    content: string;
    url?: string;
    presentationUrl?: string;
  }
  
  export interface ProcessStatus {
    status: 'pending' | 'processing' | 'complete' | 'error';
    message?: string;
    processId?: string;
    progress?: number;
  }