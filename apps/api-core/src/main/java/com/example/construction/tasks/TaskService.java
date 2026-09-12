package com.example.construction.tasks;

import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Map;
import java.util.UUID;

@Service
@RequiredArgsConstructor
public class TaskService {

    private final TaskTreeService taskTreeService;
    private final TaskRepository taskRepository;

    public List<Task> findFlatByProject(UUID projectId) {
        return taskRepository.findByProjectIdOrderByCreatedAtAsc(projectId);
    }

    public ProjectSummaryDto getSummary(UUID projectId) {
        return taskTreeService.projectSummary(projectId);
    }

    public List<TaskSummaryDto> getTree(UUID projectId) {
        return taskTreeService.taskTree(projectId);
    }

    public TaskDetailDto getDetail(UUID projectId, UUID taskId) {
        return taskTreeService.taskDetail(projectId, taskId);
    }

    public TaskDetailDto updateTask(UUID projectId, UUID taskId, Map<String, Object> updates) {
        return taskTreeService.updateTask(projectId, taskId, updates);
    }
}
