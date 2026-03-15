package com.example.construction.notifications;

import com.example.construction.meetings.TaskMeeting;

import java.nio.charset.StandardCharsets;
import java.time.ZoneId;
import java.time.format.DateTimeFormatter;
import java.util.UUID;

public class IcsCalendarInviteFactory {
    private static final DateTimeFormatter UTC_FORMAT = DateTimeFormatter.ofPattern("yyyyMMdd'T'HHmmss'Z'");

    public byte[] build(TaskMeeting meeting, NotificationProperties properties) {
        ZoneId zoneId = ZoneId.of(properties.calendar().timezone() == null || properties.calendar().timezone().isBlank()
                ? "UTC"
                : properties.calendar().timezone());
        String uid = meeting.getCalendarEventUid() == null || meeting.getCalendarEventUid().isBlank()
                ? UUID.randomUUID() + "@construction-intelligence"
                : meeting.getCalendarEventUid();
        String organizerEmail = properties.calendar().organizerEmail();
        String organizerName = properties.calendar().organizerName() == null ? "Construction Intelligence" : properties.calendar().organizerName();
        String start = meeting.getStartTime() == null ? "" : meeting.getStartTime().atZone(zoneId).withZoneSameInstant(ZoneId.of("UTC")).format(UTC_FORMAT);
        String end = meeting.getEndTime() == null ? "" : meeting.getEndTime().atZone(zoneId).withZoneSameInstant(ZoneId.of("UTC")).format(UTC_FORMAT);
        String description = escape(meeting.getAgenda());
        String summary = escape(meeting.getTitle());
        StringBuilder sb = new StringBuilder();
        sb.append("BEGIN:VCALENDAR\r\n")
          .append("PRODID:-//Construction Intelligence//Task Meetings//EN\r\n")
          .append("VERSION:2.0\r\n")
          .append("CALSCALE:GREGORIAN\r\n")
          .append("METHOD:REQUEST\r\n")
          .append("BEGIN:VEVENT\r\n")
          .append("UID:").append(uid).append("\r\n")
          .append("DTSTAMP:").append(java.time.ZonedDateTime.now(ZoneId.of("UTC")).format(UTC_FORMAT)).append("\r\n");
        if (!start.isBlank()) sb.append("DTSTART:").append(start).append("\r\n");
        if (!end.isBlank()) sb.append("DTEND:").append(end).append("\r\n");
        sb.append("SUMMARY:").append(summary).append("\r\n")
          .append("DESCRIPTION:").append(description).append("\r\n");
        if (organizerEmail != null && !organizerEmail.isBlank()) {
            sb.append("ORGANIZER;CN=").append(escape(organizerName)).append(":mailto:").append(organizerEmail).append("\r\n");
        }
        for (String attendee : RecipientParser.split(meeting.getAttendees())) {
            sb.append("ATTENDEE;CN=").append(attendee).append(";RSVP=TRUE:mailto:").append(attendee).append("\r\n");
        }
        sb.append("STATUS:CONFIRMED\r\n")
          .append("SEQUENCE:").append(meeting.getCalendarSequence() == null ? 0 : meeting.getCalendarSequence()).append("\r\n")
          .append("END:VEVENT\r\n")
          .append("END:VCALENDAR\r\n");
        return sb.toString().getBytes(StandardCharsets.UTF_8);
    }

    private String escape(String input) {
        if (input == null) return "";
        return input.replace("\\", "\\\\")
                .replace(";", "\\;")
                .replace(",", "\\,")
                .replace("\n", "\\n")
                .replace("\r", "");
    }
}
