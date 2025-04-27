import { useState } from 'react';
import { ChevronLeft, ChevronRight, Maximize } from 'lucide-react';

interface LocalSlideViewerProps {
  slides: Array<{
    id: string;
    content: string;
    url?: string;
  }>;
}

const LocalSlideViewer = ({ slides }: LocalSlideViewerProps) => {
  const [currentSlide, setCurrentSlide] = useState(0);
  const [isFullscreen, setIsFullscreen] = useState(false);

  const goToPrevious = () => {
    setCurrentSlide((prev) => (prev > 0 ? prev - 1 : prev));
  };

  const goToNext = () => {
    setCurrentSlide((prev) => (prev < slides.length - 1 ? prev + 1 : prev));
  };

  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      const slideContainer = document.getElementById('slide-container');
      if (slideContainer && slideContainer.requestFullscreen) {
        slideContainer.requestFullscreen().catch((err) => {
          console.error(`Erro ao entrar em modo de tela cheia: ${err.message}`);
        });
      }
    } else {
      if (document.exitFullscreen) {
        document.exitFullscreen();
      }
    }
    setIsFullscreen(!isFullscreen);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLDivElement>) => {
    if (e.key === 'ArrowLeft') {
      goToPrevious();
    } else if (e.key === 'ArrowRight') {
      goToNext();
    } else if (e.key === 'Escape') {
      setIsFullscreen(false);
    }
  };

  if (!slides || slides.length === 0) {
    return (
      <div className="w-full aspect-[16/9] bg-white rounded-lg shadow flex items-center justify-center">
        <p className="text-gray-500">Nenhum slide disponível</p>
      </div>
    );
  }

  return (
    <div 
      id="slide-container"
      className={`relative w-full ${isFullscreen ? 'fixed inset-0 z-50 bg-black' : 'aspect-[16/9]'}`}
      tabIndex={0}
      onKeyDown={handleKeyDown}
    >
      <div 
        className={`
          w-full h-full bg-white rounded-lg shadow overflow-hidden flex flex-col items-center justify-center
          ${isFullscreen ? 'p-8' : ''}
        `}
      >
        <div 
          className="prose max-w-none p-8 overflow-auto max-h-full w-full"
          dangerouslySetInnerHTML={{ __html: slides[currentSlide].content }}
        />
      </div>

      <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2 flex items-center space-x-2 bg-white rounded-full px-4 py-2 shadow">
        <button
          onClick={goToPrevious}
          disabled={currentSlide === 0}
          className={`p-1 rounded-full transition-colors ${
            currentSlide === 0
              ? 'text-gray-300 cursor-not-allowed'
              : 'text-gray-600 hover:bg-gray-100'
          }`}
          aria-label="Slide anterior"
        >
          <ChevronLeft className="h-5 w-5" />
        </button>
        
        <span className="text-sm text-gray-600 min-w-16 text-center">
          {currentSlide + 1} / {slides.length}
        </span>
        
        <button
          onClick={goToNext}
          disabled={currentSlide === slides.length - 1}
          className={`p-1 rounded-full transition-colors ${
            currentSlide === slides.length - 1
              ? 'text-gray-300 cursor-not-allowed'
              : 'text-gray-600 hover:bg-gray-100'
          }`}
          aria-label="Próximo slide"
        >
          <ChevronRight className="h-5 w-5" />
        </button>
      </div>

      <button
        onClick={toggleFullscreen}
        className="absolute top-4 right-4 p-2 bg-white rounded-full shadow hover:bg-gray-100 transition-colors"
        aria-label="Alternar tela cheia"
      >
        <Maximize className="h-5 w-5 text-gray-600" />
      </button>
    </div>
  );
};

export default LocalSlideViewer;