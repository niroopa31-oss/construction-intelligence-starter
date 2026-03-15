package com.example.construction.tasks;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

import java.time.LocalDateTime;
import java.util.UUID;

public final class TaskCollaborationDtos {
    private TaskCollaborationDtos() {}

    public record AssignContractorRequest(
            @NotNull UUID contractorId,
            String roleName
    ) {}

    public record CreateMeetingRequest(
            @NotBlank String title,
            String agenda,
            LocalDateTime startTime,
            LocalDateTime endTime,
            String attendees,
            String status,
            Boolean sendInviteNow,
            String inviteBody
    ) {}

    public record CreateReminderRequest(
            @NotBlank String subject,
            String body,
            String recipients,
            LocalDateTime scheduledAt,
            String status,
            Boolean sendNow
    ) {}
}
