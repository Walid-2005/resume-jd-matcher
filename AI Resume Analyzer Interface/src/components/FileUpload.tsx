import React, { useState } from 'react';
import { Upload, FileText, X, CheckCircle2 } from 'lucide-react';

interface FileUploadProps {
  onFileSelect: (file: File | null) => void;
}

export function FileUpload({ onFileSelect }: FileUploadProps) {
  const [fileName, setFileName] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setFileName(file.name);
      onFileSelect(file);
    }
  };
  
  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file && (file.type === 'application/pdf' || file.name.endsWith('.docx'))) {
      setFileName(file.name);
      onFileSelect(file);
    }
  };
  
  const handleRemove = () => {
    setFileName(null);
    onFileSelect(null);
  };
  
  return (
    <div 
      className={`relative border-2 border-dashed rounded-2xl p-12 text-center transition-all duration-300 ${
        isDragging 
          ? 'border-blue-500 bg-blue-50 scale-105 shadow-xl' 
          : fileName 
            ? 'border-green-400 bg-gradient-to-br from-green-50 to-emerald-50 shadow-lg' 
            : 'border-slate-300 bg-gradient-to-br from-slate-50 to-blue-50/50 hover:border-blue-400 hover:shadow-lg hover:scale-[1.02]'
      }`}
      onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={handleDrop}
    >
      {fileName ? (
        <div className="space-y-4">
          <div className="flex items-center justify-center">
            <div className="relative">
              <div className="w-16 h-16 bg-gradient-to-br from-green-400 to-emerald-600 rounded-2xl flex items-center justify-center shadow-lg">
                <CheckCircle2 className="w-10 h-10 text-white" />
              </div>
              <div className="absolute -top-2 -right-2 w-6 h-6 bg-green-500 rounded-full border-4 border-white animate-pulse"></div>
            </div>
          </div>
          <div className="space-y-2">
            <div className="flex items-center justify-center gap-3">
              <FileText className="w-6 h-6 text-green-600" />
              <p className="text-lg font-semibold text-slate-800">{fileName}</p>
            </div>
            <p className="text-sm text-green-600 font-medium">✓ Ready to analyze</p>
          </div>
          <button 
            onClick={handleRemove}
            className="mx-auto px-4 py-2 bg-white hover:bg-slate-50 border border-slate-200 rounded-lg transition-all hover:scale-105 shadow-sm flex items-center gap-2 text-slate-600 hover:text-slate-900"
          >
            <X className="w-4 h-4" />
            <span className="text-sm font-medium">Remove</span>
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="flex justify-center">
            <div className={`relative p-6 rounded-2xl transition-all duration-300 ${
              isDragging ? 'bg-blue-100 scale-110' : 'bg-blue-50'
            }`}>
              <Upload className={`w-16 h-16 mx-auto transition-all duration-300 ${
                isDragging ? 'text-blue-600 scale-110' : 'text-blue-400'
              }`} />
              {isDragging && (
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="w-20 h-20 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                </div>
              )}
            </div>
          </div>
          <div className="space-y-2">
            <p className="text-xl font-semibold text-slate-700">
              {isDragging ? 'Drop your file here' : 'Drag & drop your resume here'}
            </p>
            <p className="text-slate-500">or click to browse</p>
            <p className="text-xs text-slate-400 font-medium">PDF or DOCX format</p>
          </div>
          <label className="inline-block px-8 py-3 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-xl cursor-pointer hover:from-blue-600 hover:to-purple-700 transition-all shadow-lg hover:shadow-xl hover:scale-105 font-semibold">
            Browse Files
            <input 
              type="file" 
              className="hidden" 
              accept=".pdf,.docx"
              onChange={handleFileChange}
            />
          </label>
        </div>
      )}
    </div>
  );
}
