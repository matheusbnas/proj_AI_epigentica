import React from 'react';

interface SlideViewerProps {
  presentationUrl: string;
}

const SlideViewer: React.FC<SlideViewerProps> = ({ presentationUrl }) => {
  // Extract presentation ID from Google Slides URL
  const getPresentationId = (url: string) => {
    const match = url.match(/\/presentation\/d\/([a-zA-Z0-9-_]+)/);
    return match ? match[1] : '';
  };

  const presentationId = getPresentationId(presentationUrl);
  const embedUrl = `https://docs.google.com/presentation/d/${presentationId}/embed?start=false&loop=false&delayms=3000`;

  return (
    <div className="w-full aspect-[16/9] bg-white rounded-lg shadow overflow-hidden">
      <iframe
        src={embedUrl}
        frameBorder="0"
        width="100%"
        height="100%"
        allowFullScreen
        className="w-full h-full"
      />
    </div>
  );
};

export default SlideViewer;