import React from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';

const SlideContainer = ({ currentSlide, totalSlides, onPrev, onNext, children }) => (
    <div className="slide-container">
        <div className="slide-navigation">
            <button onClick={onPrev} disabled={currentSlide === 0}>
                <ChevronLeft size={24} />
            </button>
            
            <span>Slide {currentSlide + 1} de {totalSlides}</span>
            
            <button onClick={onNext} disabled={currentSlide === totalSlides - 1}>
                <ChevronRight size={24} />
            </button>
        </div>
        
        <div className="slide-content">
            {children}
        </div>
    </div>
);

export default SlideContainer;