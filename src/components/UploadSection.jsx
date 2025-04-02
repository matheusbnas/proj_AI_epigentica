import React from 'react';
import { Upload, FileText } from 'lucide-react';

const UploadSection = ({ fileName, handleFileChange, handleUpload, loading, error }) => (
    <div className="upload-section">
        <form onSubmit={handleUpload}>
            <label className="file-input">
                <input
                    type="file"
                    accept="application/pdf"
                    onChange={handleFileChange}
                    disabled={loading}
                />
                <div className="file-label">
                    <FileText size={18} />
                    <span>{fileName}</span>
                </div>
            </label>
            
            <button
                type="submit"
                className="upload-button"
                disabled={loading}
            >
                {loading ? 'Processando...' : (
                    <>
                        <Upload size={16} />
                        Iniciar Análise
                    </>
                )}
            </button>
        </form>
        
        {error && <div className="error-message">{error}</div>}
    </div>
);

export default UploadSection;