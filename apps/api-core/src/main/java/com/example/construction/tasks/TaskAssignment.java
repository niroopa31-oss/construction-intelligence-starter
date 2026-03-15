package com.example.construction.tasks;

import jakarta.persistence.*;
import lombok.*;
import java.time.Instant;
import java.util.UUID;

@Entity
@Table(name = "task_assignment")
@Getter @Setter @NoArgsConstructor @AllArgsConstructor @Builder
public class TaskAssignment {
    @Id
    @GeneratedValue
    private UUID id;
    @Column(name = "task_id", nullable = false)
    private UUID taskId;
    @Column(name = "contractor_id", nullable = false)
    private UUID contractorId;
    private String roleName;
    @Builder.Default
    private Instant createdAt = Instant.now();
}
