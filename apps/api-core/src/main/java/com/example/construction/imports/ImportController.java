package com.example.construction.imports;

import com.example.construction.projects.Project;
import com.example.construction.projects.ProjectRepository;
import com.example.construction.tasks.Task;
import com.example.construction.tasks.TaskRepository;
import jakarta.transaction.Transactional;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.*;

@RestController
@RequestMapping("/api/imports")
@RequiredArgsConstructor
public class ImportController {
    private final ProjectRepository projectRepository;
    private final TaskRepository taskRepository;

    @PostMapping("/confirm")
    @Transactional
    public ConfirmImportResponse confirm(@RequestBody ConfirmImportRequest request) {
        Project project = Project.builder()
                .userId(request.project().userId())
                .name(request.project().name())
                .projectType(request.project().projectType())
                .sourceType(request.project().sourceType())
                .location(request.project().location())
                .baselineStart(request.project().baselineStart())
                .baselineFinish(request.project().baselineFinish())
                .status("active")
                .build();
        project = projectRepository.save(project);

        Map<String, UUID> idMap = new HashMap<>();
        List<ImportTaskDto> orderedTasks = topologicalLikeOrder(request.tasks());
        for (ImportTaskDto dto : orderedTasks) {
            UUID parentId = dto.external_parent_id() != null ? idMap.get(dto.external_parent_id()) : null;
            Task task = Task.builder()
                    .projectId(project.getId())
                    .parentId(parentId)
                    .externalSourceId(dto.external_id())
                    .externalParentId(dto.external_parent_id())
                    .name(dto.name())
                    .normalizedName(dto.normalized_name())
                    .nodeType(dto.node_type())
                    .phase(dto.phase())
                    .discipline(dto.discipline())
                    .tower(dto.tower())
                    .blockName(dto.block())
                    .floorName(dto.floor())
                    .zoneName(dto.zone())
                    .baselineStart(dto.planned_start())
                    .baselineFinish(dto.planned_finish())
                    .actualStart(dto.actual_start())
                    .actualFinish(dto.actual_finish())
                    .plannedQty(toBigDecimal(dto.planned_qty()))
                    .actualQty(toBigDecimal(dto.actual_qty()))
                    .uom(dto.uom())
                    .progressPercent(toBigDecimal(dto.actual_progress()))
                    .criticalFlag(false)
                    .confidenceScore(toBigDecimal(dto.confidence()))
                    .build();
            task = taskRepository.save(task);
            idMap.put(dto.external_id(), task.getId());
        }

        return new ConfirmImportResponse(project.getId(), orderedTasks.size(), "Project and tasks saved successfully");
    }

    private List<ImportTaskDto> topologicalLikeOrder(List<ImportTaskDto> tasks) {
        List<ImportTaskDto> remaining = new ArrayList<>(tasks);
        List<ImportTaskDto> ordered = new ArrayList<>();
        Set<String> resolved = new HashSet<>();

        while (!remaining.isEmpty()) {
            int before = remaining.size();
            Iterator<ImportTaskDto> iterator = remaining.iterator();
            while (iterator.hasNext()) {
                ImportTaskDto candidate = iterator.next();
                if (candidate.external_parent_id() == null || resolved.contains(candidate.external_parent_id())) {
                    ordered.add(candidate);
                    resolved.add(candidate.external_id());
                    iterator.remove();
                }
            }
            if (remaining.size() == before) {
                ordered.addAll(remaining);
                break;
            }
        }
        return ordered;
    }

    private BigDecimal toBigDecimal(Number value) {
        return value == null ? null : BigDecimal.valueOf(value.doubleValue());
    }

    public record ConfirmImportRequest(ProjectImportDto project, List<ImportTaskDto> tasks) {}

    public record ProjectImportDto(
            UUID userId,
            String name,
            String projectType,
            String sourceType,
            String location,
            LocalDate baselineStart,
            LocalDate baselineFinish
    ) {}

    public record ImportTaskDto(
            String external_id,
            String external_parent_id,
            String source_type,
            String source_sheet,
            Integer source_row,
            String name,
            String normalized_name,
            String node_type,
            String project_hint,
            String tower,
            String block,
            String floor,
            String zone,
            String phase,
            String discipline,
            LocalDate planned_start,
            LocalDate planned_finish,
            LocalDate actual_start,
            LocalDate actual_finish,
            Double actual_progress,
            Double planned_qty,
            Double actual_qty,
            String uom,
            String contractor,
            String remarks,
            Double confidence
    ) {}

    public record ConfirmImportResponse(UUID projectId, int taskCount, String message) {}
}