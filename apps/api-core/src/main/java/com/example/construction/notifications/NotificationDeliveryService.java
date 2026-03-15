package com.example.construction.notifications;

import com.example.construction.meetings.TaskMeeting;
import com.example.construction.reminders.TaskReminder;
import jakarta.mail.Message;
import jakarta.mail.internet.InternetAddress;
import jakarta.mail.internet.MimeBodyPart;
import jakarta.mail.internet.MimeMessage;
import jakarta.mail.internet.MimeMultipart;
import lombok.RequiredArgsConstructor;
import org.springframework.mail.javamail.JavaMailSender;
import org.springframework.stereotype.Service;

import java.nio.charset.StandardCharsets;
import java.util.List;

@Service
@RequiredArgsConstructor
public class NotificationDeliveryService {
    private final JavaMailSender javaMailSender;
    private final NotificationProperties properties;
    private final IcsCalendarInviteFactory icsFactory = new IcsCalendarInviteFactory();

    public void sendReminder(TaskReminder reminder) {
        if (properties.mail() == null || !properties.mail().enabled()) {
            return;
        }
        List<String> recipients = RecipientParser.split(reminder.getRecipients());
        if (recipients.isEmpty()) {
            return;
        }

        MimeMessage message = javaMailSender.createMimeMessage();
        try {
            message.setFrom(new InternetAddress(properties.mail().fromAddress(), properties.mail().fromName(), StandardCharsets.UTF_8.name()));
            message.setRecipients(Message.RecipientType.TO, InternetAddress.parse(String.join(",", recipients)));
            message.setSubject(reminder.getSubject(), StandardCharsets.UTF_8.name());
            message.setText(reminder.getBody() == null ? "" : reminder.getBody(), StandardCharsets.UTF_8.name(), "html");
            javaMailSender.send(message);
        } catch (Exception ex) {
            throw new IllegalStateException("Failed to send reminder email", ex);
        }
    }

    public void sendMeetingInvite(TaskMeeting meeting, String bodyHtml) {
        if (properties.mail() == null || !properties.mail().enabled()) {
            return;
        }
        List<String> recipients = RecipientParser.split(meeting.getAttendees());
        if (recipients.isEmpty()) {
            return;
        }

        MimeMessage message = javaMailSender.createMimeMessage();
        try {
            message.setFrom(new InternetAddress(properties.mail().fromAddress(), properties.mail().fromName(), StandardCharsets.UTF_8.name()));
            message.setRecipients(Message.RecipientType.TO, InternetAddress.parse(String.join(",", recipients)));
            message.setSubject(meeting.getTitle(), StandardCharsets.UTF_8.name());

            MimeBodyPart body = new MimeBodyPart();
            body.setContent(bodyHtml == null ? "" : bodyHtml, "text/html; charset=UTF-8");

            MimeBodyPart calendarPart = new MimeBodyPart();
            calendarPart.setDataHandler(new jakarta.activation.DataHandler(
                    new jakarta.mail.util.ByteArrayDataSource(icsFactory.build(meeting, properties), "text/calendar;method=REQUEST;charset=UTF-8")
            ));
            calendarPart.setFileName("invite.ics");

            MimeMultipart multipart = new MimeMultipart("mixed");
            multipart.addBodyPart(body);
            multipart.addBodyPart(calendarPart);
            message.setContent(multipart);

            javaMailSender.send(message);
        } catch (Exception ex) {
            throw new IllegalStateException("Failed to send meeting invite", ex);
        }
    }
}
