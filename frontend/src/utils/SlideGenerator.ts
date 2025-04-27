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

export const generateSlidesFromJSON = (data: SlideSection[]): any[] => {
  let slides: any[] = [];

  // Title slide
  slides.push({
    id: 'title-slide',
    content: `
      <div class="flex flex-col items-center justify-center h-full">
        <h1 class="text-4xl font-bold text-blue-700 mb-4">PAINEL NUTRIGENÉTICO</h1>
        <h2 class="text-2xl font-medium text-gray-700">Relatório Personalizado</h2>
      </div>
    `
  });

  // Process each section into slides
  data.forEach((section, index) => {
    if (!section.title && !section.content) return;

    // Create a slide for this section
    const slideContent = `
      <div class="slide-content">
        ${section.title ? `<h2 class="text-2xl font-bold text-blue-700 mb-4">${section.title}</h2>` : ''}
        <div class="content">
          ${parseContentForSlide(section.content)}
        </div>
      </div>
    `;

    slides.push({
      id: `slide-${index + 1}`,
      content: slideContent
    });

    // If section has images, create additional slides for them
    if (section.images && section.images.length > 0) {
      section.images.forEach((image, imgIndex) => {
        // Here we would normally load and display the image
        // But since we don't have actual image files, we'll create placeholder slides
        slides.push({
          id: `slide-${index + 1}-image-${imgIndex + 1}`,
          content: `
            <div class="slide-content">
              <h3 class="text-xl font-semibold mb-3">Gráfico: ${section.title}</h3>
              <div class="bg-gray-200 rounded-lg flex items-center justify-center" style="height: 300px;">
                <p class="text-gray-500">Imagem ${image.id}</p>
              </div>
            </div>
          `
        });
      });
    }
  });

  // Summary slide
  slides.push({
    id: 'summary-slide',
    content: `
      <div class="flex flex-col items-center justify-center h-full">
        <h2 class="text-3xl font-bold text-blue-700 mb-4">Obrigado</h2>
        <p class="text-xl text-gray-600">Apresentação Concluída</p>
      </div>
    `
  });

  return slides;
};