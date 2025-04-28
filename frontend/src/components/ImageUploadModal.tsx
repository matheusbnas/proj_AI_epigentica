import React, { useState, useRef } from 'react';
import { X, Upload, Move } from 'lucide-react';

interface ImageUploadModalProps {
  onClose: () => void;
  onUpload: (imageUrl: string, position: { x: number; y: number; width: number; height: number }) => void;
  slideWidth: number;
  slideHeight: number;
}

const ImageUploadModal: React.FC<ImageUploadModalProps> = ({
  onClose,
  onUpload,
  slideWidth,
  slideHeight
}) => {
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const [position, setPosition] = useState({ x: 100, y: 100, width: 400, height: 300 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [isResizing, setIsResizing] = useState(false);
  const [resizeStart, setResizeStart] = useState({ x: 0, y: 0, width: 0, height: 0 });
  const imageRef = useRef<HTMLDivElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      const reader = new FileReader();
      
      reader.onload = (event) => {
        setSelectedImage(event.target?.result as string);
      };
      
      reader.readAsDataURL(file);
    }
  };

  const handleURLInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSelectedImage(e.target.value);
  };

  const handleDragStart = (e: React.MouseEvent) => {
    setIsDragging(true);
    setDragStart({
      x: e.clientX - position.x,
      y: e.clientY - position.y
    });
  };

  const handleResizeStart = (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsResizing(true);
    setResizeStart({
      x: e.clientX,
      y: e.clientY,
      width: position.width,
      height: position.height
    });
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (isDragging) {
      const newX = Math.max(0, Math.min(e.clientX - dragStart.x, slideWidth - position.width));
      const newY = Math.max(0, Math.min(e.clientY - dragStart.y, slideHeight - position.height));
      
      setPosition(prev => ({
        ...prev,
        x: newX,
        y: newY
      }));
    } else if (isResizing) {
      const deltaX = e.clientX - resizeStart.x;
      const deltaY = e.clientY - resizeStart.y;
      
      // Maintain aspect ratio (optional)
      const aspectRatio = resizeStart.width / resizeStart.height;
      
      const newWidth = Math.max(100, Math.min(resizeStart.width + deltaX, slideWidth - position.x));
      const newHeight = Math.max(100, resizeStart.height + deltaY);
      
      setPosition(prev => ({
        ...prev,
        width: newWidth,
        height: newHeight
      }));
    }
  };

  const handleMouseUp = () => {
    setIsDragging(false);
    setIsResizing(false);
  };

  const handleSubmit = () => {
    if (selectedImage) {
      onUpload(selectedImage, position);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black bg-opacity-50 flex items-center justify-center"
         onMouseMove={isDragging || isResizing ? handleMouseMove : undefined}
         onMouseUp={handleMouseUp}
         onMouseLeave={handleMouseUp}>
      <div className="bg-white rounded-lg shadow-lg w-full max-w-4xl max-h-[90vh] flex flex-col">
        <div className="p-4 border-b border-gray-200 flex justify-between items-center">
          <h3 className="text-lg font-medium">Adicionar Imagem ao Slide</h3>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>
        
        <div className="p-6 flex-1 overflow-auto">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Carregar Imagem
                </label>
                <div className="flex items-center">
                  <label className="w-full flex items-center justify-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 cursor-pointer">
                    <Upload className="h-5 w-5 mr-2" />
                    Selecionar arquivo
                    <input type="file" className="sr-only" onChange={handleFileChange} accept="image/*" />
                  </label>
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  OU URL da Imagem
                </label>
                <input
                  type="text"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="https://exemplo.com/imagem.jpg"
                  onChange={handleURLInput}
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Posição e Dimensões
                </label>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs text-gray-500">X</label>
                    <input
                      type="number"
                      value={position.x}
                      onChange={(e) => setPosition(prev => ({ ...prev, x: Number(e.target.value) }))}
                      className="w-full px-3 py-1 border border-gray-300 rounded-md"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-gray-500">Y</label>
                    <input
                      type="number"
                      value={position.y}
                      onChange={(e) => setPosition(prev => ({ ...prev, y: Number(e.target.value) }))}
                      className="w-full px-3 py-1 border border-gray-300 rounded-md"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-gray-500">Largura</label>
                    <input
                      type="number"
                      value={position.width}
                      onChange={(e) => setPosition(prev => ({ ...prev, width: Number(e.target.value) }))}
                      className="w-full px-3 py-1 border border-gray-300 rounded-md"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-gray-500">Altura</label>
                    <input
                      type="number"
                      value={position.height}
                      onChange={(e) => setPosition(prev => ({ ...prev, height: Number(e.target.value) }))}
                      className="w-full px-3 py-1 border border-gray-300 rounded-md"
                    />
                  </div>
                </div>
              </div>
            </div>
            
            <div className="relative bg-gray-100 border border-gray-300 rounded-md overflow-hidden" style={{ height: '300px' }}>
              <div className="absolute inset-0 flex items-center justify-center">
                {!selectedImage && (
                  <p className="text-gray-500 text-center px-4">
                    Selecione uma imagem para visualizar e posicionar no slide
                  </p>
                )}
                
                {selectedImage && (
                  <div 
                    ref={imageRef}
                    className="absolute cursor-move flex items-center justify-center"
                    style={{
                      left: `${position.x / slideWidth * 100}%`,
                      top: `${position.y / slideHeight * 100}%`,
                      width: `${position.width / slideWidth * 100}%`,
                      height: `${position.height / slideHeight * 100}%`,
                      border: '2px dashed #3B82F6',
                      backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    }}
                    onMouseDown={handleDragStart}
                  >
                    <img 
                      src={selectedImage} 
                      alt="Preview" 
                      className="max-w-full max-h-full object-contain"
                    />
                    <div 
                      className="absolute bottom-0 right-0 w-6 h-6 bg-blue-600 rounded-tl-md flex items-center justify-center cursor-se-resize"
                      onMouseDown={handleResizeStart}
                    >
                      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M22 2L2 22" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                        <path d="M22 13L13 22" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                        <path d="M22 22L22 13L13 22" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                      </svg>
                    </div>
                    <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                      <Move className="h-8 w-8 text-blue-600 opacity-50" />
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
        
        <div className="p-4 border-t border-gray-200 flex justify-end space-x-3">
          <button
            onClick={onClose}
            className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 transition-colors"
          >
            Cancelar
          </button>
          <button
            onClick={handleSubmit}
            disabled={!selectedImage}
            className={`px-4 py-2 rounded-md text-white ${
              !selectedImage ? 'bg-blue-400 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-700'
            } transition-colors`}
          >
            Adicionar Imagem
          </button>
        </div>
      </div>
    </div>
  );
};

export default ImageUploadModal;