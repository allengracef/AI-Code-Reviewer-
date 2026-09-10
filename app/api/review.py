from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import IssueRecord, ReviewRecord, User
from app.schemas.review import CodeFile
from app.services.auth import get_current_user
from app.services.language import detect_language
from app.services.review import review_code

ALLOWED_EXTENSIONS = {".py", ".java", ".js"}
MAX_FILE_SIZE = 25 * 1024 * 1024

router = APIRouter(dependencies=[Depends(get_current_user)])


# ── Helpers ───────────────────────────────────────────────────────────────────
def _get_user_review_or_404(review_id: int, user: User, db: Session) -> ReviewRecord:
    record = (
        db.query(ReviewRecord)
        .filter(ReviewRecord.id == review_id, ReviewRecord.user_id == user.id)
        .first()
    )
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Review {review_id} not found.",
        )
    return record


def _serialize_review(r: ReviewRecord, include_issues: bool = True) -> dict:
    base = {
        "id": r.id,
        "filename": r.filename,
        "language": r.language,
        "summary": r.summary,
        "created_at": r.created_at,
        "updated_at": r.updated_at,
        "issue_count": len(r.issues),
    }
    if include_issues:
        base["issues"] = [
            {
                "id": i.id,
                "source": i.source,
                "severity": i.severity,
                "category": i.category,
                "message": i.message,
                "line": i.line,
                "column": i.column,
                "explanation": i.explanation,
                "suggestion": i.suggestion,
            }
            for i in r.issues
        ]
    return base


# ── Endpoints ─────────────────────────────────────────────────────────────────
@router.post("/upload", response_model=CodeFile)
async def upload_code(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload a source file and receive an AI + static-analysis code review."""
    filename = file.filename or ""
    extension = "." + filename.split(".")[-1].lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {extension}. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size exceeds the maximum allowed size of 25 MB.",
        )

    try:
        source_code = contents.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file must be a valid UTF-8 text file.",
        )

    language = detect_language(extension)
    review = await run_in_threadpool(review_code, source_code, language)

    # ── Persist to database ──────────────────────────────────────────────────
    record = ReviewRecord(
        user_id=current_user.id,
        filename=filename,
        language=language,
        summary=review.get("summary"),
    )
    db.add(record)
    db.flush()  # populate record.id without committing yet

    for issue in review.get("issues", []):
        db.add(
            IssueRecord(
                review_id=record.id,
                source=issue.get("source", ""),
                severity=issue.get("severity", ""),
                category=issue.get("category", ""),
                message=issue.get("message", ""),
                line=issue.get("line"),
                column=issue.get("column"),
                code=issue.get("code"),
                explanation=issue.get("explanation"),
                suggestion=issue.get("suggestion"),
            )
        )

    db.commit()
    # ─────────────────────────────────────────────────────────────────────────

    return {
        "filename": file.filename,
        "content_type": file.content_type,
        "size": len(contents),
        "code": source_code,
        "language": language,
        "review": review,
    }


@router.get("/")
def list_reviews(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    limit: int = Query(20, ge=1, le=100, description="Results per page (max 100)"),
):
    """Return a paginated list of the current user's reviews (newest first)."""
    offset = (page - 1) * limit
    total = (
        db.query(ReviewRecord)
        .filter(ReviewRecord.user_id == current_user.id)
        .count()
    )
    records = (
        db.query(ReviewRecord)
        .filter(ReviewRecord.user_id == current_user.id)
        .order_by(ReviewRecord.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return {
        "page": page,
        "limit": limit,
        "total": total,
        "pages": max(1, -(-total // limit)),  # ceiling division
        "items": [_serialize_review(r, include_issues=False) for r in records],
    }


@router.get("/{review_id}")
def get_review(
    review_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return a single review (must belong to the current user)."""
    record = _get_user_review_or_404(review_id, current_user, db)
    return _serialize_review(record, include_issues=True)


@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_review(
    review_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a review and all its issues (must belong to the current user)."""
    record = _get_user_review_or_404(review_id, current_user, db)
    db.delete(record)
    db.commit()
