import React, { useState, useEffect } from 'react';
import { AlertCircle } from 'lucide-react';
import Navbar from './components/Navbar';
import Footer from './components/Footer';
import UploadSection from './components/UploadSection';
import SlideContainer from './components/SlideContainer';
import SlideViewer from './components/SlideViewer';

interface SlideData {
  id: string;
  content: string;
  url?: string;
  presentationUrl?: string;
}

function App() {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [slides, setSlides] = useState<SlideData[]>([]);
  const [currentSlide, setCurrentSlide] = useState(0);
  const [progress, setProgress] = useState(0);
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [presentationUrl, setPresentationUrl] = useState<string | null>(null);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files?.[0]) {
      setFile(event.target.files[0]);
      setError(null);
    }
  };

  const handleUpload = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!file) {
      setError('Por favor, selecione um arquivo PDF');
      return;
    }

    setLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      // Enviar o arquivo para o backend
      const response = await fetch('http://localhost:8000/process-pdf', { // Certifique-se de que o URL está correto
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        throw new Error('Erro ao processar o arquivo');
      }

      const { process_id } = await response.json(); // Obter o process_id do backend

      // Configurar WebSocket para acompanhar o progresso
      const wsUrl = `ws://localhost:8000/ws/${process_id}`;
      const newWs = new WebSocket(wsUrl);
      
      newWs.onerror = (error) => {
        console.error('WebSocket error:', error);
        setError('Erro na conexão WebSocket');
        setLoading(false);
      };

      newWs.onopen = () => {
        console.log('WebSocket conectado');
        setWs(newWs);
      };

      newWs.onmessage = async (event) => {
        const message = JSON.parse(event.data);
        switch (message.type) {
          case 'status':
            setProgress(20);
            break;
          case 'progress':
            setProgress(message.progress);
            if (message.message.includes('JSON encontrados')) {
              // Mostrar mensagem específica quando usar JSON existente
              setError(null);
            }
            break;
          case 'complete':
            setSlides(message.slides);
            setProgress(100);

            // Após o processamento, chamar o endpoint para criar os slides
            try {
              const slidesResponse = await fetch('/create-slides', {
                method: 'POST',
              });

              if (!slidesResponse.ok) {
                throw new Error('Erro ao criar slides');
              }

              const { presentation_url } = await slidesResponse.json();
              setPresentationUrl(presentation_url);
            } catch (err) {
              setError('Erro ao criar slides. Tente novamente.');
            }

            setLoading(false);
            break;
          case 'error':
            setError(message.message);
            setLoading(false);
            break;
        }
      };

      setProgress(50); // Atualizar o progresso inicial
    } catch (err) {
      setError('Erro ao processar o arquivo. Tente novamente.');
      setLoading(false);
      ws?.close();
    }
  };

  useEffect(() => {
    return () => {
      ws?.close();
    };
  }, [ws]);

  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      <Navbar />
      
      <main className="flex-grow">
        <div className="max-w-7xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
          <UploadSection
            fileName={file?.name || 'Selecione um arquivo PDF'}
            handleFileChange={handleFileChange}
            handleUpload={handleUpload}
            loading={loading}
            error={error}
          />

          {loading && (
            <div className="mt-8 bg-white rounded-lg shadow-sm p-6">
              <div className="space-y-4">
                <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-blue-600 transition-all duration-500"
                    style={{ width: `${progress}%` }}
                  />
                </div>
                <p className="text-center text-sm text-gray-600">
                  Processando... {progress}%
                </p>
              </div>
            </div>
          )}

          {presentationUrl && (
            <div className="mt-8">
              <h2 className="text-lg font-bold">Apresentação Gerada</h2>
              <SlideViewer presentationUrl={presentationUrl} />
            </div>
          )}

          {slides.length > 0 && (
            <SlideContainer
              currentSlide={currentSlide}
              totalSlides={slides.length}
              onPrev={() => setCurrentSlide(curr => Math.max(0, curr - 1))}
              onNext={() => setCurrentSlide(curr => Math.min(slides.length - 1, curr + 1))}
            >
              <div className="bg-white rounded-lg shadow-sm p-6">
                {slides[currentSlide].url ? (
                  <img 
                    src={slides[currentSlide].url} 
                    alt={`Slide ${currentSlide + 1}`}
                    className="w-full h-auto"
                  />
                ) : (
                  <div className="prose max-w-none">
                    {slides[currentSlide].content}
                  </div>
                )}
              </div>
            </SlideContainer>
          )}

          {error && (
            <div className="mt-4 p-4 bg-red-50 rounded-md flex items-center space-x-2">
              <AlertCircle className="h-5 w-5 text-red-500" />
              <p className="text-red-700">{error}</p>
            </div>
          )}
        </div>
      </main>

      <Footer />
    </div>
  );
}

export default App;