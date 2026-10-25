import asyncio
import os
from services.api.database import async_session_factory, Base, engine
from services.api.models.workspace import Workspace
from services.api.models.user import User, UserRole
from services.api.models.document import Document, DocumentClassification, DocumentStatus
from services.api.auth.security import hash_password
from services.api.ingestion.pipeline import IngestionPipeline
from services.api.eval.runner import EvaluationRunner

# Ensure models are loaded
import services.api.models  # noqa: F401


SAMPLE_MSA = """MASTER SERVICES AGREEMENT

This Master Services Agreement ("Agreement") is entered into by and between Alpha Legal Technologies Inc. ("Client") and Apex Global Solutions LLC ("Provider").

1. TERM AND TERMINATION
1.1 Initial Term. This Agreement shall commence on January 1, 2025 and shall continue for an initial term of three (3) years unless terminated earlier in accordance with Section 1.2.
1.2 Termination for Cause. Either party may terminate this Agreement upon thirty (30) days prior written notice if the other party breaches any material term and fails to cure such breach within the thirty (30) day notice period.

2. CONFIDENTIALITY AND NON-DISCLOSURE
2.1 Protection of Confidential Information. Each party agrees to hold the other party's Confidential Information in strict confidence and not to disclose such information to any third party.
2.2 Survival. The obligations of non-disclosure and confidentiality under this Section 2 shall remain in full force and effect for two (2) years following the expiration or termination of this Agreement.

3. INDEMNIFICATION AND DEFENSE
3.1 Mutual Indemnity. Each party ("Indemnifying Party") shall indemnify, defend, and hold harmless the other party from and against any third-party claims, liabilities, losses, damages, and reasonable legal expenses arising out of gross negligence or willful misconduct.

4. LIMITATION OF LIABILITY
4.1 Aggregate Cap. In no event shall either party's aggregate cumulative liability arising out of or related to this Agreement exceed the total fees paid by Client to Provider during the twelve (12) month period immediately preceding the event giving rise to liability.
4.2 Waiver of Consequential Damages. Neither party shall be liable to the other for indirect, incidental, punitive, or consequential damages.

5. GOVERNING LAW AND DISPUTE RESOLUTION
5.1 Choice of Law. This Agreement shall be governed by, and construed in accordance with, the laws of the State of Delaware, without giving effect to conflicts of laws principles.
5.2 Jurisdiction. Any dispute arising out of this Agreement shall be resolved exclusively in the state or federal courts located in New Castle County, Delaware.
"""

SAMPLE_NDA = """MUTUAL NON-DISCLOSURE AGREEMENT

This Mutual Non-Disclosure Agreement ("NDA") is executed as of February 15, 2025 by Alpha Legal Technologies Inc. and Beta Counterparty Partners.

1. Definition of Proprietary Information. "Proprietary Information" includes all financial, technical, customer, pricing, and strategic disclosures made in writing or orally.
2. Non-Use Restriction. Recipient shall use Proprietary Information exclusively to evaluate the proposed strategic alliance and for no other commercial purpose.
3. Permitted Disclosures. Recipient may disclose Proprietary Information only to employees, counsel, and auditors with a strict need to know and subject to confidentiality restrictions at least as protective as this NDA.
4. Survival. The confidentiality covenants herein shall endure for twenty-four (24) months after termination of discussions.
5. Governing Law. This NDA shall be governed exclusively by the laws of the State of New York.
"""

SAMPLE_AMENDMENT = """AMENDMENT NO. 1 TO MASTER SERVICES AGREEMENT

This Amendment No. 1 modifies the Master Services Agreement between Alpha Legal Technologies Inc. and Apex Global Solutions LLC.

1. Modification of Liability Provisions.
Section 4.1 of the Agreement is hereby amended and restated in its entirety as follows:
"4.1 Aggregate Cap. In no event shall Provider's aggregate cumulative liability exceed three times (3x) the total fees paid by Client during the preceding twelve-month period, provided that liability for data security breaches and gross negligence shall be uncapped."

2. Modification of Governing Law.
Section 5.1 of the Agreement is hereby amended as follows:
"5.1 Choice of Law. This Agreement shall henceforth be governed by, and construed in accordance with, the laws of the State of New York."
"""


async def seed():
    print("🌱 Seeding TrustCounsel AI database with synthetic demonstration contracts...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_factory() as db:
        # Create Default Workspace
        ws = Workspace(
            id="ws-demo-corp",
            name="Apex Corporate Counsel Matter Vault",
            slug="apex-corporate-counsel",
        )
        db.add(ws)
        await db.flush()

        # Create Default Users
        admin_user = User(
            id="usr-demo-admin",
            workspace_id=ws.id,
            email="partner@trustcounsel.ai",
            password_hash=hash_password("Password123!"),
            full_name="Partner Sarah Jenkins",
            role=UserRole.ADMINISTRATOR,
        )
        db.add(admin_user)

        reviewer_user = User(
            id="usr-demo-reviewer",
            workspace_id=ws.id,
            email="reviewer@trustcounsel.ai",
            password_hash=hash_password("Password123!"),
            full_name="Senior Counsel David Vance",
            role=UserRole.REVIEWER,
        )
        db.add(reviewer_user)
        await db.flush()

        # Ingest Sample Contracts
        contracts = [
            ("Master_Services_Agreement_2025.txt", "Master Services Agreement", DocumentClassification.MSA, SAMPLE_MSA),
            ("Mutual_NDA_Bilateral.txt", "Mutual Non-Disclosure Agreement", DocumentClassification.NDA, SAMPLE_NDA),
            ("MSA_Amendment_Redline_v2.txt", "Counterparty Amendment No. 1", DocumentClassification.MSA, SAMPLE_AMENDMENT),
        ]

        os.makedirs("./data/uploads", exist_ok=True)

        for filename, title, classification, text in contracts:
            storage_path = os.path.join("./data/uploads", f"{ws.id}_{filename}")
            with open(storage_path, "w", encoding="utf-8") as f:
                f.write(text)

            content_bytes = text.encode("utf-8")
            content_hash = IngestionPipeline.compute_sha256(content_bytes)

            doc = Document(
                workspace_id=ws.id,
                title=title,
                filename=filename,
                file_size=len(content_bytes),
                mime_type="text/plain",
                content_hash=content_hash,
                storage_path=storage_path,
                status=DocumentStatus.UPLOADED,
                classification=classification,
            )
            db.add(doc)
            await db.flush()

            # Execute pipeline
            await IngestionPipeline.process_document(doc.id, db)
            print(f"  ✓ Ingested and indexed: '{filename}' ({doc.page_count} pages)")

        # Create Baseline Evaluation Run
        await EvaluationRunner.run_benchmark(
            dataset_name="legal_qa_contracts_v1",
            workspace_id=ws.id,
            db=db,
            model_identifier="mock-legal-v1",
            is_baseline=True,
        )
        print("  ✓ Created golden baseline evaluation run.")

        await db.commit()
    print("✅ Seed completed successfully! Default login: partner@trustcounsel.ai / Password123!")


if __name__ == "__main__":
    asyncio.run(seed())
