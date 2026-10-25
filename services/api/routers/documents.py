import os
import uuid

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from services.api.auth.dependencies import (
    TenantContext,
    get_tenant_context,
    require_role,
)
from services.api.config import settings
from services.api.database import get_db
from services.api.ingestion.pipeline import IngestionPipeline
from services.api.models.audit import AuditEvent
from services.api.models.document import (
    Document,
    DocumentChunk,
    DocumentClassification,
    DocumentStatus,
)
from services.api.models.user import UserRole

router = APIRouter(prefix="/documents", tags=["Documents"])


class DocumentItemResponse(BaseModel):
    id: str
    workspace_id: str
    title: str
    filename: str
    file_size: int
    content_hash: str
    page_count: int
    status: str
    classification: str
    error_message: str | None = None
    created_at: str


class DocumentListResponse(BaseModel):
    items: list[DocumentItemResponse]
    total: int
    page: int
    limit: int


class DocumentStatusResponse(BaseModel):
    id: str
    status: str
    chunk_count: int
    error_message: str | None = None


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: str | None = None,
    tenant: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Document).where(Document.workspace_id == tenant.workspace_id)
    if status:
        stmt = stmt.where(Document.status == status)

    # Count
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_res = await db.execute(count_stmt)
    total = total_res.scalar() or 0

    # Paginate
    stmt = stmt.order_by(Document.created_at.desc()).offset((page - 1) * limit).limit(limit)
    res = await db.execute(stmt)
    docs = res.scalars().all()

    items = [
        DocumentItemResponse(
            id=d.id,
            workspace_id=d.workspace_id,
            title=d.title,
            filename=d.filename,
            file_size=d.file_size,
            content_hash=d.content_hash,
            page_count=d.page_count,
            status=d.status.value,
            classification=d.classification.value,
            error_message=d.error_message,
            created_at=d.created_at.isoformat(),
        )
        for d in docs
    ]
    return DocumentListResponse(items=items, total=total, page=page, limit=limit)


@router.post("", status_code=status.HTTP_202_ACCEPTED, response_model=DocumentItemResponse)
async def upload_document(
    file: UploadFile = File(...),
    title: str | None = Form(None),
    classification: str | None = Form("GENERAL_CONTRACT"),
    tenant: TenantContext = Depends(require_role([UserRole.ADMINISTRATOR, UserRole.RESEARCHER])),
    db: AsyncSession = Depends(get_db),
):
    # Validate filename & extension
    if not file.filename:
        raise HTTPException(status_code=400, detail={"error_code": "EMPTY_FILENAME", "message": "Filename cannot be empty"})

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".pdf", ".txt", ".md"]:
        raise HTTPException(
            status_code=400,
            detail={"error_code": "INVALID_FILE_TYPE", "message": f"Extension '{ext}' not supported. Allowed: .pdf, .txt"},
        )

    # Read bytes
    content = await file.read()
    if len(content) > settings.MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail={"error_code": "FILE_TOO_LARGE", "message": f"File exceeds {settings.MAX_UPLOAD_SIZE_BYTES} bytes limit"},
        )

    # Calculate SHA-256
    content_hash = IngestionPipeline.compute_sha256(content)

    # Check duplicate in workspace
    dup_res = await db.execute(
        select(Document).where(Document.workspace_id == tenant.workspace_id, Document.content_hash == content_hash)
    )
    dup = dup_res.scalar_one_or_none()
    if dup:
        return DocumentItemResponse(
            id=dup.id,
            workspace_id=dup.workspace_id,
            title=dup.title,
            filename=dup.filename,
            file_size=dup.file_size,
            content_hash=dup.content_hash,
            page_count=dup.page_count,
            status=dup.status.value,
            classification=dup.classification.value,
            error_message=dup.error_message,
            created_at=dup.created_at.isoformat(),
        )

    # Save to storage
    doc_id = str(uuid.uuid4())
    save_filename = f"{tenant.workspace_id}_{doc_id}_{os.path.basename(file.filename)}"
    storage_path = os.path.join(settings.STORAGE_DIR, save_filename)
    with open(storage_path, "wb") as f:
        f.write(content)

    # Classification mapping
    try:
        doc_class = DocumentClassification(classification)
    except Exception:
        doc_class = DocumentClassification.GENERAL_CONTRACT

    # Create document record
    doc = Document(
        id=doc_id,
        workspace_id=tenant.workspace_id,
        title=title or file.filename,
        filename=file.filename,
        file_size=len(content),
        mime_type=file.content_type or "application/octet-stream",
        content_hash=content_hash,
        storage_path=storage_path,
        status=DocumentStatus.UPLOADED,
        classification=doc_class,
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    # Execute ingestion immediately
    try:
        await IngestionPipeline.process_document(doc.id, db)
        await db.refresh(doc)
    except Exception:
        # Status becomes FAILED inside pipeline
        await db.refresh(doc)

    return DocumentItemResponse(
        id=doc.id,
        workspace_id=doc.workspace_id,
        title=doc.title,
        filename=doc.filename,
        file_size=doc.file_size,
        content_hash=doc.content_hash,
        page_count=doc.page_count,
        status=doc.status.value,
        classification=doc.classification.value,
        error_message=doc.error_message,
        created_at=doc.created_at.isoformat(),
    )


@router.get("/{document_id}", response_model=DocumentItemResponse)
async def get_document(
    document_id: str,
    tenant: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(
        select(Document).where(Document.id == document_id, Document.workspace_id == tenant.workspace_id)
    )
    doc = res.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail={"error_code": "NOT_FOUND", "message": "Document not found"})

    return DocumentItemResponse(
        id=doc.id,
        workspace_id=doc.workspace_id,
        title=doc.title,
        filename=doc.filename,
        file_size=doc.file_size,
        content_hash=doc.content_hash,
        page_count=doc.page_count,
        status=doc.status.value,
        classification=doc.classification.value,
        error_message=doc.error_message,
        created_at=doc.created_at.isoformat(),
    )


@router.get("/{document_id}/status", response_model=DocumentStatusResponse)
async def get_document_status(
    document_id: str,
    tenant: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(
        select(Document).where(Document.id == document_id, Document.workspace_id == tenant.workspace_id)
    )
    doc = res.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail={"error_code": "NOT_FOUND", "message": "Document not found"})

    # Count chunks
    chunk_res = await db.execute(
        select(func.count(DocumentChunk.id)).where(DocumentChunk.document_id == document_id)
    )
    chunk_count = chunk_res.scalar() or 0

    return DocumentStatusResponse(
        id=doc.id,
        status=doc.status.value,
        chunk_count=chunk_count,
        error_message=doc.error_message,
    )


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    tenant: TenantContext = Depends(require_role([UserRole.ADMINISTRATOR])),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(
        select(Document).where(Document.id == document_id, Document.workspace_id == tenant.workspace_id)
    )
    doc = res.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail={"error_code": "NOT_FOUND", "message": "Document not found"})

    # Remove storage file if exists
    if os.path.exists(doc.storage_path):
        try:
            os.remove(doc.storage_path)
        except Exception:
            pass

    # Audit event
    audit = AuditEvent(
        workspace_id=tenant.workspace_id,
        user_id=tenant.user_id,
        action="DOCUMENT_DELETED",
        entity_type="document",
        entity_id=doc.id,
        details=f'{{"filename": "{doc.filename}"}}',
    )
    db.add(audit)

    await db.delete(doc)
    await db.commit()
    return {"success": True, "message": "Document deleted successfully"}
