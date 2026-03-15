package com.example.construction.imports;

import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;
import java.util.UUID;

public interface ImportDraftRepository extends JpaRepository<ImportDraft, UUID> {
    List<ImportDraft> findByUserIdOrderByCreatedAtDesc(UUID userId);
}
