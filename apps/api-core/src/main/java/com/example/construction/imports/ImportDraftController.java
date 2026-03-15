package com.example.construction.imports;

import com.example.construction.projects.Project;
import com.example.construction.projects.ProjectRepository;
import com.example.construction.tasks.Task;
import com.example.construction.tasks.TaskRepository;
import jakarta.transaction.Transactional;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.server.ResponseStatusException;

import java.time.LocalDate;
import java.util.*;

@RestController
@RequestMapping("/api/import-drafts")
@RequiredArgsConstructor
public class ImportDraftController {

    private final ImportDraftRepository draftRepository;
    private final ImportDraftNodeRepository nodeRepository;
    private final ProjectRepository projectRepository;
    private final TaskRepository taskRepository;

    // ─── GET draft summary with tree ───────────────────────────────
    @GetMapping("/{draftId}")
    public Map<String, Object> getDraft(@PathVariable UUID draftId) {
        ImportDraft draft = draftRepository.findById(draftId)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Draft not found"));

        List<ImportDraftNode> nodes = nodeRepository.findByDraftIdOrderBySortOrder(draftId);
        List<Map<String, Object>> tree = buildTree(nodes);

        Map<String, Object> result = new LinkedHashMap<>();
        result.put("draftId", draft.getId().toString());
        result.put("projectName", draft.getProjectName());
        result.put("projectTypeSuggested", draft.getProjectTypeSuggested());
        result.put("projectTypeSelected", draft.getProjectTypeSelected());
        result.put("status", draft.getStatus());
        result.put("nodeCount", nodes.size());
        result.put("tree", tree);
        return result;
    }

    // ─── ADD child node ────────────────────────────────────────────
    @PostMapping("/{draftId}/nodes")
    @Transactional
    public Map<String, Object> addNode(@PathVariable UUID draftId,
                                       @RequestBody Map<String, Object> body) {
        assertDraftExists(draftId);
        int maxSort = nodeRepository.findByDraftIdOrderBySortOrder(draftId).stream()
                .mapToInt(ImportDraftNode::getSortOrder).max().orElse(0);

        ImportDraftNode node = ImportDraftNode.builder()
                .draftId(draftId)
                .parentId(toUUID(body.get("parentId")))
                .name(asString(body.getOrDefault("name", "Untitled")))
                .nodeType(asString(body.getOrDefault("nodeType", "task")))
                .tower(asString(body.get("tower")))
                .floorName(asString(body.get("floorName")))
                .phase(asString(body.get("phase")))
                .baselineStart(toLocalDate(body.get("baselineStart")))
                .baselineFinish(toLocalDate(body.get("baselineFinish")))
                .sortOrder(maxSort + 1)
                .build();
        node = nodeRepository.save(node);
        return nodeToMap(node);
    }

    // ─── UPDATE node ───────────────────────────────────────────────
    @PatchMapping("/{draftId}/nodes/{nodeId}")
    @Transactional
    public Map<String, Object> updateNode(@PathVariable UUID draftId,
                                          @PathVariable UUID nodeId,
                                          @RequestBody Map<String, Object> body) {
        ImportDraftNode node = nodeRepository.findById(nodeId)
                .filter(n -> n.getDraftId().equals(draftId))
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Node not found"));

        if (body.containsKey("name")) node.setName(asString(body.get("name")));
        if (body.containsKey("nodeType")) node.setNodeType(asString(body.get("nodeType")));
        if (body.containsKey("tower")) node.setTower(asString(body.get("tower")));
        if (body.containsKey("floorName")) node.setFloorName(asString(body.get("floorName")));
        if (body.containsKey("phase")) node.setPhase(asString(body.get("phase")));
        if (body.containsKey("baselineStart")) node.setBaselineStart(toLocalDate(body.get("baselineStart")));
        if (body.containsKey("baselineFinish")) node.setBaselineFinish(toLocalDate(body.get("baselineFinish")));
        if (body.containsKey("sortOrder")) node.setSortOrder(((Number) body.get("sortOrder")).intValue());

        node = nodeRepository.save(node);
        return nodeToMap(node);
    }

    // ─── MOVE node ─────────────────────────────────────────────────
    @PostMapping("/{draftId}/nodes/{nodeId}/move")
    @Transactional
    public void moveNode(@PathVariable UUID draftId,
                         @PathVariable UUID nodeId,
                         @RequestBody Map<String, Object> body) {
        ImportDraftNode node = nodeRepository.findById(nodeId)
                .filter(n -> n.getDraftId().equals(draftId))
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Node not found"));

        if (body.containsKey("newParentId")) node.setParentId(toUUID(body.get("newParentId")));
        if (body.containsKey("newSortOrder")) node.setSortOrder(((Number) body.get("newSortOrder")).intValue());
        nodeRepository.save(node);
    }

    // ─── DELETE node ───────────────────────────────────────────────
    @DeleteMapping("/{draftId}/nodes/{nodeId}")
    @Transactional
    public void deleteNode(@PathVariable UUID draftId,
                           @PathVariable UUID nodeId,
                           @RequestBody(required = false) Map<String, Object> body) {
        ImportDraftNode node = nodeRepository.findById(nodeId)
                .filter(n -> n.getDraftId().equals(draftId))
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Node not found"));

        boolean cascade = body != null && Boolean.TRUE.equals(body.get("cascade"));
        boolean moveChildren = body != null && Boolean.TRUE.equals(body.get("moveChildrenToParent"));

        List<ImportDraftNode> children = nodeRepository.findByDraftIdOrderBySortOrder(draftId).stream()
                .filter(n -> nodeId.equals(n.getParentId()))
                .toList();

        if (!children.isEmpty() && !cascade && !moveChildren) {
            throw new ResponseStatusException(HttpStatus.CONFLICT,
                    "Node has children. Use cascade=true or moveChildrenToParent=true.");
        }

        if (cascade) {
            deleteSubtree(draftId, nodeId);
        } else {
            if (moveChildren) {
                for (ImportDraftNode child : children) {
                    child.setParentId(node.getParentId());
                    nodeRepository.save(child);
                }
            }
            nodeRepository.delete(node);
        }
    }

