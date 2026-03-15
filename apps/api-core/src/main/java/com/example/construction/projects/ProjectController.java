package com.example.construction.projects;

import com.example.construction.tasks.Task;
import com.example.construction.tasks.TaskRepository;
import jakarta.transaction.Transactional;
import jakarta.validation.constraints.NotBlank;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.server.ResponseStatusException;

import java.time.LocalDate;
import java.util.*;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api/projects")
@RequiredArgsConstructor
public class ProjectController {
    private final ProjectRepository projectRepository;
    private final TaskRepository taskRepository;

    @GetMapping
    public List<Project> list(@RequestParam UUID userId) {
        return projectRepository.findByUserIdOrderByCreatedAtDesc(userId);
    }

    @PostMapping
    public Project create(@RequestBody CreateProjectRequest request) {
        Project project = Project.builder()
                .userId(request.userId())
                .name(request.name())
                .projectType(request.projectType())
                .sourceType(request.sourceType())
                .location(request.location())
                .baselineStart(request.baselineStart())
                .baselineFinish(request.baselineFinish())
                .status("active")
                .build();
        return projectRepository.save(project);
    }

    @DeleteMapping("/{projectId}")
    @Transactional
    public Map<String, Object> delete(@PathVariable UUID projectId) {
        Project project = projectRepository.findById(projectId)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Project not found"));
        List<Task> tasks = taskRepository.findByProjectIdOrderByCreatedAtAsc(projectId);
        taskRepository.deleteAll(tasks);
        projectRepository.delete(project);
        Map<String, Object> result = new LinkedHashMap<>();
        result.put("deleted", true);
        result.put("projectId", projectId.toString());
        result.put("tasksRemoved", tasks.size());
        return result;
    }

    @GetMapping("/{projectId}/export.csv")
    public ResponseEntity<byte[]> exportCsv(@PathVariable UUID projectId) {
        Project project = projectRepository.findById(projectId)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Project not found"));
        List<Task> tasks = taskRepository.findByProjectIdOrderByCreatedAtAsc(projectId);

        // Build parent-path map for hierarchy breadcrumb
        Map<UUID, Task> taskMap = tasks.stream().collect(Collectors.toMap(Task::getId, t -> t));

        StringBuilder csv = new StringBuilder();
        csv.append("Name,Node Type,Phase,Tower,Floor,Zone,Discipline,Baseline Start,Baseline Finish,")
           .append("Actual Start,Actual Finish,Forecast Finish,Progress %,Planned Qty,Actual Qty,UOM,Critical,Path\n");

        for (Task t : tasks) {
            csv.append(esc(t.getName())).append(',');
            csv.append(esc(t.getNodeType())).append(',');
            csv.append(esc(t.getPhase())).append(',');
            csv.append(esc(t.getTower())).append(',');
            csv.append(esc(t.getFloorName())).append(',');
            csv.append(esc(t.getZoneName())).append(',');
            csv.append(esc(t.getDiscipline())).append(',');
            csv.append(esc(t.getBaselineStart())).append(',');
            csv.append(esc(t.getBaselineFinish())).append(',');
            csv.append(esc(t.getActualStart())).append(',');
            csv.append(esc(t.getActualFinish())).append(',');
            csv.append(esc(t.getForecastFinish())).append(',');
            csv.append(esc(t.getProgressPercent())).append(',');
            csv.append(esc(t.getPlannedQty())).append(',');
            csv.append(esc(t.getActualQty())).append(',');
            csv.append(esc(t.getUom())).append(',');
            csv.append(t.isCriticalFlag() ? "Yes" : "No").append(',');
            csv.append(esc(buildPath(t, taskMap)));
            csv.append('\n');
        }

        byte[] bytes = csv.toString().getBytes(java.nio.charset.StandardCharsets.UTF_8);
        String filename = project.getName().replaceAll("[^a-zA-Z0-9._\\- ]", "_") + ".csv";
        return ResponseEntity.ok()
                .header(HttpHeaders.CONTENT_DISPOSITION, "attachment; filename=\"" + filename + "\"")
                .contentType(MediaType.parseMediaType("text/csv; charset=UTF-8"))
                .body(bytes);
    }

    private String buildPath(Task task, Map<UUID, Task> taskMap) {
        LinkedList<String> path = new LinkedList<>();
        Task current = task;
        while (current != null) {
            path.addFirst(current.getName());
            current = current.getParentId() == null ? null : taskMap.get(current.getParentId());
        }
        return String.join(" › ", path);
    }

    private String esc(Object value) {
        if (value == null) return "";
        String s = value.toString();
        if (s.contains(",") || s.contains("\"") || s.contains("\n")) {
            return "\"" + s.replace("\"", "\"\"") + "\"";
        }
        return s;
    }

    public record CreateProjectRequest(
            UUID userId,
            @NotBlank String name,
            @NotBlank String projectType,
            @NotBlank String sourceType,
            String location,
            LocalDate baselineStart,
            LocalDate baselineFinish
    ) {}
}
