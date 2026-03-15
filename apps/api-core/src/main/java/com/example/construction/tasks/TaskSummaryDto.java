package com.example.construction.tasks;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

public record TaskSummaryDto(
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
        boolean criticalFlag,
        BigDecimal confidenceScore,
        String status,
        long delayedDays,
        int documentCount,
        int imageCount,
        int discrepancyCount,
        List<String> contractorNames,
        List<TaskSummaryDto> children
) {
    public static TaskSummaryDto fromTask(Task task) {
        return fromTask(task, List.of());
    }

    public static TaskSummaryDto fromTask(Task task, List<String> contractorNames) {
        return new TaskSummaryDto(
                task.getId(),
                task.getProjectId(),
                task.getParentId(),
                task.getName(),
                task.getNodeType(),
                task.getPhase(),
                task.getDiscipline(),
                task.getTower(),
                task.getFloorName(),
                task.getZoneName(),
                task.getBaselineStart(),
                task.getBaselineFinish(),
                task.getActualStart(),
                task.getActualFinish(),
                task.getForecastFinish(),
                task.getProgressPercent(),
                task.isCriticalFlag(),
                task.getConfidenceScore(),
                TaskViewLogic.inferStatus(task),
                TaskViewLogic.delayedDays(task),
                0,
                0,
                0,
                contractorNames,
                new ArrayList<>()
        );
    }
}
