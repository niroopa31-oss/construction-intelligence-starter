package com.example.construction.imports;

import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;
import java.util.UUID;

public interface ImportDraftNodeRepository extends JpaRepository<ImportDraftNode, UUID> {
    List<ImportDraftNode> findByDraftIdOrderBySortOrder(UUID draftId);
}
