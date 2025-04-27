import { useState, useEffect } from 'react';
import { AlertCircle, ExternalLink, RefreshCw } from 'lucide-react';

interface SlideViewerProps {
  presentationUrl: string;
}

const SlideViewer = ({ presentationUrl }: SlideViewerProps) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [presentationId, setPresentationId] = useState<string | null>(null);

  useEffect(() => {
    // Reset states when URL changes
    setLoading(true);
    setError(null);
    
    try {
      // Extract presentation ID from Google Slides URL
      const extractId = (url: string) => {
        // Teste diferentes formatos de URL do Google Slides
        const patterns = [
          /\/presentation\/d\/([a-zA-Z0-9-_]+)/,
          /\/presentation\/([a-zA-Z0-9-_]+)/,
          /id=([a-zA-Z0-9-_]+)/
        ];
        
        for (const pattern of patterns) {
          const match = url.match(pattern);
          if (match && match[1]) {
            return match[1];
          }
        }
        
        return null;
      };
      
      const id = extractId(presentationUrl);
      
      if (!id) {
        throw new Error('Não foi possível extrair o ID da apresentação da URL fornecida');
      }
      
      setPresentationId(id);
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Ocorreu um erro desconhecido ao processar a URL da apresentação');
      }
    } finally {
      setLoading(false);
    }
  }, [presentationUrl]);
  
  const handleIframeLoad = () => {
    setLoading(false);
  };
  
  const handleIframeError = () => {
    setLoading(false);
    setError('Erro ao carregar a apresentação. Verifique se a URL está correta e se você tem permissão para acessá-la.');
  };
  
  const retryLoading = () => {
    setLoading(true);
    setError(null);
    // Forçar a re-renderização do iframe
    setPresentationId(null);
    setTimeout(() => {
      const extractId = (url: string) => {
        const match = url.match(/\/presentation\/d\/([a-zA-Z0-9-_]+)/);
        return match ? match[1] : null;
      };
      
      setPresentationId(extractId(presentationUrl));
    }, 500);
  };
  
  if (error) {
    return (
      <div className="w-full aspect-[16/9] bg-white rounded-lg shadow overflow-hidden flex flex-col items-center justify-center p-6 text-center">
        <AlertCircle className="h-12 w-12 text-red-500 mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">Problema ao carregar a apresentação</h3>
        <p className="text-gray-600 mb-4">{error}</p>
        <div className="flex space-x-4">
          <button 
            onClick={retryLoading}
            className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Tentar novamente
          </button>
          
          <a 
            href={presentationUrl} 
            target="_blank" 
            rel="noopener noreferrer"
            className="flex items-center px-4 py-2 bg-gray-100 text-gray-800 rounded-md hover:bg-gray-200 transition-colors"
          >
            <ExternalLink className="h-4 w-4 mr-2" />
            Abrir no navegador
          </a>
        </div>
      </div>
    );
  }
  
  if (loading || !presentationId) {
    return (
      <div className="w-full aspect-[16/9] bg-white rounded-lg shadow overflow-hidden flex items-center justify-center">
        <div className="flex flex-col items-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
          <p className="text-gray-600">Carregando apresentação...</p>
        </div>
      </div>
    );
  }
  
  // Construir a URL de incorporação
  const embedUrl = `https://docs.google.com/presentation/d/${presentationId}/embed?start=false&loop=false&delayms=3000`;
  
  return (
    <div className="w-full flex flex-col">
      <div className="w-full aspect-[16/9] bg-white rounded-lg shadow overflow-hidden">
        <iframe
          src={embedUrl}
          frameBorder="0"
          width="100%"
          height="100%"
          allowFullScreen
          className="w-full h-full"
          onLoad={handleIframeLoad}
          onError={handleIframeError}
        />
      </div>
      
      <div className="flex justify-end mt-2">
        <a 
          href={presentationUrl} 
          target="_blank" 
          rel="noopener noreferrer"
          className="flex items-center text-sm text-blue-600 hover:text-blue-800"
        >
          <ExternalLink className="h-4 w-4 mr-1" />
          Abrir em nova aba
        </a>
      </div>
    </div>
  );
};

export default SlideViewer;