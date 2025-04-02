import React from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';

interface SlideContainerProps {
  currentSlide: number;
  totalSlides: number;
  onPrev: () => void;
  onNext: () => void;
  children: React.ReactNode;
}

const SlideContainer: React.FC<SlideContainerProps> = ({
  currentSlide,
  totalSlides,
  onPrev,
  onNext,
  children
}) => (
  <div className="mt-8">
    <div className="flex items-center justify-between mb-4">
      <button
        onClick={onPrev}
        disabled={currentSlide === 0}
        className={`p-2 rounded-full transition-colors ${
          currentSlide === 0
            ? 'text-gray-400 cursor-not-allowed'
            : 'text-gray-600 hover:bg-gray-100'
        }`}
      >
        <ChevronLeft className="h-6 w-6" />
      </button>
      
      <span className="text-sm text-gray-600">
        Slide {currentSlide + 1} de {totalSlides}
      </span>
      
      <button
        onClick={onNext}
        disabled={currentSlide === totalSlides - 1}
        className={`p-2 rounded-full transition-colors ${
          currentSlide === totalSlides - 1
            ? 'text-gray-400 cursor-not-allowed'
            : 'text-gray-600 hover:bg-gray-100'
        }`}
      >
        <ChevronRight className="h-6 w-6" />
      </button>
    </div>
    
    {children}
  </div>
);

export default SlideContainer;