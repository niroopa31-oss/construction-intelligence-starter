package com.example.construction.meetings;

import jakarta.persistence.*;
import lombok.*;

import java.time.Instant;
import java.time.LocalDateTime;
import java.util.UUID;

@Entity
@Table(name = "task_meeting")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class TaskMeeting {
    @Id
    @GeneratedValue
    private UUID id;

    @Column(name = "task_id", nullable = false)
    private UUID taskId;

    @Column(nullable = false)
    private String title;

    @Column(columnDefinition = "text")
    private String agenda;

    private LocalDateTime startTime;
    private LocalDateTime endTime;
    private String attendees;
    private String status;

    private String calendarEventUid;
    private Integer calendarSequence;
    private LocalDateTime inviteSentAt;

    @Builder.Default
    private Instant createdAt = Instant.now();
}
