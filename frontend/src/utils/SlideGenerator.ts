import { SlideSection } from '../types';

export const parseContentForSlide = (content: string): string => {
  // Convert markdown-like content to HTML
  let processedContent = content
    .replace(/# (.+)/g, '<h1 class="text-2xl font-bold mb-4">$1</h1>')
    .replace(/## (.+)/g, '<h2 class="text-xl font-semibold mb-3">$1</h2>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\$(.+?)\$/g, '<span class="text-blue-600">$1</span>')
    .replace(/\n\n/g, '<p class="mb-4"></p>')
    .replace(/\n/g, '<br />');

  // Handle tables
  if (content.includes('|')) {
    const tableRegex = /\|(.+?)\|[\s\S]+?(?=\n\n|\n$|$)/g;
    const tableMatches = content.match(tableRegex);
    
    if (tableMatches) {
      tableMatches.forEach(table => {
        const rows = table.split('\n').filter(Boolean);
        
        let htmlTable = '<table class="min-w-full divide-y divide-gray-200 my-4">';
        
        rows.forEach((row, index) => {
          if (row.trim().startsWith('|') && row.trim().endsWith('|')) {
            const cells = row
              .trim()
              .slice(1, -1)
              .split('|')
              .map(cell => cell.trim());
            
            if (index === 0) {
              // Header row
              htmlTable += '<thead><tr>';
              cells.forEach(cell => {
                htmlTable += `<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">${cell}</th>`;
              });
              htmlTable += '</tr></thead><tbody>';
            } else if (index === 1 && row.includes(':--')) {
              // Alignment row, skip
            } else {
              // Data row
              htmlTable += '<tr>';
              cells.forEach(cell => {
                htmlTable += `<td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${cell}</td>`;
              });
              htmlTable += '</tr>';
            }
          }
        });
        
        htmlTable += '</tbody></table>';
        processedContent = processedContent.replace(table, htmlTable);
      });
    }
  }

  return processedContent;
};

const enhanceContentWithAI = (content: string): string => {
  // Add professional formatting and structure
  // This is a simple example - could be expanded with actual AI processing
  return content
    .replace(/## (.+)/g, '<h2 class="text-2xl font-bold text-blue-800 mb-4 slide-title">$1</h2>')
    .replace(/\| /g, '<div class="table-cell px-4 py-2">')
    .replace(/ \|/g, '</div>')
    .replace(/\|\n/g, '</div></div>\n<div class="table-row">')
    .replace(/\|/g, '<div class="table-row">')
    .replace(/\n\n/g, '</p><p class="mb-4">');
};

export const generateSlidesFromJSON = (data: SlideSection[]): any[] => {
  let slides: any[] = [];

  // Title slide with improved styling
  slides.push({
    id: 'title-slide',
    content: `
      <div class="flex flex-col items-center justify-center h-full bg-gradient-to-br from-blue-50 to-white p-8 rounded-lg">
        <h1 class="text-4xl font-bold text-blue-800 mb-4">PAINEL NUTRIGENÉTICO</h1>
        <h2 class="text-2xl font-medium text-gray-700">Relatório Personalizado</h2>
      </div>
    `,
    type: 'cover'
  });

  // Process each section with AI enhancement
  data.forEach((section, index) => {
    if (!section.title && !section.content) return;

    const enhancedContent = enhanceContentWithAI(section.content);
    const slideContent = `
      <div class="slide-content p-6">
        ${section.title ? 
          `<h2 class="text-2xl font-bold text-blue-800 mb-6 border-b pb-2">${section.title}</h2>` 
          : ''}
        <div class="content prose prose-lg max-w-none">
          ${enhancedContent}
        </div>
      </div>
    `;

    slides.push({
      id: `slide-${index + 1}`,
      content: slideContent,
      type: 'content'
    });

    // Handle images with improved layout
    if (section.images && section.images.length > 0) {
      section.images.forEach((image, imgIndex) => {
        slides.push({
          id: `slide-${index + 1}-image-${imgIndex + 1}`,
          content: `
            <div class="slide-content p-6">
              <h3 class="text-xl font-semibold text-blue-700 mb-4">
                ${section.title} - Visualização ${imgIndex + 1}
              </h3>
              <div class="aspect-video bg-gray-100 rounded-lg flex items-center justify-center">
                <div class="text-gray-500">
                  Imagem ${image.id}
                  <div class="text-sm text-gray-400 mt-2">
                    Posição: (${image.posicao.top_left_x}, ${image.posicao.top_left_y}) - 
                    (${image.posicao.bottom_right_x}, ${image.posicao.bottom_right_y})
                  </div>
                </div>
              </div>
            </div>
          `,
          type: 'image'
        });
      });
    }
  });

  return slides;
};