package com.example.construction.tasks;

import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.UUID;

public interface TaskRepository extends JpaRepository<Task, UUID> {
    List<Task> findByProjectIdOrderByCreatedAtAsc(UUID projectId);
}
