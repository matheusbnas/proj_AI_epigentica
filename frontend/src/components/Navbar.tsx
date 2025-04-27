import React from 'react';
import { FileText } from 'lucide-react';

const Navbar: React.FC = () => {
  return (
    <header className="bg-white shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16 items-center">
          <div className="flex items-center">
            <FileText className="h-8 w-8 text-blue-600" />
            <h1 className="ml-2 text-xl font-semibold text-gray-900">
              NutriGen<span className="text-blue-600">Slides</span>
            </h1>
          </div>
          <nav className="flex space-x-4">
            <a href="#" className="text-gray-500 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium">
              Início
            </a>
            <a href="#" className="text-gray-500 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium">
              Como Usar
            </a>
            <a href="#" className="text-gray-500 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium">
              Sobre
            </a>
          </nav>
        </div>
      </div>
    </header>
  );
};

export default Navbar;