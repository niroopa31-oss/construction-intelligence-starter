package com.example.construction.tasks;

import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;
import java.util.UUID;

@RestController
@RequestMapping("/api/projects/{projectId}")
@RequiredArgsConstructor
public class TaskController {

    private final TaskService taskService;
    private final AiSummaryService aiSummaryService;

    @GetMapping("/tasks/flat")
    public List<Task> flat(@PathVariable UUID projectId) {
        return taskService.findFlatByProject(projectId);
    }

    @GetMapping("/summary")
    public ProjectSummaryDto summary(@PathVariable UUID projectId) {
        return taskService.getSummary(projectId);
    }

    @GetMapping("/tasks/tree")
    public List<TaskSummaryDto> tree(@PathVariable UUID projectId) {
        return taskService.getTree(projectId);
    }

    @GetMapping("/tasks/{taskId}/detail")
    public TaskDetailDto detail(@PathVariable UUID projectId, @PathVariable UUID taskId) {
        return taskService.getDetail(projectId, taskId);
    }

    @GetMapping("/ai-summary")
    public Map<String, Object> aiSummary(@PathVariable UUID projectId) {
        return aiSummaryService.getSummary(projectId);
    }
}
