import React, { useState } from 'react';
import { ChevronLeft, ChevronRight, Maximize, Image, MessageSquare } from 'lucide-react';
import ChatbotPanel from './ChatbotPanel';
import ImageUploadModal from './ImageUploadModal';

interface SlideContainerProps {
  slides: any[];
  currentSlide: number;
  onSlideChange: (index: number) => void;
}

const SlideContainer: React.FC<SlideContainerProps> = ({
  slides,
  currentSlide,
  onSlideChange,
}) => {
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [showChatbot, setShowChatbot] = useState(false);
  const [showImageUpload, setShowImageUpload] = useState(false);
  const [manualImages, setManualImages] = useState<Record<number, any[]>>({});

  const goToPrevious = () => {
    if (currentSlide > 0) {
      onSlideChange(currentSlide - 1);
    }
  };

  const goToNext = () => {
    if (currentSlide < slides.length - 1) {
      onSlideChange(currentSlide + 1);
    }
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

  const toggleChatbot = () => {
    setShowChatbot(!showChatbot);
  };

  const toggleImageUpload = () => {
    setShowImageUpload(!showImageUpload);
  };

  const handleImageUpload = (imageUrl: string, position: { x: number; y: number; width: number; height: number }) => {
    // Adiciona imagem manual ao slide atual
    setManualImages(prev => {
      const idx = currentSlide;
      const arr = prev[idx] || [];
      return {
        ...prev,
        [idx]: [...arr, { id: `manual_${Date.now()}`, url: imageUrl, position }]
      };
    });
    setShowImageUpload(false);
  };

  if (!slides || slides.length === 0) {
    return (
      <div className="w-full aspect-[16/9] bg-white rounded-lg shadow flex items-center justify-center">
        <p className="text-gray-500">Nenhum slide disponível</p>
      </div>
    );
  }

  const slide = slides[currentSlide];
  // Junta imagens automáticas e manuais
  const allImages = [
    ...(slide.images || []),
    ...(manualImages[currentSlide] || [])
  ];

  return (
    <div 
      id="slide-container"
      className={`relative w-full ${isFullscreen ? 'fixed inset-0 z-50 bg-black' : 'aspect-[16/9]'}`}
    >
      <div 
        className={`
          w-full h-full bg-white rounded-lg shadow overflow-hidden flex flex-col items-center justify-center
          ${isFullscreen ? 'p-8' : ''}
        `}
      >
        <div 
          className="prose max-w-none p-8 overflow-auto max-h-full w-full relative"
        >
          <div dangerouslySetInnerHTML={{ __html: slide.content }} />
          
          {/* Render images if they exist */}
          {allImages && allImages.map((image: any) => (
            <div 
              key={image.id}
              className="absolute"
              style={{
                top: `${image.position?.top ?? image.posicao?.top_left_y ?? 0}px`,
                left: `${image.position?.left ?? image.posicao?.top_left_x ?? 0}px`,
                width: `${image.position?.width ?? ((image.posicao?.bottom_right_x ?? 0) - (image.posicao?.top_left_x ?? 0))}px`,
                height: `${image.position?.height ?? ((image.posicao?.bottom_right_y ?? 0) - (image.posicao?.top_left_y ?? 0))}px`
              }}
            >
              <img 
                src={image.url || `https://via.placeholder.com/${image.position?.width || 100}x${image.position?.height || 100}?text=Image`} 
                alt="Slide content"
                className="w-full h-full object-contain"
              />
            </div>
          ))}
        </div>
      </div>

      {/* Slide navigation controls */}
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

      {/* Utility buttons */}
      <div className="absolute top-4 right-4 flex space-x-2">
        <button
          onClick={toggleImageUpload}
          className="p-2 bg-white rounded-full shadow hover:bg-gray-100 transition-colors"
          aria-label="Adicionar imagem"
        >
          <Image className="h-5 w-5 text-gray-600" />
        </button>
        
        <button
          onClick={toggleChatbot}
          className="p-2 bg-white rounded-full shadow hover:bg-gray-100 transition-colors"
          aria-label="Abrir chatbot"
        >
          <MessageSquare className="h-5 w-5 text-gray-600" />
        </button>
        
        <button
          onClick={toggleFullscreen}
          className="p-2 bg-white rounded-full shadow hover:bg-gray-100 transition-colors"
          aria-label="Alternar tela cheia"
        >
          <Maximize className="h-5 w-5 text-gray-600" />
        </button>
      </div>

      {/* Chatbot panel */}
      {showChatbot && (
        <ChatbotPanel 
          slideContent={slide.content} 
          onClose={toggleChatbot} 
        />
      )}

      {/* Image upload modal */}
      {showImageUpload && (
        <ImageUploadModal
          onClose={toggleImageUpload}
          onUpload={handleImageUpload}
          slideWidth={1920} // Default 16:9 slide width
          slideHeight={1080} // Default 16:9 slide height
        />
      )}
    </div>
  );
};

export default SlideContainer;