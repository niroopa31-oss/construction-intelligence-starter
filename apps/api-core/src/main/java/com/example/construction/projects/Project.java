package com.example.construction.projects;

import jakarta.persistence.*;
import lombok.*;
import java.time.Instant;
import java.time.LocalDate;
import java.util.UUID;

@Entity
@Table(name = "project")
@Getter @Setter @NoArgsConstructor @AllArgsConstructor @Builder
public class Project {
    @Id
    @GeneratedValue
    private UUID id;
    @Column(name = "user_id", nullable = false)
    private UUID userId;
    @Column(nullable = false)
    private String name;
    @Column(name = "project_type", nullable = false)
    private String projectType;
    @Column(name = "source_type", nullable = false)
    private String sourceType;
    private String location;
    private LocalDate baselineStart;
    private LocalDate baselineFinish;
    private LocalDate forecastFinish;
    @Column(nullable = false)
    private String status;
    @Builder.Default
    private Instant createdAt = Instant.now();
}
