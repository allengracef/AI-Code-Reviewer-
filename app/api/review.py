import urllib.request
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import IssueRecord, ReviewRecord, User
from app.schemas.review import CodeFile, CodePasteRequest, GithubImportRequest
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
    import json
    confidence_breakdown = None
    unknown_zones = None
    if r.confidence_breakdown_json:
        try:
            confidence_breakdown = json.loads(r.confidence_breakdown_json)
        except Exception:
            confidence_breakdown = None
    if r.unknown_zones_json:
        try:
            unknown_zones = json.loads(r.unknown_zones_json)
        except Exception:
            unknown_zones = None

    base = {
        "id": r.id,
        "filename": r.filename,
        "language": r.language,
        "summary": r.summary,
        "time_complexity": r.time_complexity,
        "space_complexity": r.space_complexity,
        "refactored_code": r.refactored_code,
        "risk_score": r.risk_score,
        "risk_level": r.risk_level,
        "analysis_confidence": r.analysis_confidence,
        "analysis_coverage": r.analysis_coverage,
        "detected_framework": r.detected_framework,
        "confidence_breakdown": confidence_breakdown,
        "unknown_zones": unknown_zones,
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
    import json
    confidence_breakdown_json = json.dumps(review.get("confidence_breakdown")) if review.get("confidence_breakdown") else None
    unknown_zones_json = json.dumps(review.get("unknown_zones")) if review.get("unknown_zones") else None

    record = ReviewRecord(
        user_id=current_user.id,
        filename=filename,
        language=language,
        summary=review.get("summary"),
        time_complexity=review.get("time_complexity"),
        space_complexity=review.get("space_complexity"),
        refactored_code=review.get("refactored_code"),
        risk_score=review.get("risk_score"),
        risk_level=review.get("risk_level"),
        analysis_confidence=review.get("analysis_confidence"),
        analysis_coverage=review.get("analysis_coverage"),
        detected_framework=review.get("detected_framework"),
        confidence_breakdown_json=confidence_breakdown_json,
        unknown_zones_json=unknown_zones_json,
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
                line=str(issue.get("line")) if issue.get("line") is not None else None,
                column=issue.get("column"),
                code=issue.get("code"),
                explanation=issue.get("explanation"),
                suggestion=issue.get("suggestion"),
            )
        )

    db.commit()

    review["id"] = record.id

    return {
        "filename": file.filename,
        "content_type": file.content_type,
        "size": len(contents),
        "code": source_code,
        "language": language,
        "review": review,
    }


