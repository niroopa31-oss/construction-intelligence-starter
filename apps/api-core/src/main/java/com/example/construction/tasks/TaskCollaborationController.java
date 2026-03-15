package com.example.construction.tasks;

import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;
import java.util.UUID;

@RestController
@RequestMapping("/api/projects/{projectId}/tasks/{taskId}/collaboration")
@RequiredArgsConstructor
public class TaskCollaborationController {
    private final TaskCollaborationService taskCollaborationService;

    @PostMapping("/assignments")
    public ResponseEntity<TaskDetailDto> assignContractor(
            @PathVariable UUID projectId,
            @PathVariable UUID taskId,
            @Valid @RequestBody TaskCollaborationDtos.AssignContractorRequest request
    ) {
        return ResponseEntity.ok(taskCollaborationService.assignContractor(projectId, taskId, request));
    }

    @DeleteMapping("/assignments/{assignmentId}")
    public ResponseEntity<TaskDetailDto> removeAssignment(
            @PathVariable UUID projectId,
            @PathVariable UUID taskId,
            @PathVariable UUID assignmentId
    ) {
        return ResponseEntity.ok(taskCollaborationService.removeAssignment(projectId, taskId, assignmentId));
    }

    @PostMapping("/meetings")
    public ResponseEntity<TaskDetailDto> createMeeting(
            @PathVariable UUID projectId,
            @PathVariable UUID taskId,
            @Valid @RequestBody TaskCollaborationDtos.CreateMeetingRequest request
    ) {
        return ResponseEntity.ok(taskCollaborationService.createMeeting(projectId, taskId, request));
    }

    @PostMapping("/meetings/{meetingId}/send-invite")
    public ResponseEntity<TaskDetailDto> sendMeetingInvite(
            @PathVariable UUID projectId,
            @PathVariable UUID taskId,
            @PathVariable UUID meetingId,
            @RequestBody(required = false) Map<String, String> request
    ) {
        return ResponseEntity.ok(taskCollaborationService.sendMeetingInvite(
                projectId,
                taskId,
                meetingId,
                request == null ? null : request.get("inviteBody")
        ));
    }

    @PostMapping("/reminders")
    public ResponseEntity<TaskDetailDto> createReminder(
            @PathVariable UUID projectId,
            @PathVariable UUID taskId,
            @Valid @RequestBody TaskCollaborationDtos.CreateReminderRequest request
    ) {
        return ResponseEntity.ok(taskCollaborationService.createReminder(projectId, taskId, request));
    }

    @PostMapping("/reminders/{reminderId}/send")
    public ResponseEntity<TaskDetailDto> sendReminder(
            @PathVariable UUID projectId,
            @PathVariable UUID taskId,
            @PathVariable UUID reminderId
    ) {
        return ResponseEntity.ok(taskCollaborationService.sendReminder(projectId, taskId, reminderId));
    }
}
