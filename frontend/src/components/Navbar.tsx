import React from 'react';
import { FileText, BarChart2, Settings } from 'lucide-react';

const Navbar: React.FC = () => {
  return (
    <nav className="bg-white shadow-sm">
      <div className="max-w-7xl mx-auto px-4 py-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <FileText className="h-8 w-8 text-blue-600" />
            <h1 className="text-2xl font-bold text-gray-900">
              Análise Genética
            </h1>
          </div>
          <div className="flex space-x-6">
            <a href="/" className="flex items-center space-x-1 text-gray-700 hover:text-blue-600">
              <FileText className="h-5 w-5" />
              <span>Análises</span>
            </a>
            <a href="/stats" className="flex items-center space-x-1 text-gray-700 hover:text-blue-600">
              <BarChart2 className="h-5 w-5" />
              <span>Estatísticas</span>
            </a>
            <a href="/settings" className="flex items-center space-x-1 text-gray-700 hover:text-blue-600">
              <Settings className="h-5 w-5" />
              <span>Configurações</span>
            </a>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;