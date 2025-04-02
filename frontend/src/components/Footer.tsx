import React from 'react';

const Footer: React.FC = () => {
  const currentYear = new Date().getFullYear();
  
  return (
    <footer className="bg-white border-t">
      <div className="max-w-7xl mx-auto px-4 py-6 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center">
          <p className="text-sm text-gray-500">
            © {currentYear} Análise Genética. Todos os direitos reservados.
          </p>
          <div className="flex space-x-6">
            <a href="/privacy" className="text-sm text-gray-500 hover:text-gray-900">
              Privacidade
            </a>
            <a href="/terms" className="text-sm text-gray-500 hover:text-gray-900">
              Termos
            </a>
            <a href="/contact" className="text-sm text-gray-500 hover:text-gray-900">
              Contato
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;