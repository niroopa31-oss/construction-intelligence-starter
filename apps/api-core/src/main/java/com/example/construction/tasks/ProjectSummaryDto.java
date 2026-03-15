package com.example.construction.tasks;

import java.time.LocalDate;
import java.util.UUID;

public record ProjectSummaryDto(
        UUID projectId,
        String projectName,
        String projectType,
        LocalDate baselineFinish,
        LocalDate forecastFinish,
        long totalTasks,
        long completedTasks,
        long delayedTasks,
        long milestoneCount,
        long highRiskCount,
        double overallProgress
) {}
