package com.example.construction.tasks;

import com.example.construction.contractors.Contractor;
import com.example.construction.contractors.ContractorRepository;
import com.example.construction.meetings.TaskMeetingRepository;
import com.example.construction.projects.Project;
import com.example.construction.projects.ProjectRepository;
import com.example.construction.reminders.TaskReminderRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.*;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class TaskTreeService {
    private final TaskRepository taskRepository;
    private final ProjectRepository projectRepository;
    private final ContractorRepository contractorRepository;
    private final TaskAssignmentRepository taskAssignmentRepository;
    private final TaskMeetingRepository taskMeetingRepository;
    private final TaskReminderRepository taskReminderRepository;

    public ProjectSummaryDto projectSummary(UUID projectId) {
        Project project = projectRepository.findById(projectId)
                .orElseThrow(() -> new NoSuchElementException("Project not found"));

        List<Task> tasks = taskRepository.findByProjectIdOrderByCreatedAtAsc(projectId);
        long total = tasks.size();
        long completed = tasks.stream().filter(t -> "completed".equals(TaskViewLogic.inferStatus(t))).count();
        long delayed = tasks.stream().filter(t -> "delayed".equals(TaskViewLogic.inferStatus(t))).count();
        long milestones = tasks.stream().filter(t -> "milestone".equalsIgnoreCase(t.getNodeType())).count();
        long highRisk = tasks.stream().filter(t -> List.of("delayed", "at-risk").contains(TaskViewLogic.inferStatus(t))).count();
        double progress = tasks.stream().map(Task::getProgressPercent).filter(Objects::nonNull).mapToDouble(BigDecimal::doubleValue).average().orElse(0.0);

        LocalDate forecastFinish = tasks.stream().map(Task::getForecastFinish).filter(Objects::nonNull).max(LocalDate::compareTo).orElse(project.getForecastFinish());

        return new ProjectSummaryDto(project.getId(), project.getName(), project.getProjectType(), project.getBaselineFinish(), forecastFinish, total, completed, delayed, milestones, highRisk, progress);
    }

    public List<TaskSummaryDto> taskTree(UUID projectId) {
        List<Task> tasks = taskRepository.findByProjectIdOrderByCreatedAtAsc(projectId);
        Map<UUID, List<String>> contractorNamesByTask = contractorNamesByTask(tasks);
        Map<UUID, TaskSummaryDto> dtoMap = tasks.stream()
                .map(task -> TaskSummaryDto.fromTask(task, contractorNamesByTask.getOrDefault(task.getId(), List.of())))
                .collect(Collectors.toMap(TaskSummaryDto::id, dto -> dto, (a, b) -> a, LinkedHashMap::new));

        List<TaskSummaryDto> roots = new ArrayList<>();
        for (TaskSummaryDto dto : dtoMap.values()) {
            if (dto.parentId() != null && dtoMap.containsKey(dto.parentId())) dtoMap.get(dto.parentId()).children().add(dto);
            else roots.add(dto);
        }
        return roots;
    }

    public TaskDetailDto taskDetail(UUID projectId, UUID taskId) {
        List<Task> tasks = taskRepository.findByProjectIdOrderByCreatedAtAsc(projectId);
        Task target = tasks.stream().filter(t -> t.getId().equals(taskId)).findFirst().orElseThrow(() -> new NoSuchElementException("Task not found"));
        Map<UUID, Task> taskMap = tasks.stream().collect(Collectors.toMap(Task::getId, t -> t));
        List<String> path = buildPath(target, taskMap);
        Map<UUID, Contractor> contractorsById = contractorRepository.findByProjectIdOrderByCompanyNameAsc(projectId).stream().collect(Collectors.toMap(Contractor::getId, c -> c));

        List<TaskAssignment> assignments = taskAssignmentRepository.findByTaskIdOrderByCreatedAtAsc(taskId);
        List<TaskDetailDto.ContractorAssignmentDto> assignmentDtos = assignments.stream().map(assignment -> {
            Contractor contractor = contractorsById.get(assignment.getContractorId());
            if (contractor == null) return null;
            return new TaskDetailDto.ContractorAssignmentDto(assignment.getId(), contractor.getId(), contractor.getCompanyName(), contractor.getContactName(), contractor.getEmail(), assignment.getRoleName());
        }).filter(Objects::nonNull).toList();

        List<String> contractorNames = assignmentDtos.stream().map(TaskDetailDto.ContractorAssignmentDto::companyName).distinct().toList();
        List<TaskDetailDto.ContractorOptionDto> contractorOptions = contractorsById.values().stream()
                .sorted(Comparator.comparing(Contractor::getCompanyName, String.CASE_INSENSITIVE_ORDER))
                .map(contractor -> new TaskDetailDto.ContractorOptionDto(contractor.getId(), contractor.getCompanyName(), contractor.getContactName(), contractor.getEmail(), contractor.getTradeType()))
                .toList();

        List<TaskDetailDto.MeetingDto> meetings = taskMeetingRepository.findByTaskIdOrderByStartTimeAscCreatedAtAsc(taskId).stream()
                .map(meeting -> new TaskDetailDto.MeetingDto(meeting.getId(), meeting.getTitle(), meeting.getAgenda(), meeting.getStartTime(), meeting.getEndTime(), meeting.getAttendees(), meeting.getStatus(), meeting.getInviteSentAt(), meeting.getCalendarEventUid()))
                .toList();

        List<TaskDetailDto.ReminderDto> reminders = taskReminderRepository.findByTaskIdOrderByScheduledAtAscCreatedAtAsc(taskId).stream()
                .map(reminder -> new TaskDetailDto.ReminderDto(reminder.getId(), reminder.getSubject(), reminder.getBody(), reminder.getRecipients(), reminder.getScheduledAt(), reminder.getSentAt(), reminder.getStatus(), reminder.getSendError()))
                .toList();

        List<String> aiSuggestions = buildAiSuggestions(target, assignmentDtos, meetings, reminders);
        String status = TaskViewLogic.inferStatus(target);
        return new TaskDetailDto(target.getId(), target.getProjectId(), target.getParentId(), target.getName(), target.getNodeType(), target.getPhase(), target.getDiscipline(), target.getTower(), target.getFloorName(), target.getZoneName(), target.getBaselineStart(), target.getBaselineFinish(), target.getActualStart(), target.getActualFinish(), target.getForecastFinish(), target.getProgressPercent(), target.getPlannedQty(), target.getActualQty(), target.getUom(), target.isCriticalFlag(), target.getConfidenceScore(), status, TaskViewLogic.delayedDays(target), path, contractorNames, List.of(), List.of(), List.of(), aiSuggestions, assignmentDtos, contractorOptions, meetings, reminders);
    }

    @org.springframework.transaction.annotation.Transactional
    public TaskDetailDto updateTask(UUID projectId, UUID taskId, Map<String, Object> updates) {
        Task task = taskRepository.findById(taskId)
                .filter(t -> t.getProjectId().equals(projectId))
                .orElseThrow(() -> new NoSuchElementException("Task not found"));

        if (updates.containsKey("name")) task.setName((String) updates.get("name"));
        if (updates.containsKey("phase")) task.setPhase((String) updates.get("phase"));
        if (updates.containsKey("discipline")) task.setDiscipline((String) updates.get("discipline"));
        if (updates.containsKey("tower")) task.setTower((String) updates.get("tower"));
        if (updates.containsKey("floorName")) task.setFloorName((String) updates.get("floorName"));
        if (updates.containsKey("zoneName")) task.setZoneName((String) updates.get("zoneName"));
        if (updates.containsKey("baselineStart")) task.setBaselineStart(parseDate(updates.get("baselineStart")));
        if (updates.containsKey("baselineFinish")) task.setBaselineFinish(parseDate(updates.get("baselineFinish")));
        if (updates.containsKey("actualStart")) task.setActualStart(parseDate(updates.get("actualStart")));
        if (updates.containsKey("actualFinish")) task.setActualFinish(parseDate(updates.get("actualFinish")));
        if (updates.containsKey("forecastFinish")) task.setForecastFinish(parseDate(updates.get("forecastFinish")));
        if (updates.containsKey("plannedQty")) task.setPlannedQty(parseBigDecimal(updates.get("plannedQty")));
        if (updates.containsKey("actualQty")) task.setActualQty(parseBigDecimal(updates.get("actualQty")));
        if (updates.containsKey("uom")) task.setUom((String) updates.get("uom"));
        if (updates.containsKey("progressPercent")) task.setProgressPercent(parseBigDecimal(updates.get("progressPercent")));
        if (updates.containsKey("criticalFlag")) task.setCriticalFlag(Boolean.TRUE.equals(updates.get("criticalFlag")));

        taskRepository.save(task);
        return taskDetail(projectId, taskId);
    }

    private LocalDate parseDate(Object value) {
        if (value == null || "".equals(value)) return null;
        return LocalDate.parse(value.toString());
    }

    private BigDecimal parseBigDecimal(Object value) {
        if (value == null || "".equals(value)) return null;
        return new BigDecimal(value.toString());
    }

    private Map<UUID, List<String>> contractorNamesByTask(List<Task> tasks) {
        UUID projectId = tasks.stream().findFirst().map(Task::getProjectId).orElse(null);
        Map<UUID, String> contractorNameMap = projectId == null ? Map.of() : contractorRepository.findByProjectIdOrderByCompanyNameAsc(projectId).stream().collect(Collectors.toMap(Contractor::getId, Contractor::getCompanyName));
        return tasks.stream().map(Task::getId).collect(Collectors.toMap(taskId -> taskId, taskId -> taskAssignmentRepository.findByTaskIdOrderByCreatedAtAsc(taskId).stream().map(TaskAssignment::getContractorId).map(contractorNameMap::get).filter(Objects::nonNull).distinct().toList()));
    }

    private List<String> buildAiSuggestions(Task target, List<TaskDetailDto.ContractorAssignmentDto> assignments, List<TaskDetailDto.MeetingDto> meetings, List<TaskDetailDto.ReminderDto> reminders) {
        List<String> aiSuggestions = new ArrayList<>();
        String status = TaskViewLogic.inferStatus(target);
        if (assignments.isEmpty()) aiSuggestions.add("Assign a contractor owner so reminders and meeting agendas can be targeted automatically.");
        if (meetings.isEmpty() && List.of("delayed", "at-risk").contains(status)) aiSuggestions.add("Schedule a recovery meeting and send the calendar invite immediately so commitments are tracked.");
        if (reminders.stream().noneMatch(r -> "sent".equalsIgnoreCase(r.status())) && !assignments.isEmpty()) aiSuggestions.add("Send a reminder to the assigned contractor before the next daily review.");
        if ("delayed".equals(status)) aiSuggestions.add("Split the work into parallel zones and increase manpower for the next 3 working days to reduce slippage.");
        else if ("at-risk".equals(status)) aiSuggestions.add("Update actual progress and upload fresh site photos so the forecast can be recalculated with better confidence.");
        else aiSuggestions.add("Keep meetings, reminders, and evidence linked here so this task stays audit-ready.");
        return aiSuggestions;
    }

    private List<String> buildPath(Task task, Map<UUID, Task> taskMap) {
        LinkedList<String> path = new LinkedList<>();
        Task current = task;
        while (current != null) {
            path.addFirst(current.getName());
            current = current.getParentId() == null ? null : taskMap.get(current.getParentId());
        }
        return path;
    }
}
