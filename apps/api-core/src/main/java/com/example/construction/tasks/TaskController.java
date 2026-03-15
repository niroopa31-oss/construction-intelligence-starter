package com.example.construction.tasks;

import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.UUID;

@RestController
@RequestMapping("/api/projects/{projectId}")
@RequiredArgsConstructor
public class TaskController {
    private final TaskRepository taskRepository;
    private final TaskTreeService taskTreeService;

    @GetMapping("/tasks/flat")
    public List<Task> flat(@PathVariable UUID projectId) {
        return taskRepository.findByProjectIdOrderByCreatedAtAsc(projectId);
    }

    @GetMapping("/summary")
    public ProjectSummaryDto summary(@PathVariable UUID projectId) {
        return taskTreeService.projectSummary(projectId);
    }

    @GetMapping("/tasks/tree")
    public List<TaskSummaryDto> tree(@PathVariable UUID projectId) {
        return taskTreeService.taskTree(projectId);
    }

    @GetMapping("/tasks/{taskId}/detail")
    public TaskDetailDto detail(@PathVariable UUID projectId, @PathVariable UUID taskId) {
        return taskTreeService.taskDetail(projectId, taskId);
    }
}
