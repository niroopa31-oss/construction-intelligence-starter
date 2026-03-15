package com.example.construction.tasks;

import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;
import java.util.UUID;

public interface TaskAssignmentRepository extends JpaRepository<TaskAssignment, UUID> {
    List<TaskAssignment> findByTaskIdOrderByCreatedAtAsc(UUID taskId);
    void deleteByIdAndTaskId(UUID id, UUID taskId);
}
