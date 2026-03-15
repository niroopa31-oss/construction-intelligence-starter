package com.example.construction.imports;

import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.*;

@Service
@RequiredArgsConstructor
public class ImportPreviewDraftService {
    private final ImportDraftRepository draftRepository;
    private final ImportDraftNodeRepository nodeRepository;

    @Transactional
    public DraftCreationResult createDraftFromPreview(String fileName,
                                                      UUID userId,
                                                      Map<String, Object> previewEnvelope,
                                                      String projectTypeOverride) {
        Map<String, Object> preview = castMap(previewEnvelope.get("preview"));
        String projectName = asString(preview.getOrDefault("project_name", fileName == null ? "Imported Project" : fileName));
        String sourceType = asString(preview.getOrDefault("source_type", inferSourceType(fileName)));
        String projectTypeSuggested = asString(preview.getOrDefault("project_type", "general construction"));

        ImportDraft draft = draftRepository.save(ImportDraft.builder()
                .userId(userId)
                .fileName(fileName)
                .sourceType(sourceType)
                .projectName(projectName)
                .projectTypeSuggested(projectTypeSuggested)
                .projectTypeSelected(blankToNull(projectTypeOverride))
                .status("draft")
                .build());

        List<Map<String, Object>> flatTasks = castListOfMaps(preview.get("flat_tasks"));
        if (flatTasks.isEmpty()) {
            flatTasks = castListOfMaps(preview.get("sample"));
        }

        List<Map<String, Object>> ordered = topologicalLikeOrder(flatTasks);
        Map<String, UUID> externalToNodeId = new LinkedHashMap<>();
        int sortOrder = 1;

        for (Map<String, Object> task : ordered) {
            String externalId = asString(task.get("external_id"));
            String externalParentId = asString(task.get("external_parent_id"));
            UUID parentId = externalParentId == null ? null : externalToNodeId.get(externalParentId);
            ImportDraftNode node = ImportDraftNode.builder()
                    .draftId(draft.getId())
                    .parentId(parentId)
                    .externalSourceId(externalId)
                    .name(asString(task.getOrDefault("name", "Untitled task")))
                    .nodeType(defaultNodeType(asString(task.get("node_type"))))
                    .phase(asString(task.get("phase")))
                    .discipline(asString(task.get("discipline")))
                    .tower(asString(task.get("tower")))
                    .blockName(asString(task.get("block")))
                    .floorName(asString(task.get("floor")))
                    .zoneName(asString(task.get("zone")))
                    .baselineStart(toLocalDate(task.get("planned_start")))
                    .baselineFinish(toLocalDate(task.get("planned_finish")))
                    .plannedQty(toBigDecimal(task.get("planned_qty")))
                    .uom(asString(task.get("uom")))
                    .confidenceScore(toBigDecimal(task.get("confidence")))
                    .sortOrder(sortOrder++)
                    .build();
            node = nodeRepository.save(node);
            if (externalId != null) {
                externalToNodeId.put(externalId, node.getId());
            }
        }

        return new DraftCreationResult(draft.getId(), draft.getProjectName(), ordered.size());
    }

    private List<Map<String, Object>> topologicalLikeOrder(List<Map<String, Object>> tasks) {
        List<Map<String, Object>> remaining = new ArrayList<>(tasks);
        List<Map<String, Object>> ordered = new ArrayList<>();
        Set<String> resolved = new LinkedHashSet<>();

        while (!remaining.isEmpty()) {
            int before = remaining.size();
            Iterator<Map<String, Object>> iterator = remaining.iterator();
            while (iterator.hasNext()) {
                Map<String, Object> candidate = iterator.next();
                String externalId = asString(candidate.get("external_id"));
                String parentId = asString(candidate.get("external_parent_id"));
                if (parentId == null || resolved.contains(parentId) || Objects.equals(parentId, externalId)) {
                    ordered.add(candidate);
                    if (externalId != null) {
                        resolved.add(externalId);
                    }
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

    @SuppressWarnings("unchecked")
    private Map<String, Object> castMap(Object value) {
        return value instanceof Map<?, ?> map ? (Map<String, Object>) map : Map.of();
    }

    @SuppressWarnings("unchecked")
    private List<Map<String, Object>> castListOfMaps(Object value) {
        if (!(value instanceof List<?> list)) {
            return List.of();
        }
        List<Map<String, Object>> result = new ArrayList<>();
        for (Object item : list) {
            if (item instanceof Map<?, ?> map) {
                result.add((Map<String, Object>) map);
            }
        }
        return result;
    }

    private String inferSourceType(String fileName) {
        if (fileName == null) {
            return "unknown";
        }
        String lower = fileName.toLowerCase(Locale.ROOT);
        if (lower.endsWith(".xml")) return "xml";
        if (lower.endsWith(".xlsx") || lower.endsWith(".xls") || lower.endsWith(".xlsm")) return "excel";
        return "unknown";
    }

    private String defaultNodeType(String value) {
        return switch (value == null ? "" : value.trim().toLowerCase(Locale.ROOT)) {
            case "stage", "task", "sub_task", "milestone", "summary" -> value;
            default -> "task";
        };
    }

    private String asString(Object value) {
        if (value == null) {
            return null;
        }
        String text = String.valueOf(value).trim();
        return text.isEmpty() || "null".equalsIgnoreCase(text) ? null : text;
    }

    private String blankToNull(String value) {
        return asString(value);
    }

    private LocalDate toLocalDate(Object value) {
        String text = asString(value);
        if (text == null) {
            return null;
        }
        try {
            return LocalDate.parse(text.substring(0, 10));
        } catch (Exception ignored) {
            return null;
        }
    }

    private BigDecimal toBigDecimal(Object value) {
        if (value == null) {
            return null;
        }
        try {
            return new BigDecimal(String.valueOf(value));
        } catch (Exception ignored) {
            return null;
        }
    }

    public record DraftCreationResult(UUID draftId, String projectName, int nodeCount) {}
}
