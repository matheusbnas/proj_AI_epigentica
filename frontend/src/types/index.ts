// Define types for slide data
export interface SlideData {
  id: string;
  title: string;
  content: string;
  images?: ImageData[];
  chatbotEnabled?: boolean;
}

export interface ImageData {
  id: string;
  url?: string;
  position: {
    top: number;
    left: number;
    width: number;
    height: number;
  };
}

export interface SlideSection {
  title: string;
  content: string;
  slides: SlideData[];
}

export interface TableData {
  headers: string[];
  rows: string[][];
}

export interface ChatMessage {
  id: string;
  sender: 'user' | 'bot';
  text: string;
  timestamp: Date;
}

// Define types for the structured JSON data
export interface StructuredData {
  arquivo: string;
  data_processamento: string;
  paginas: PageData[];
}

export interface PageData {
  numero: number;
  texto: string;
  imagens: ImageData[];
}

export interface ImagePosition {
  top_left_x: number;
  top_left_y: number;
  bottom_right_x: number;
  bottom_right_y: number;
}

export interface ProcessStatus {
  status: string;
  progress: number;
  stage: string;
  message?: string;
  result?: any;
}