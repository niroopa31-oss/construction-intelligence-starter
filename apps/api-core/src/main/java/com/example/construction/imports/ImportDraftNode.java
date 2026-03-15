package com.example.construction.imports;

import jakarta.persistence.*;
import lombok.*;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.UUID;

@Entity
@Table(name = "import_draft_node")
@Getter @Setter @NoArgsConstructor @AllArgsConstructor @Builder
public class ImportDraftNode {
    @Id
    @GeneratedValue
    private UUID id;
    @Column(name = "draft_id", nullable = false)
    private UUID draftId;
    @Column(name = "parent_id")
    private UUID parentId;
    private String externalSourceId;
    @Column(nullable = false)
    private String name;
    @Column(nullable = false)
    private String nodeType;
    private String phase;
    private String discipline;
    private String tower;
    private String blockName;
    private String floorName;
    private String zoneName;
    private LocalDate baselineStart;
    private LocalDate baselineFinish;
    private BigDecimal plannedQty;
    private String uom;
    private BigDecimal confidenceScore;
    @Column(name = "sort_order", nullable = false)
    private int sortOrder;
}
