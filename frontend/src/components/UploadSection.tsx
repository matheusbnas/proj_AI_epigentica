import React from 'react';
import { Upload, FileText } from 'lucide-react';

interface UploadSectionProps {
  fileName: string;
  handleFileChange: (event: React.ChangeEvent<HTMLInputElement>) => void;
  handleUpload: (event: React.FormEvent) => void;
  loading: boolean;
  error: string | null;
}

const UploadSection: React.FC<UploadSectionProps> = ({
  fileName,
  handleFileChange,
  handleUpload,
  loading,
  error
}) => (
  <div className="bg-white rounded-lg shadow-sm p-6">
    <form onSubmit={handleUpload} className="space-y-4">
      <div className="flex flex-col items-center justify-center border-2 border-dashed border-gray-300 rounded-lg p-6 hover:border-blue-500 transition-colors">
        <label className="cursor-pointer flex flex-col items-center space-y-2">
          <input
            type="file"
            accept="application/pdf"
            onChange={handleFileChange}
            disabled={loading}
            className="hidden"
          />
          <FileText className="h-12 w-12 text-gray-400" />
          <span className="text-sm text-gray-600">{fileName}</span>
        </label>
      </div>
      
      <button
        type="submit"
        className={`w-full flex items-center justify-center space-x-2 px-4 py-2 rounded-md text-white transition-colors ${
          loading
            ? 'bg-gray-400 cursor-not-allowed'
            : 'bg-blue-600 hover:bg-blue-700'
        }`}
        disabled={loading}
      >
        {loading ? (
          <>
            <div className="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent" />
            <span>Processando...</span>
          </>
        ) : (
          <>
            <Upload className="h-5 w-5" />
            <span>Iniciar Análise</span>
          </>
        )}
      </button>
    </form>
    
    {error && (
      <div className="mt-4 p-4 bg-red-50 rounded-md text-sm text-red-700">
        {error}
      </div>
    )}
  </div>
);

export default UploadSection;