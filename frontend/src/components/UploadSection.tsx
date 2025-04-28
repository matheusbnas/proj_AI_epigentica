import React, { useRef } from 'react';
import { Upload, File, X, FileText } from 'lucide-react';

interface UploadSectionProps {
  fileName: string;
  handleFileChange: (event: React.ChangeEvent<HTMLInputElement>) => void;
  handleUpload: (event: React.FormEvent) => void;
  loading: boolean;
  error: string | null;
  acceptedFileTypes?: string;
}

const UploadSection: React.FC<UploadSectionProps> = ({
  fileName,
  handleFileChange,
  handleUpload,
  loading,
  error,
  acceptedFileTypes = ".pdf,.json"
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleResetFile = () => {
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
      handleFileChange({ target: { files: null } } as React.ChangeEvent<HTMLInputElement>);
    }
  };

  const getFileIcon = () => {
    if (fileName.toLowerCase().endsWith('.pdf')) {
      return <FileText className="h-5 w-5 text-red-500" />;
    } else if (fileName.toLowerCase().endsWith('.json')) {
      return <FileText className="h-5 w-5 text-blue-500" />;
    }
    return <File className="h-5 w-5 text-gray-500" />;
  };

  return (
    <div className="bg-white rounded-lg shadow-sm p-6">
      <div className="max-w-xl mx-auto">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Gerar Apresentação</h2>
        <p className="text-gray-600 mb-6">
          Carregue um arquivo PDF ou JSON para gerar uma apresentação de slides interativa com chatbot.
        </p>

        <form onSubmit={handleUpload} className="space-y-6">
          <div className="flex flex-col items-center justify-center border-2 border-dashed border-gray-300 rounded-lg p-6 hover:bg-gray-50 transition-colors cursor-pointer">
            <input
              ref={fileInputRef}
              type="file"
              className="hidden"
              onChange={handleFileChange}
              accept={acceptedFileTypes}
              disabled={loading}
            />
            <Upload className="h-10 w-10 text-gray-400 mb-3" />
            <p className="text-sm font-medium text-gray-900 mb-1">
              Clique para selecionar ou arraste um arquivo
            </p>
            <p className="text-xs text-gray-500">
              Arquivos suportados: PDF e JSON (máx. 30MB)
            </p>

            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
              disabled={loading}
            >
              Selecionar Arquivo
            </button>
          </div>

          {fileName !== 'Selecione um arquivo PDF' && (
            <div className="flex items-center justify-between bg-blue-50 rounded-md p-3">
              <div className="flex items-center">
                {getFileIcon()}
                <span className="ml-2 text-sm font-medium text-gray-700 truncate max-w-xs">
                  {fileName}
                </span>
              </div>
              <button
                type="button"
                onClick={handleResetFile}
                className="text-gray-500 hover:text-gray-700"
                disabled={loading}
              >
                <X className="h-5 w-5" />
              </button>
            </div>
          )}

          <button
            type="submit"
            className="w-full py-2 px-4 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            disabled={loading || fileName === 'Selecione um arquivo PDF'}
          >
            {loading ? (
              <span className="flex items-center justify-center">
                <svg
                  className="animate-spin -ml-1 mr-2 h-4 w-4 text-white"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  ></circle>
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  ></path>
                </svg>
                Processando...
              </span>
            ) : (
              'Gerar Apresentação'
            )}
          </button>
        </form>
      </div>
    </div>
  );
};

export default UploadSection;