@router.post("/paste", response_model=CodeFile)
async def paste_code(
    payload: CodePasteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Review pasted code or fetched code content directly."""
    source_code = payload.code
    if not source_code.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Code snippet cannot be empty.",
        )

    # Determine extension if present
    raw_filename = (payload.filename or "").strip()
    ext = ("." + raw_filename.split(".")[-1].lower()) if "." in raw_filename else None

    # Detect language accurately from explicit setting, filename, or code contents
    language = detect_language(
        extension=ext,
        code=source_code,
        explicit_language=payload.language,
    )

    # Map language to suitable default filename extension
    ext_map = {"python": ".py", "javascript": ".js", "java": ".java"}
    proper_ext = ext_map.get(language, ".py")

    if not raw_filename:
        filename = f"snippet{proper_ext}"
    elif "." not in raw_filename:
        filename = f"{raw_filename}{proper_ext}"
    else:
        file_ext = "." + raw_filename.split(".")[-1].lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            filename = raw_filename.rsplit(".", 1)[0] + proper_ext
        else:
            filename = raw_filename

    review = await run_in_threadpool(review_code, source_code, language)

    import json
    confidence_breakdown_json = json.dumps(review.get("confidence_breakdown")) if review.get("confidence_breakdown") else None
    unknown_zones_json = json.dumps(review.get("unknown_zones")) if review.get("unknown_zones") else None

    record = ReviewRecord(
        user_id=current_user.id,
        filename=filename,
        language=language,
        summary=review.get("summary"),
        time_complexity=review.get("time_complexity"),
        space_complexity=review.get("space_complexity"),
        refactored_code=review.get("refactored_code"),
        risk_score=review.get("risk_score"),
        risk_level=review.get("risk_level"),
        analysis_confidence=review.get("analysis_confidence"),
        analysis_coverage=review.get("analysis_coverage"),
        detected_framework=review.get("detected_framework"),
        confidence_breakdown_json=confidence_breakdown_json,
        unknown_zones_json=unknown_zones_json,
    )
    db.add(record)
    db.flush()

    for issue in review.get("issues", []):
        db.add(
            IssueRecord(
                review_id=record.id,
                source=issue.get("source", ""),
                severity=issue.get("severity", ""),
                category=issue.get("category", ""),
                message=issue.get("message", ""),
                line=str(issue.get("line")) if issue.get("line") is not None else None,
                column=issue.get("column"),
                code=issue.get("code"),
                explanation=issue.get("explanation"),
                suggestion=issue.get("suggestion"),
            )
        )

    db.commit()

    review["id"] = record.id

    return {
        "filename": filename,
        "content_type": "text/plain",
        "size": len(source_code.encode("utf-8")),
        "code": source_code,
        "language": language,
        "review": review,
    }


@router.post("/github", response_model=CodeFile)
async def import_from_github(
    payload: GithubImportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Fetch file directly from GitHub and perform AI + static review."""
    url = payload.url.strip()
    if not url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="GitHub URL cannot be empty.",
        )

    # Convert standard github URL to raw user content URL if needed
    raw_url = url
    if "github.com" in url and "raw.githubusercontent.com" not in url:
        raw_url = url.replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")

    # Extract filename from URL
    filename = url.split("?")[0].split("/")[-1] or "github_file.py"
    if "." not in filename:
        filename += ".py"

    extension = "." + filename.split(".")[-1].lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{extension}' from GitHub. Allowed extensions: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # Fetch contents using urllib
    try:
        def _fetch():
            req = urllib.request.Request(
                raw_url,
                headers={"User-Agent": "BugLens-App/1.0"}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                return resp.read().decode("utf-8")

        source_code = await run_in_threadpool(_fetch)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to fetch file from GitHub. Ensure the repository and file URL are public. Details: {str(exc)}",
        )

    if not source_code.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The fetched GitHub file is empty.",
        )

    language = detect_language(extension)
    review = await run_in_threadpool(review_code, source_code, language)

    import json
    confidence_breakdown_json = json.dumps(review.get("confidence_breakdown")) if review.get("confidence_breakdown") else None
    unknown_zones_json = json.dumps(review.get("unknown_zones")) if review.get("unknown_zones") else None

    record = ReviewRecord(
        user_id=current_user.id,
        filename=filename,
        language=language,
        summary=review.get("summary"),
        time_complexity=review.get("time_complexity"),
        space_complexity=review.get("space_complexity"),
        refactored_code=review.get("refactored_code"),
        risk_score=review.get("risk_score"),
        risk_level=review.get("risk_level"),
        analysis_confidence=review.get("analysis_confidence"),
        analysis_coverage=review.get("analysis_coverage"),
        detected_framework=review.get("detected_framework"),
        confidence_breakdown_json=confidence_breakdown_json,
        unknown_zones_json=unknown_zones_json,
    )
    db.add(record)
    db.flush()

    for issue in review.get("issues", []):
        db.add(
            IssueRecord(
                review_id=record.id,
                source=issue.get("source", ""),
                severity=issue.get("severity", ""),
                category=issue.get("category", ""),
                message=issue.get("message", ""),
                line=str(issue.get("line")) if issue.get("line") is not None else None,
                column=issue.get("column"),
                code=issue.get("code"),
                explanation=issue.get("explanation"),
                suggestion=issue.get("suggestion"),
            )
        )

    db.commit()

    return {
        "filename": filename,
        "content_type": "text/plain",
        "size": len(source_code.encode("utf-8")),
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
