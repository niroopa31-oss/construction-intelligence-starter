package com.example.construction.notifications;

import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties(prefix = "app.notifications")
public record NotificationProperties(
        Mail mail,
        Calendar calendar
) {
    public record Mail(String fromAddress, String fromName, boolean enabled) {}
    public record Calendar(String organizerEmail, String organizerName, String timezone) {}
}
