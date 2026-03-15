package com.example.construction.reminders;

import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;
import java.util.UUID;

public interface TaskReminderRepository extends JpaRepository<TaskReminder, UUID> {
    List<TaskReminder> findByTaskIdOrderByScheduledAtAscCreatedAtAsc(UUID taskId);
}
