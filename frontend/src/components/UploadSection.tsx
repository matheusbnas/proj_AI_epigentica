import React from 'react';
import { Upload, File, CheckCircle, Loader2 } from 'lucide-react';

interface UploadSectionProps {
  fileName: string;
  handleFileChange: (event: React.ChangeEvent<HTMLInputElement>) => void;
  handleUpload: (event: React.FormEvent) => void;
  loading: boolean;
  error: string | null;
  progress?: number;
  processingStatus?: string;
}

const UploadSection: React.FC<UploadSectionProps> = ({
  fileName,
  handleFileChange,
  handleUpload,
  loading,
  error,
  progress,
  processingStatus
}) => {
  return (
    <div className="bg-white rounded-lg shadow-sm p-6">
      <div className="text-center mb-6">
        <h2 className="text-2xl font-bold text-gray-900">
          Crie apresentações a partir de relatórios nutrigenéticos
        </h2>
        <p className="mt-2 text-gray-600">
          Faça upload do seu arquivo PDF para gerar uma apresentação profissional automaticamente
        </p>
      </div>

      <form onSubmit={handleUpload} className="space-y-4">
        <div className="flex flex-col items-center justify-center border-2 border-dashed border-gray-300 rounded-lg p-8 transition hover:border-blue-500">
          <div className="p-3 rounded-full bg-blue-50 mb-3">
            <Upload className="h-6 w-6 text-blue-600" />
          </div>
          <p className="text-sm text-gray-500 mb-2">
            Arraste e solte o arquivo PDF ou clique para selecionar
          </p>
          <label className="relative cursor-pointer bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-md transition">
            Selecionar Arquivo
            <input
              type="file"
              className="sr-only"
              accept=".pdf"
              onChange={handleFileChange}
              disabled={loading}
            />
          </label>
        </div>

        <div className="flex items-center space-x-2 p-3 bg-gray-50 rounded-lg">
          <File className="h-5 w-5 text-gray-400" />
          <span className="text-sm text-gray-600 truncate flex-1">
            {fileName}
          </span>
          {fileName !== 'Selecione um arquivo PDF' && (
            <CheckCircle className="h-5 w-5 text-green-500" />
          )}
        </div>

        <button
          type="submit"
          disabled={loading || fileName === 'Selecione um arquivo PDF'}
          className={`w-full py-3 px-4 rounded-md font-medium transition ${
            loading || fileName === 'Selecione um arquivo PDF'
              ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
              : 'bg-blue-600 text-white hover:bg-blue-700'
          }`}
        >
          {loading ? 'Processando...' : 'Gerar Apresentação'}
        </button>
      </form>

      {loading && progress !== undefined && (
        <div className="mt-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">{processingStatus}</span>
            <span className="text-sm text-gray-500">{progress}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2.5">
            <div 
              className="bg-blue-600 h-2.5 rounded-full transition-all duration-300"
              style={{ width: `${progress}%` }}
            ></div>
          </div>
        </div>
      )}
    </div>
  );
};

export default UploadSection;