import React, { useState, useEffect, useCallback } from 'react';
import { AlertCircle, FileText, Loader2 } from 'lucide-react';
import Navbar from './components/Navbar';
import Footer from './components/Footer';
import UploadSection from './components/UploadSection';
import SlideContainer from './components/SlideContainer';
import SlideViewer from './components/SlideViewer';
import { generateSlidesFromStructuredJSON } from './utils/SlideGenerator';

interface SlideData {
  id: string;
  content: string;
  url?: string;
  presentationUrl?: string;
}

interface WebSocketMessage {
  type: 'status' | 'progress' | 'complete' | 'error';
  stage?: keyof typeof PROGRESS_STAGES;
  message?: string;
  slides?: SlideData[];
  presentation_url?: string;
  progress?: number;
}

// Define progress stages
const PROGRESS_STAGES = {
  UPLOADING: { step: 1, progress: 10, message: 'Enviando arquivo...' },
  PROCESSING_PDF: { step: 2, progress: 20, message: 'Processando PDF...' },
  EXTRACTING_TEXT: { step: 3, progress: 30, message: 'Extraindo texto...' },
  CREATING_PRESENTATION: { step: 4, progress: 50, message: 'Criando apresentação...' },
  CREATING_SLIDES: { step: 5, progress: 60, message: 'Criando slides...' },
  POPULATING_SLIDES: { step: 6, progress: 70, message: 'Populando conteúdo...' },
  FORMATTING_CONTENT: { step: 7, progress: 80, message: 'Formatando conteúdo...' },
  FINALIZING: { step: 8, progress: 90, message: 'Finalizando...' },
  COMPLETE: { step: 9, progress: 100, message: 'Processo concluído!' }
};

interface ProcessStatus {
  stage: keyof typeof PROGRESS_STAGES;
  message?: string;
  error?: string;
}

