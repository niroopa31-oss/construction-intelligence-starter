package com.example.construction.tasks;

import com.example.construction.contractors.Contractor;
import com.example.construction.contractors.ContractorRepository;
import com.example.construction.meetings.TaskMeeting;
import com.example.construction.meetings.TaskMeetingRepository;
import com.example.construction.notifications.NotificationDeliveryService;
import com.example.construction.reminders.TaskReminder;
import com.example.construction.reminders.TaskReminderRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.NoSuchElementException;
import java.util.UUID;

@Service
@RequiredArgsConstructor
public class TaskCollaborationService {
    private final TaskRepository taskRepository;
    private final ContractorRepository contractorRepository;
    private final TaskAssignmentRepository taskAssignmentRepository;
    private final TaskMeetingRepository taskMeetingRepository;
    private final TaskReminderRepository taskReminderRepository;
    private final TaskTreeService taskTreeService;
    private final NotificationDeliveryService notificationDeliveryService;

    public TaskDetailDto assignContractor(UUID projectId, UUID taskId, TaskCollaborationDtos.AssignContractorRequest request) {
        requireTask(projectId, taskId);
        Contractor contractor = contractorRepository.findById(request.contractorId())
                .filter(c -> c.getProjectId().equals(projectId))
                .orElseThrow(() -> new NoSuchElementException("Contractor not found"));

        boolean exists = taskAssignmentRepository.findByTaskIdOrderByCreatedAtAsc(taskId).stream()
                .anyMatch(assignment -> assignment.getContractorId().equals(contractor.getId()));

        if (!exists) {
            taskAssignmentRepository.save(TaskAssignment.builder()
                    .taskId(taskId)
                    .contractorId(contractor.getId())
                    .roleName(request.roleName())
                    .build());
        }
        return taskTreeService.taskDetail(projectId, taskId);
    }

    public TaskDetailDto removeAssignment(UUID projectId, UUID taskId, UUID assignmentId) {
        requireTask(projectId, taskId);
        taskAssignmentRepository.deleteByIdAndTaskId(assignmentId, taskId);
        return taskTreeService.taskDetail(projectId, taskId);
    }

    @Transactional
    public TaskDetailDto createMeeting(UUID projectId, UUID taskId, TaskCollaborationDtos.CreateMeetingRequest request) {
        requireTask(projectId, taskId);
        TaskMeeting meeting = taskMeetingRepository.save(TaskMeeting.builder()
                .taskId(taskId)
                .title(request.title())
                .agenda(request.agenda())
                .startTime(request.startTime())
                .endTime(request.endTime())
                .attendees(request.attendees())
                .status(request.status() == null || request.status().isBlank() ? "scheduled" : request.status())
                .calendarSequence(0)
                .build());

        if (Boolean.TRUE.equals(request.sendInviteNow())) {
            sendMeetingInviteInternal(meeting, request.inviteBody());
        }
        return taskTreeService.taskDetail(projectId, taskId);
    }

    @Transactional
    public TaskDetailDto sendMeetingInvite(UUID projectId, UUID taskId, UUID meetingId, String inviteBody) {
        requireTask(projectId, taskId);
        TaskMeeting meeting = taskMeetingRepository.findById(meetingId)
                .filter(m -> m.getTaskId().equals(taskId))
                .orElseThrow(() -> new NoSuchElementException("Meeting not found"));
        sendMeetingInviteInternal(meeting, inviteBody);
        return taskTreeService.taskDetail(projectId, taskId);
    }

    @Transactional
    public TaskDetailDto createReminder(UUID projectId, UUID taskId, TaskCollaborationDtos.CreateReminderRequest request) {
        requireTask(projectId, taskId);
        TaskReminder reminder = taskReminderRepository.save(TaskReminder.builder()
                .taskId(taskId)
                .subject(request.subject())
                .body(request.body())
                .recipients(request.recipients())
                .scheduledAt(request.scheduledAt())
                .status(request.status() == null || request.status().isBlank() ? "draft" : request.status())
                .build());

        if (Boolean.TRUE.equals(request.sendNow())) {
            sendReminderInternal(reminder);
        }
        return taskTreeService.taskDetail(projectId, taskId);
    }

    @Transactional
    public TaskDetailDto sendReminder(UUID projectId, UUID taskId, UUID reminderId) {
        requireTask(projectId, taskId);
        TaskReminder reminder = taskReminderRepository.findById(reminderId)
                .filter(r -> r.getTaskId().equals(taskId))
                .orElseThrow(() -> new NoSuchElementException("Reminder not found"));
        sendReminderInternal(reminder);
        return taskTreeService.taskDetail(projectId, taskId);
    }

    private void sendMeetingInviteInternal(TaskMeeting meeting, String inviteBody) {
        notificationDeliveryService.sendMeetingInvite(meeting, inviteBody == null || inviteBody.isBlank()
                ? defaultMeetingBody(meeting)
                : inviteBody);
        meeting.setInviteSentAt(LocalDateTime.now());
        meeting.setCalendarSequence((meeting.getCalendarSequence() == null ? 0 : meeting.getCalendarSequence()) + 1);
        meeting.setStatus("invite_sent");
        if (meeting.getCalendarEventUid() == null || meeting.getCalendarEventUid().isBlank()) {
            meeting.setCalendarEventUid(UUID.randomUUID() + "@construction-intelligence");
        }
        taskMeetingRepository.save(meeting);
    }

    private void sendReminderInternal(TaskReminder reminder) {
        try {
            notificationDeliveryService.sendReminder(reminder);
            reminder.setSentAt(LocalDateTime.now());
            reminder.setStatus("sent");
            reminder.setSendError(null);
        } catch (RuntimeException ex) {
            reminder.setStatus("failed");
            reminder.setSendError(ex.getMessage());
        }
        taskReminderRepository.save(reminder);
    }

    private String defaultMeetingBody(TaskMeeting meeting) {
        return "<p>Please join the task coordination meeting.</p>"
                + "<p><strong>Agenda:</strong><br/>" + (meeting.getAgenda() == null ? "-" : meeting.getAgenda()) + "</p>";
    }

    private void requireTask(UUID projectId, UUID taskId) {
        taskRepository.findById(taskId)
                .filter(task -> task.getProjectId().equals(projectId))
                .orElseThrow(() -> new NoSuchElementException("Task not found"));
    }
}
