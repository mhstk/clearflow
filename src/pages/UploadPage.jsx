import React, { useState } from 'react';
import { Button } from '../components/Button';
import { Upload, FileText, CheckCircle, AlertCircle, Loader } from 'lucide-react';
import { transactionsAPI } from '../services/api';

/**
 * Upload page for CSV file uploads
 */
export const UploadPage = () => {
  const [isDragging, setIsDragging] = useState(false);
  const [uploadedFile, setUploadedFile] = useState(null);
  const [previewData, setPreviewData] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);
  const [uploadError, setUploadError] = useState(null);

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    handleFileUpload(file);
  };

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    handleFileUpload(file);
  };

  const handleFileUpload = (file) => {
    if (file && (file.type === 'text/csv' || file.name.endsWith('.csv'))) {
      setUploadedFile(file);
      setUploadResult(null);
      setUploadError(null);
      // Set basic preview data
      setPreviewData({
        fileName: file.name,
        fileSize: (file.size / 1024).toFixed(2) + ' KB',
      });
    } else {
      setUploadError('Please upload a valid CSV file');
      setUploadedFile(null);
      setPreviewData(null);
    }
  };

  const handleProcessFile = async () => {
    if (!uploadedFile) return;

    setIsUploading(true);
    setUploadError(null);
    setUploadResult(null);

    try {
      // Upload CSV to backend
      const response = await transactionsAPI.uploadCSV(uploadedFile);
      const result = response.data;

      setUploadResult({
        insertedCount: result.inserted_count,
        skippedCount: result.skipped_count,
        accountId: result.account_id,
        totalProcessed: result.inserted_count + result.skipped_count
      });

      // Clear file selection after successful upload
      setTimeout(() => {
        setUploadedFile(null);
        setPreviewData(null);
      }, 3000);

    } catch (error) {
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to upload CSV file';
      setUploadError(errorMessage);
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Upload Card */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8">
        <div className="text-center mb-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Upload Transactions CSV</h2>
          <p className="text-sm text-gray-500">
            Upload your bank statement CSV file to automatically categorize and analyze your
            transactions
          </p>
        </div>

        {/* Drag and Drop Area */}
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={`
            border-2 border-dashed rounded-xl p-12 text-center transition-colors
            ${
              isDragging
                ? 'border-primary-500 bg-primary-50'
                : 'border-gray-300 hover:border-primary-400'
            }
          `}
        >
          <div className="flex flex-col items-center">
            <div className="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center mb-4">
              <Upload size={32} className="text-primary-600" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              Drop your CSV file here
            </h3>
            <p className="text-sm text-gray-500 mb-4">or</p>
            <input
              id="file-upload"
              type="file"
              accept=".csv"
              onChange={handleFileSelect}
              className="hidden"
            />
            <label htmlFor="file-upload" className="cursor-pointer">
              <Button variant="primary" as="span">
                Browse Files
              </Button>
            </label>
          </div>
        </div>

        {/* Supported Format Info */}
        <div className="mt-6 p-4 bg-blue-50 rounded-lg">
          <h4 className="text-sm font-semibold text-blue-900 mb-2">Supported Format</h4>
          <ul className="text-sm text-blue-700 space-y-1">
            <li>• CSV files from most major banks</li>
            <li>• Required columns: Date, Description, Amount</li>
            <li>• Optional columns: Category, Merchant, Account</li>
            <li>• Maximum file size: 10 MB</li>
          </ul>
        </div>
      </div>

      {/* Error Message */}
      {uploadError && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4">
          <div className="flex items-start">
            <div className="flex-shrink-0">
              <AlertCircle size={20} className="text-red-600" />
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-semibold text-red-900">Upload Failed</h3>
              <p className="text-sm text-red-700 mt-1">{uploadError}</p>
            </div>
          </div>
        </div>
      )}

      {/* Success Message */}
      {uploadResult && (
        <div className="bg-green-50 border border-green-200 rounded-xl p-6">
          <div className="flex items-start">
            <div className="flex-shrink-0">
              <CheckCircle size={24} className="text-green-600" />
            </div>
            <div className="ml-4 flex-1">
              <h3 className="text-lg font-semibold text-green-900">Upload Successful!</h3>
              <p className="text-sm text-green-700 mt-1">
                Your transactions have been processed and imported.
              </p>
              <div className="mt-4 grid grid-cols-3 gap-4">
                <div className="bg-white rounded-lg p-3 border border-green-200">
                  <p className="text-2xl font-bold text-green-600">{uploadResult.insertedCount}</p>
                  <p className="text-xs text-gray-600 mt-1">Transactions Added</p>
                </div>
                <div className="bg-white rounded-lg p-3 border border-green-200">
                  <p className="text-2xl font-bold text-gray-600">{uploadResult.skippedCount}</p>
                  <p className="text-xs text-gray-600 mt-1">Duplicates Skipped</p>
                </div>
                <div className="bg-white rounded-lg p-3 border border-green-200">
                  <p className="text-2xl font-bold text-gray-900">{uploadResult.totalProcessed}</p>
                  <p className="text-xs text-gray-600 mt-1">Total Processed</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* File Preview Section */}
      {previewData && !uploadResult && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center">
              <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center mr-3">
                <FileText size={20} className="text-blue-600" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-gray-900">File Ready</h3>
                <p className="text-sm text-gray-500">
                  {previewData.fileName} ({previewData.fileSize})
                </p>
              </div>
            </div>
            <Button
              variant="primary"
              onClick={handleProcessFile}
              disabled={isUploading}
            >
              {isUploading ? (
                <span className="flex items-center">
                  <Loader size={16} className="mr-2 animate-spin" />
                  Uploading...
                </span>
              ) : (
                'Upload to Server'
              )}
            </Button>
          </div>

          <div className="p-4 bg-blue-50 rounded-lg">
            <p className="text-sm text-blue-900">
              Click "Upload to Server" to process and import your transactions.
              The system will automatically categorize merchants and detect duplicates.
            </p>
          </div>
        </div>
      )}

      {/* Instructions */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">How It Works</h3>
        <div className="space-y-4">
          <div className="flex items-start">
            <div className="flex-shrink-0 w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center mr-3">
              <span className="text-sm font-semibold text-primary-600">1</span>
            </div>
            <div>
              <h4 className="text-sm font-semibold text-gray-900 mb-1">
                Export from Your Bank
              </h4>
              <p className="text-sm text-gray-500">
                Download your transaction history as a CSV file from your bank's website
              </p>
            </div>
          </div>

          <div className="flex items-start">
            <div className="flex-shrink-0 w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center mr-3">
              <span className="text-sm font-semibold text-primary-600">2</span>
            </div>
            <div>
              <h4 className="text-sm font-semibold text-gray-900 mb-1">Upload & Preview</h4>
              <p className="text-sm text-gray-500">
                Upload your CSV file and preview the data to ensure it looks correct
              </p>
            </div>
          </div>

          <div className="flex items-start">
            <div className="flex-shrink-0 w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center mr-3">
              <span className="text-sm font-semibold text-primary-600">3</span>
            </div>
            <div>
              <h4 className="text-sm font-semibold text-gray-900 mb-1">
                AI Categorization
              </h4>
              <p className="text-sm text-gray-500">
                Our AI will automatically categorize transactions and extract merchant information
              </p>
            </div>
          </div>

          <div className="flex items-start">
            <div className="flex-shrink-0 w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center mr-3">
              <span className="text-sm font-semibold text-primary-600">4</span>
            </div>
            <div>
              <h4 className="text-sm font-semibold text-gray-900 mb-1">
                Review & Analyze
              </h4>
              <p className="text-sm text-gray-500">
                Review your transactions and get AI-powered insights about your spending habits
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
