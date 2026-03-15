package com.example.construction.tasks;

import jakarta.persistence.*;
import lombok.*;
import java.math.BigDecimal;
import java.time.Instant;
import java.time.LocalDate;
import java.util.UUID;

@Entity
@Table(name = "task")
@Getter @Setter @NoArgsConstructor @AllArgsConstructor @Builder
public class Task {
    @Id
    @GeneratedValue
    private UUID id;
    @Column(name = "project_id", nullable = false)
    private UUID projectId;
    @Column(name = "parent_id")
    private UUID parentId;
    private String externalSourceId;
    private String externalParentId;
    @Column(nullable = false)
    private String name;
    private String normalizedName;
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
    private LocalDate actualStart;
    private LocalDate actualFinish;
    private LocalDate forecastFinish;
    private BigDecimal plannedQty;
    private BigDecimal actualQty;
    private String uom;
    private BigDecimal progressPercent;
    private boolean criticalFlag;
    private BigDecimal confidenceScore;
    @Builder.Default
    private Instant createdAt = Instant.now();
}