function App() {
  const [file, setFile] = useState<File | null>(null);
  const [fileType, setFileType] = useState<'pdf' | 'json' | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [slides, setSlides] = useState<SlideData[]>([]);
  const [currentSlide, setCurrentSlide] = useState(0);
  const [progress, setProgress] = useState(0);
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [presentationUrl, setPresentationUrl] = useState<string | null>(null);
  const [useLocalViewer, setUseLocalViewer] = useState(true);
  const [processStatus, setProcessStatus] = useState<ProcessStatus>({ stage: 'UPLOADING' });
  const [wsRetries, setWsRetries] = useState(0);
  const [structuredSlides, setStructuredSlides] = useState<any[]>([]);
  const [manualImagesMap, setManualImagesMap] = useState<Record<number, any[]>>({});
  const MAX_RETRIES = 3;

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files?.[0]) {
      const file = event.target.files[0];
      setFile(file);
      setError(null);
      
      // Determine file type
      if (file.name.toLowerCase().endsWith('.pdf')) {
        setFileType('pdf');
      } else if (file.name.toLowerCase().endsWith('.json')) {
        setFileType('json');
        handleJsonFile(file);
      } else {
        setError('Formato de arquivo não suportado. Por favor, selecione um arquivo PDF ou JSON.');
        setFileType(null);
      }
    }
  };

  const handleJsonFile = (file: File) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const jsonData = JSON.parse(e.target?.result as string);
        // Passa manualImagesMap para permitir imagens manuais
        const generatedSlides = generateSlidesFromStructuredJSON(jsonData, manualImagesMap);
        setStructuredSlides(generatedSlides);
        setSlides(generatedSlides);
        setUseLocalViewer(true);
      } catch (err) {
        setError('Erro ao processar o arquivo JSON. Certifique-se de que é um arquivo JSON válido.');
      }
    };
    reader.readAsText(file);
  };

  const handleWebSocketMessage = async (message: WebSocketMessage) => {
    console.log('Mensagem recebida:', message);
    
    try {
      switch (message.type) {
        case 'status':
          if (message.stage && PROGRESS_STAGES[message.stage]) {
            const stage = PROGRESS_STAGES[message.stage];
            setProcessStatus({
              stage: message.stage,
              message: message.message || stage.message
            });
            setProgress(message.progress || stage.progress);
          }
          break;
        
        case 'progress':
          if (message.stage && PROGRESS_STAGES[message.stage]) {
            setProcessStatus({
              stage: message.stage,
              message: message.message || PROGRESS_STAGES[message.stage].message
            });
            setProgress(message.progress || PROGRESS_STAGES[message.stage].progress);
          }
          break;

        case 'complete':
          setProcessStatus({ stage: 'COMPLETE' });
          if (message.slides?.length) {
            setSlides(message.slides);
          }
          if (message.presentation_url) {
            setPresentationUrl(message.presentation_url);
            setUseLocalViewer(false);
            // Add small delay to ensure Google Slides is ready
            await new Promise(resolve => setTimeout(resolve, 2000));
          }
          setProgress(100);
          setLoading(false);
          break;

        case 'error':
          throw new Error(message.message || 'Erro desconhecido no processamento');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Erro desconhecido';
      setError(errorMessage);
      setProcessStatus({
        stage: 'UPLOADING',
        error: errorMessage
      });
      setLoading(false);
    }
  };

  const connectWebSocket = useCallback((processId: string) => {
    const wsUrl = `ws://localhost:8000/ws/${processId}`;
    const newWs = new WebSocket(wsUrl);
    
    newWs.onerror = (error) => {
      console.error('WebSocket error:', error);
      if (wsRetries < MAX_RETRIES) {
        setTimeout(() => {
          setWsRetries(prev => prev + 1);
          connectWebSocket(processId);
        }, 1000 * (wsRetries + 1)); // Exponential backoff
      } else {
        setError('Erro na conexão WebSocket após várias tentativas.');
        setLoading(false);
      }
    };

    newWs.onopen = () => {
      console.log('WebSocket conectado');
      setWs(newWs);
      setWsRetries(0); // Reset retries on successful connection
    };

    newWs.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data) as WebSocketMessage;
        handleWebSocketMessage(message);
      } catch (err) {
        console.error('Erro ao processar mensagem do WebSocket:', err);
        setError('Erro ao processar mensagem do servidor');
        setLoading(false);
        newWs.close();
      }
    };

    newWs.onclose = () => {
      console.log('WebSocket desconectado');
      setWs(null);
    };
  }, [wsRetries]);

  const handleUpload = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!file) {
      setError('Por favor, selecione um arquivo');
      return;
    }

    if (fileType === 'json') {
      // JSON files are processed client-side
      setProcessStatus({ stage: 'COMPLETE' });
      setProgress(100);
      return;
    }

    setLoading(true);
    setError(null);
    setSlides([]);
    setPresentationUrl(null);
    setProcessStatus({ stage: 'UPLOADING' });

    const formData = new FormData();
    formData.append('file', file);

    try {
      // Enviar o arquivo para o backend
      const response = await fetch('http://localhost:8000/process-pdf', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ message: 'Erro ao processar o arquivo' }));
        throw new Error(errorData.message || 'Erro ao processar o arquivo');
      }

      const { process_id } = await response.json();
      connectWebSocket(process_id);
      
      setProgress(50); // Atualizar o progresso inicial
    } catch (err) {
      console.error('Erro ao enviar arquivo:', err);
      if (err instanceof Error) {
        setError(`Erro ao enviar arquivo: ${err.message}`);
      } else {
        setError('Erro ao processar o arquivo. Tente novamente.');
      }
      setLoading(false);
      ws?.close();
    }
  };

  const toggleViewerMode = () => {
    setUseLocalViewer((prev) => !prev);
    // Quando alternar para visualizador local, garanta que os slides locais estejam visíveis
    if (!useLocalViewer && structuredSlides.length > 0) {
      setSlides(structuredSlides);
    }
  };

  useEffect(() => {
    return () => {
      ws?.close();
    };
  }, [ws]);

  const handleSlideChange = (index: number) => {
    setCurrentSlide(index);
  };

  const renderProgress = () => {
    if (!loading) return null;

    const currentStage = PROGRESS_STAGES[processStatus.stage];
    return (
      <div className="mt-8 bg-white rounded-lg shadow-sm p-6">
        <div className="space-y-4">
          <div className="flex items-center space-x-2 mb-2">
            <Loader2 className="h-4 w-4 animate-spin text-blue-600" />
            <span className="text-sm font-medium text-gray-700">
              {processStatus.message || currentStage.message}
            </span>
          </div>
          <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
            <div 
              className="h-full bg-blue-600 transition-all duration-500"
              style={{ width: `${progress}%` }}
            />
          </div>
          <div className="flex justify-between text-xs text-gray-500">
            <span>Progresso: {progress}%</span>
            <span>Etapa {currentStage.step} de {Object.keys(PROGRESS_STAGES).length}</span>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      <Navbar />
      
      <main className="flex-grow">
        <div className="max-w-7xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
          <UploadSection
            fileName={file?.name || 'Selecione um arquivo PDF ou JSON'}
            handleFileChange={handleFileChange}
            handleUpload={handleUpload}
            loading={loading}
            error={error}
            acceptedFileTypes=".pdf,.json"
          />

          {renderProgress()}

          {(presentationUrl || slides.length > 0) && (
            <div className="mt-8">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-lg font-bold">Apresentação Gerada</h2>
                {presentationUrl && (
                  <button
                    onClick={toggleViewerMode}
                    className="text-sm px-3 py-1 bg-blue-100 text-blue-700 rounded-md hover:bg-blue-200 transition-colors"
                  >
                    {useLocalViewer ? 'Usar Visualizador Google' : 'Usar Visualizador Local'}
                  </button>
                )}
              </div>
              
              {presentationUrl && !useLocalViewer ? (
                <SlideViewer presentationUrl={presentationUrl} />
              ) : (
                slides.length > 0 && (
                  <SlideContainer
                    slides={slides}
                    currentSlide={currentSlide}
                    onSlideChange={handleSlideChange}
                    manualImagesMap={manualImagesMap}
                    setManualImagesMap={setManualImagesMap}
                  />
                )
              )}
            </div>
          )}

          {error && (
            <div className="mt-4 p-4 bg-red-50 rounded-md flex items-center space-x-2">
              <AlertCircle className="h-5 w-5 text-red-500" />
              <div className="flex-1">
                <p className="text-red-700">{error}</p>
                {(presentationUrl || slides.length > 0) && (
                  <p className="text-sm text-red-600 mt-1">
                    Ocorreu um erro, mas você ainda pode visualizar os slides gerados.
                  </p>
                )}
              </div>
            </div>
          )}
        </div>
      </main>

      <Footer />
    </div>
  );
}

export default App;