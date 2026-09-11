import { useCallback, useState } from 'react';
import api from '../api/client';
import { UploadCloud, FileCode2 } from 'lucide-react';
import './UploadPanel.css';

const ALLOWED = ['.py', '.js', '.java'];

export default function UploadPanel({ onDone, onResult }) {
  const [dragging, setDragging] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const submit = useCallback(async (file) => {
    const ext = '.' + file.name.split('.').pop().toLowerCase();
    if (!ALLOWED.includes(ext)) {
      setError(`Unsupported file type: ${ext}. Allowed: ${ALLOWED.join(', ')}`);
      return;
    }
    setError('');
    setLoading(true);
    try {
      const form = new FormData();
      form.append('file', file);
      const { data } = await api.post('/api/v1/reviews/upload', form);
      onResult({
        id: null, 
        filename: data.filename,
        language: data.language,
        summary: data.review.summary,
        time_complexity: data.review.time_complexity,
        space_complexity: data.review.space_complexity,
        refactored_code: data.review.refactored_code,
        issues: data.review.issues || []
      });
      onDone();
    } catch (err) {
      setError(err.response?.data?.detail || 'Upload failed.');
    } finally {
      setLoading(false);
    }
  }, [onDone, onResult]);

  const onDrop = useCallback(e => {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) submit(file);
  }, [submit]);

  const onFileChange = e => {
    if (e.target.files[0]) submit(e.target.files[0]);
  };

  return (
    <div className="upload-panel">
      <h3 className="upload-title">Upload File</h3>
      <label
        className={`drop-zone ${dragging ? 'dragging' : ''} ${loading ? 'loading' : ''}`}
        onDragOver={e => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
      >
        <input type="file" accept=".py,.js,.java" onChange={onFileChange} hidden disabled={loading} />
        {loading ? (
          <div className="upload-loading">
            <div className="spinner" />
            <span>Reviewing…</span>
          </div>
        ) : (
          <>
            <UploadCloud size={32} className="drop-icon" color="#38bdf8" />
            <span className="drop-label">Drop a file or <u>browse</u></span>
            <span className="drop-hint">.py · .js · .java — max 25 MB</span>
          </>
        )}
      </label>
      {error && <div className="upload-error">{error}</div>}
    </div>
  );
}
