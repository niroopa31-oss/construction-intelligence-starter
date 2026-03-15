package com.example.construction.reminders;

import jakarta.persistence.*;
import lombok.*;

import java.time.Instant;
import java.time.LocalDateTime;
import java.util.UUID;

@Entity
@Table(name = "task_reminder")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class TaskReminder {
    @Id
    @GeneratedValue
    private UUID id;

    @Column(name = "task_id", nullable = false)
    private UUID taskId;

    private String subject;

    @Column(columnDefinition = "text")
    private String body;

    @Column(columnDefinition = "text")
    private String recipients;

    private LocalDateTime scheduledAt;
    private LocalDateTime sentAt;
    private String status;
    private String sendError;

    @Builder.Default
    private Instant createdAt = Instant.now();
}
