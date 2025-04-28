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

// Função para converter tabela JSON em HTML
const renderTable = (tabela: { cabecalho: string[]; linhas: any[][] }) => {
  return `
    <table class="min-w-full divide-y divide-gray-200 my-4 border">
      <thead>
        <tr>
          ${tabela.cabecalho.map(cell => `<th class="px-4 py-2 bg-gray-100 text-xs font-semibold text-gray-700 border">${cell}</th>`).join('')}
        </tr>
      </thead>
      <tbody>
        ${tabela.linhas.map(linha => `
          <tr>
            ${linha.map(cell => `<td class="px-4 py-2 border">${cell}</td>`).join('')}
          </tr>
        `).join('')}
      </tbody>
    </table>
  `;
};

/**
 * Converte markdown básico (títulos, listas, negrito, itálico, fórmulas, tabelas) em HTML.
 */
function markdownToHtml(text: string): string {
  let html = text;

  // Títulos
  html = html.replace(/^### (.+)$/gm, '<h3 class="text-lg font-semibold mb-2">$1</h3>');
  html = html.replace(/^## (.+)$/gm, '<h2 class="text-xl font-bold mb-3">$1</h2>');
  html = html.replace(/^# (.+)$/gm, '<h1 class="text-2xl font-bold mb-4">$1</h1>');

  // Listas
  html = html.replace(/^\s*-\s(.+)$/gm, '<li>$1</li>');
  html = html.replace(/(<li>.*<\/li>)/gms, '<ul class="list-disc ml-6 mb-2">$1</ul>');

  // Negrito e itálico
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');

  // Fórmulas ($...$)
  html = html.replace(/\$([^\$]+)\$/g, '<span class="text-blue-600">$1</span>');

  // Parágrafos
  html = html.replace(/\n{2,}/g, '</p><p class="mb-4">');
  html = html.replace(/\n/g, '<br />');
  html = `<p class="mb-4">${html}</p>`;

  // Tabelas markdown
  html = html.replace(/((?:\|.*\n)+)/g, (match) => {
    return markdownTableToHtml(match);
  });

  return html;
}

/**
 * Converte uma tabela markdown em HTML estilizado.
 */
function markdownTableToHtml(tableText: string): string {
  const rows = tableText.trim().split('\n').filter(Boolean);
  if (rows.length < 2) return tableText; // Não é tabela válida

  const header = rows[0].split('|').map(cell => cell.trim()).filter(Boolean);
  const aligns = rows[1].split('|').map(cell => cell.trim()).filter(Boolean);
  const bodyRows = rows.slice(2);

  let html = `<table class="min-w-full divide-y divide-gray-200 my-4 border"><thead><tr>`;
  header.forEach(cell => {
    html += `<th class="px-4 py-2 bg-gray-100 text-xs font-semibold text-gray-700 border">${cell}</th>`;
  });
  html += `</tr></thead><tbody>`;
  bodyRows.forEach(row => {
    const cells = row.split('|').map(cell => cell.trim()).filter(Boolean);
    html += `<tr>`;
    cells.forEach(cell => {
      html += `<td class="px-4 py-2 border">${cell}</td>`;
    });
    html += `</tr>`;
  });
  html += `</tbody></table>`;
  return html;
}

export const generateSlidesFromStructuredJSON = (jsonData: any, manualImagesMap?: Record<number, any[]>): any[] => {
  if (!jsonData || !jsonData.paginas) return [];

  const slides: any[] = [];

  // Slide de capa
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

  jsonData.paginas.forEach((pagina: any, idx: number) => {
    let content = '';

    // Título
    if (pagina.titulo) {
      content += `<h2 class="text-2xl font-bold text-blue-800 mb-4">${pagina.titulo}</h2>`;
    }

    // Texto formatado
    if (pagina.texto) {
      content += `<div class="prose prose-lg max-w-none mb-4">${markdownToHtml(pagina.texto)}</div>`;
    }

    // Tabelas JSON (se houver)
    if (pagina.tabelas && pagina.tabelas.length > 0) {
      pagina.tabelas.forEach((tabela: any) => {
        content += renderTable(tabela);
      });
    }

    // Imagens automáticas
    let images = [];
    if (pagina.imagens && pagina.imagens.length > 0) {
      images = [...pagina.imagens];
      content += `<div class="flex flex-wrap gap-4 mt-4">`;
      pagina.imagens.forEach((img: any) => {
        content += `
          <div class="flex flex-col items-center">
            <div class="w-48 h-32 bg-gray-100 rounded flex items-center justify-center text-gray-400">
              <span>Imagem ${img.id}</span>
            </div>
            <div class="text-xs text-gray-500 mt-1">
              (${img.posicao.top_left_x}, ${img.posicao.top_left_y}) - (${img.posicao.bottom_right_x}, ${img.posicao.bottom_right_y})
            </div>
          </div>
        `;
      });
      content += `</div>`;
    }

    // Imagens manuais (adicionadas pelo usuário)
    if (manualImagesMap && manualImagesMap[pagina.numero]) {
      images = images.concat(manualImagesMap[pagina.numero]);
      content += `<div class="flex flex-wrap gap-4 mt-4">`;
      manualImagesMap[pagina.numero].forEach((img: any) => {
        content += `
          <div class="flex flex-col items-center">
            <img src="${img.url}" class="w-48 h-32 object-contain rounded bg-gray-100" alt="Imagem manual" />
            <div class="text-xs text-gray-500 mt-1">
              (Manual)
            </div>
          </div>
        `;
      });
      content += `</div>`;
    }

    slides.push({
      id: `slide-${idx + 1}`,
      content: `<div class="slide-content p-6">${content}</div>`,
      type: 'content',
      images // para SlideContainer exibir
    });
  });

  return slides;
};