    // ─── CONFIRM draft → create real project ───────────────────────
    @PostMapping("/{draftId}/confirm")
    @Transactional
    public Map<String, Object> confirmDraft(@PathVariable UUID draftId,
                               @RequestBody Map<String, Object> body) {
        ImportDraft draft = draftRepository.findById(draftId)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Draft not found"));

        if ("confirmed".equals(draft.getStatus())) {
            throw new ResponseStatusException(HttpStatus.CONFLICT, "Draft already confirmed.");
        }

        String projectName = asString(body.getOrDefault("projectName", draft.getProjectName()));
        String projectType = asString(body.getOrDefault("projectTypeSelected", draft.getProjectTypeSuggested()));
        UUID userId = toUUID(body.getOrDefault("userId", draft.getUserId().toString()));

        Project project = Project.builder()
                .userId(userId)
                .name(projectName)
                .projectType(projectType)
                .sourceType(draft.getSourceType())
                .status("active")
                .build();
        project = projectRepository.save(project);

        List<ImportDraftNode> nodes = nodeRepository.findByDraftIdOrderBySortOrder(draftId);
        Map<UUID, UUID> draftNodeToTaskId = new LinkedHashMap<>();
        for (ImportDraftNode node : nodes) {
            UUID parentTaskId = node.getParentId() == null ? null : draftNodeToTaskId.get(node.getParentId());
            Task task = Task.builder()
                    .projectId(project.getId())
                    .parentId(parentTaskId)
                    .externalSourceId(node.getExternalSourceId())
                    .name(node.getName())
                    .nodeType(node.getNodeType())
                    .phase(node.getPhase())
                    .discipline(node.getDiscipline())
                    .tower(node.getTower())
                    .blockName(node.getBlockName())
                    .floorName(node.getFloorName())
                    .zoneName(node.getZoneName())
                    .baselineStart(node.getBaselineStart())
                    .baselineFinish(node.getBaselineFinish())
                    .plannedQty(node.getPlannedQty())
                    .uom(node.getUom())
                    .confidenceScore(node.getConfidenceScore())
                    .criticalFlag(false)
                    .build();
            task = taskRepository.save(task);
            draftNodeToTaskId.put(node.getId(), task.getId());
        }

        draft.setStatus("confirmed");
        draft.setProjectTypeSelected(projectType);
        draftRepository.save(draft);

        Map<String, Object> result = new LinkedHashMap<>();
        result.put("projectId", project.getId().toString());
        result.put("projectName", project.getName());
        result.put("taskCount", draftNodeToTaskId.size());
        return result;
    }

    // ─── helpers ───────────────────────────────────────────────────

    private void assertDraftExists(UUID draftId) {
        if (!draftRepository.existsById(draftId)) {
            throw new ResponseStatusException(HttpStatus.NOT_FOUND, "Draft not found");
        }
    }

    private void deleteSubtree(UUID draftId, UUID parentId) {
        List<ImportDraftNode> children = nodeRepository.findByDraftIdOrderBySortOrder(draftId).stream()
                .filter(n -> parentId.equals(n.getParentId()))
                .toList();
        for (ImportDraftNode child : children) {
            deleteSubtree(draftId, child.getId());
        }
        nodeRepository.deleteById(parentId);
    }

    private List<Map<String, Object>> buildTree(List<ImportDraftNode> nodes) {
        Map<UUID, Map<String, Object>> nodeMap = new LinkedHashMap<>();
        for (ImportDraftNode n : nodes) {
            Map<String, Object> m = nodeToMap(n);
            m.put("children", new ArrayList<>());
            nodeMap.put(n.getId(), m);
        }
        List<Map<String, Object>> roots = new ArrayList<>();
        for (ImportDraftNode n : nodes) {
            Map<String, Object> m = nodeMap.get(n.getId());
            if (n.getParentId() != null && nodeMap.containsKey(n.getParentId())) {
                @SuppressWarnings("unchecked")
                List<Map<String, Object>> siblings = (List<Map<String, Object>>) nodeMap.get(n.getParentId()).get("children");
                siblings.add(m);
            } else {
                roots.add(m);
            }
        }
        return roots;
    }

    private Map<String, Object> nodeToMap(ImportDraftNode n) {
        Map<String, Object> m = new LinkedHashMap<>();
        m.put("id", n.getId().toString());
        m.put("parentId", n.getParentId() == null ? null : n.getParentId().toString());
        m.put("name", n.getName());
        m.put("nodeType", n.getNodeType());
        m.put("tower", n.getTower());
        m.put("floorName", n.getFloorName());
        m.put("phase", n.getPhase());
        m.put("baselineStart", n.getBaselineStart() == null ? null : n.getBaselineStart().toString());
        m.put("baselineFinish", n.getBaselineFinish() == null ? null : n.getBaselineFinish().toString());
        m.put("sortOrder", n.getSortOrder());
        return m;
    }

    private String asString(Object value) {
        return value == null ? null : value.toString().isBlank() ? null : value.toString();
    }

    private UUID toUUID(Object value) {
        if (value == null) return null;
        String s = value.toString().trim();
        return s.isEmpty() ? null : UUID.fromString(s);
    }

    private LocalDate toLocalDate(Object value) {
        if (value == null) return null;
        String s = value.toString().trim();
        return s.isEmpty() ? null : LocalDate.parse(s);
    }
}
