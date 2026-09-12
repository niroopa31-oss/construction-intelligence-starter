package com.example.construction.tasks;

import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.util.List;
import java.util.Map;
import java.util.UUID;

@Service
@RequiredArgsConstructor
public class AiSummaryService {

    private final TaskService taskService;
    private final RestTemplate restTemplate;

    @Value("${ai.service.url:http://localhost:8000}")
    private String aiServiceUrl;

    public Map<String, Object> getSummary(UUID projectId) {
        List<Task> tasks = taskService.findFlatByProject(projectId);

        List<Map<String, Object>> flatTasks = tasks.stream().map(t -> {
            Map<String, Object> m = new java.util.LinkedHashMap<>();
            m.put("node_type",       t.getNodeType() != null ? t.getNodeType().toLowerCase() : "sub_task");
            m.put("name",            t.getName());
            m.put("planned_start",   t.getBaselineStart()  != null ? t.getBaselineStart().toString()  : null);
            m.put("planned_finish",  t.getBaselineFinish() != null ? t.getBaselineFinish().toString() : null);
            m.put("actual_progress", t.getProgressPercent());
            return m;
        }).toList();

        Map<String, Object> body = Map.of(
                "flat_tasks",   flatTasks,
                "project_name", ""
        );
        

        @SuppressWarnings("unchecked")
        Map<String, Object> result = restTemplate.postForObject(
                aiServiceUrl + "/api/projects/" + projectId + "/ai-summary",
                body,
                Map.class
        );

        return result != null ? result : Map.of("error", "No response from AI service");
    }
}