package com.example.construction.imports;

import jakarta.persistence.*;
import lombok.*;
import java.time.Instant;
import java.util.UUID;

@Entity
@Table(name = "import_draft")
@Getter @Setter @NoArgsConstructor @AllArgsConstructor @Builder
public class ImportDraft {
    @Id
    @GeneratedValue
    private UUID id;
    @Column(name = "user_id", nullable = false)
    private UUID userId;
    private String fileName;
    @Column(name = "source_type", nullable = false)
    private String sourceType;
    @Column(name = "project_name", nullable = false)
    private String projectName;
    private String projectTypeSuggested;
    private String projectTypeSelected;
    @Column(nullable = false)
    private String status;
    @Builder.Default
    private Instant createdAt = Instant.now();
}
