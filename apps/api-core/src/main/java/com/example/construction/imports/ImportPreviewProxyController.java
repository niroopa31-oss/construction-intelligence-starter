package com.example.construction.imports;

import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.http.*;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.UUID;

@RestController
@RequestMapping("/api/imports")
@RequiredArgsConstructor
public class ImportPreviewProxyController {
    @Value("${app.aiImportServiceBaseUrl}")
    private String aiImportServiceBaseUrl;

    private final ImportPreviewDraftService importPreviewDraftService;

    @PostMapping(value = "/preview", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public Map<String, Object> preview(@RequestPart("file") MultipartFile file,
                                       @RequestParam(required = false) String projectType,
                                       @RequestParam(required = false) String projectName,
                                       @RequestParam(required = false) UUID userId,
                                       @RequestParam(defaultValue = "true") boolean createDraft) throws IOException {

        // Build multipart body for the Python AI service
        MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();
        ByteArrayResource fileResource = new ByteArrayResource(file.getBytes()) {
            @Override
            public String getFilename() {
                return file.getOriginalFilename();
            }
        };
        body.add("file", fileResource);
        if (projectType != null && !projectType.isBlank()) {
            body.add("projectType", projectType);
        }
        // Always send the original filename as project name hint so the Python
        // service doesn't fall back to the temp-file path.
        String effectiveProjectName = (projectName != null && !projectName.isBlank())
                ? projectName
                : stripExtension(file.getOriginalFilename());
        if (effectiveProjectName != null && !effectiveProjectName.isBlank()) {
            body.add("projectName", effectiveProjectName);
        }

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.MULTIPART_FORM_DATA);
        HttpEntity<MultiValueMap<String, Object>> requestEntity = new HttpEntity<>(body, headers);

        RestTemplate restTemplate = new RestTemplate();
        ResponseEntity<Map> responseEntity = restTemplate.postForEntity(
                aiImportServiceBaseUrl + "/api/imports/preview",
                requestEntity,
                Map.class
        );

        @SuppressWarnings("unchecked")
        Map<String, Object> aiResponse = responseEntity.getBody();
        Map<String, Object> response = new LinkedHashMap<>(aiResponse == null ? Map.of() : aiResponse);

        if (!createDraft) {
            response.put("draftCreated", false);
            return response;
        }

        UUID safeUserId = userId == null ? UUID.fromString("00000000-0000-0000-0000-000000000001") : userId;
        ImportPreviewDraftService.DraftCreationResult draft = importPreviewDraftService.createDraftFromPreview(
                file.getOriginalFilename(),
                safeUserId,
                response,
                projectType
        );

        response.put("draftCreated", true);
        response.put("draftId", draft.draftId());
        response.put("reviewUrl", "/projects/import?draftId=" + draft.draftId());
        response.put("draftProjectName", draft.projectName());
        response.put("draftNodeCount", draft.nodeCount());
        response.put("nextStep", "Open the hierarchy review screen directly so the user can correct anything before saving.");
        return response;
    }

    private String stripExtension(String filename) {
        if (filename == null) return null;
        int dot = filename.lastIndexOf('.');
        String stem = dot > 0 ? filename.substring(0, dot) : filename;
        return stem.replace('_', ' ').replace('-', ' ').trim();
    }
}
