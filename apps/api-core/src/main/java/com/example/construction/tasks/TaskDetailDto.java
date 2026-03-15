package com.example.construction.tasks;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;

public record TaskDetailDto(
        UUID id,
        UUID projectId,
        UUID parentId,
        String name,
        String nodeType,
        String phase,
        String discipline,
        String tower,
        String floorName,
        String zoneName,
        LocalDate baselineStart,
        LocalDate baselineFinish,
        LocalDate actualStart,
        LocalDate actualFinish,
        LocalDate forecastFinish,
        BigDecimal progressPercent,
        BigDecimal plannedQty,
        BigDecimal actualQty,
        String uom,
        boolean criticalFlag,
        BigDecimal confidenceScore,
        String status,
        long delayedDays,
        List<String> path,
        List<String> contractorNames,
        List<ArtifactDto> documents,
        List<ArtifactDto> images,
        List<DiscrepancyDto> discrepancies,
        List<String> aiSuggestions,
        List<ContractorAssignmentDto> contractorAssignments,
        List<ContractorOptionDto> availableContractors,
        List<MeetingDto> meetings,
        List<ReminderDto> reminders
) {
    public record ArtifactDto(UUID id, String label, String type, String uploadedAt) {}
    public record DiscrepancyDto(UUID id, String severity, String summary, String status) {}
    public record ContractorAssignmentDto(UUID id, UUID contractorId, String companyName, String contactName, String email, String roleName) {}
    public record ContractorOptionDto(UUID id, String companyName, String contactName, String email, String tradeType) {}
    public record MeetingDto(UUID id, String title, String agenda, LocalDateTime startTime, LocalDateTime endTime, String attendees, String status, LocalDateTime inviteSentAt, String calendarEventUid) {}
    public record ReminderDto(UUID id, String subject, String body, String recipients, LocalDateTime scheduledAt, LocalDateTime sentAt, String status, String sendError) {}
}
