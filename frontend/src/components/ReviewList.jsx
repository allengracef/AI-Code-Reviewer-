import { useEffect, useState } from 'react';
import api from '../api/client';
import { Trash2, ChevronLeft, ChevronRight } from 'lucide-react';
import './ReviewList.css';

export default function ReviewList({ onSelect, onDelete, activeId }) {
  const [reviews, setReviews] = useState([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api.get(`/api/v1/reviews/?page=${page}&limit=20`)
      .then(r => {
        setReviews(r.data.items);
        setTotalPages(r.data.pages);
      })
      .finally(() => setLoading(false));
  }, [page]);

  const LANG_COLOR = { python: '#3b82f6', javascript: '#f59e0b', java: '#ef4444' };

  return (
    <div className="review-list">
      <h3 className="list-title">Past Reviews</h3>
      {loading ? (
        <div className="list-loading"><div className="spinner" /></div>
      ) : reviews.length === 0 ? (
        <p className="list-empty">No reviews yet. Upload a file above!</p>
      ) : (
        <ul className="list-items">
          {reviews.map(r => (
            <li
              key={r.id}
              className={`list-item ${activeId === r.id ? 'active' : ''}`}
              onClick={() => onSelect(r.id)}
            >
              <div className="list-item-main">
                <span
                  className="list-lang-dot"
                  style={{ background: LANG_COLOR[r.language] || '#6b7280' }}
                />
                <span className="list-filename">{r.filename}</span>
              </div>
              <div className="list-item-meta">
                <span className="list-count">{r.issue_count} issues</span>
                <button
                  className="list-delete"
                  title="Delete"
                  onClick={e => { e.stopPropagation(); onDelete(r.id); }}
                >
                  <Trash2 size={13} />
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}

      {totalPages > 1 && (
        <div className="list-pagination">
          <button disabled={page === 1} onClick={() => setPage(p => p - 1)}>
            <ChevronLeft size={14} />
          </button>
          <span>{page} / {totalPages}</span>
          <button disabled={page === totalPages} onClick={() => setPage(p => p + 1)}>
            <ChevronRight size={14} />
          </button>
        </div>
      )}
    </div>
  );
}
