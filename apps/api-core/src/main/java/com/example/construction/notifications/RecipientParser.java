package com.example.construction.notifications;

import java.util.Arrays;
import java.util.List;

public final class RecipientParser {
    private RecipientParser() {}

    public static List<String> split(String raw) {
        if (raw == null || raw.isBlank()) {
            return List.of();
        }
        return Arrays.stream(raw.split("[,;]"))
                .map(String::trim)
                .filter(v -> !v.isBlank())
                .distinct()
                .toList();
    }
}
