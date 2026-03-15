package com.example.construction.meetings;

import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;
import java.util.UUID;

public interface TaskMeetingRepository extends JpaRepository<TaskMeeting, UUID> {
    List<TaskMeeting> findByTaskIdOrderByStartTimeAscCreatedAtAsc(UUID taskId);
}
