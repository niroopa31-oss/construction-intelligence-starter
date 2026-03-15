package com.example.construction.tasks;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.temporal.ChronoUnit;

final class TaskViewLogic {
    private TaskViewLogic() {}

    static String inferStatus(Task task) {
        BigDecimal progress = task.getProgressPercent() == null ? BigDecimal.ZERO : task.getProgressPercent();
        if (progress.compareTo(BigDecimal.valueOf(100)) >= 0 || task.getActualFinish() != null) {
            return "completed";
        }
        if (task.getForecastFinish() != null && task.getBaselineFinish() != null && task.getForecastFinish().isAfter(task.getBaselineFinish())) {
            return "delayed";
        }
        if (task.getBaselineFinish() != null && task.getBaselineFinish().isBefore(LocalDate.now()) && progress.compareTo(BigDecimal.valueOf(100)) < 0) {
            return "at-risk";
        }
        if (progress.compareTo(BigDecimal.ZERO) > 0) {
            return "on-track";
        }
        return "not-started";
    }

    static long delayedDays(Task task) {
        if (task.getForecastFinish() != null && task.getBaselineFinish() != null && task.getForecastFinish().isAfter(task.getBaselineFinish())) {
            return ChronoUnit.DAYS.between(task.getBaselineFinish(), task.getForecastFinish());
        }
        return 0;
    }
}
