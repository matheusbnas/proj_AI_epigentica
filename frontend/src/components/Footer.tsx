import React from 'react';

const Footer: React.FC = () => {
  return (
    <footer className="bg-white border-t border-gray-200">
      <div className="max-w-7xl mx-auto px-4 py-6 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center">
          <p className="text-sm text-gray-500">
            &copy; {new Date().getFullYear()} NutriGenSlides. Todos os direitos reservados.
          </p>
          <div className="flex space-x-6">
            <a href="#" className="text-gray-400 hover:text-gray-500">
              Termos de Uso
            </a>
            <a href="#" className="text-gray-400 hover:text-gray-500">
              Privacidade
            </a>
            <a href="#" className="text-gray-400 hover:text-gray-500">
              Contato
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;