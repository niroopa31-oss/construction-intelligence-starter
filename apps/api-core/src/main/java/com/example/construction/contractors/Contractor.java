package com.example.construction.contractors;

import jakarta.persistence.*;
import lombok.*;
import java.util.UUID;

@Entity
@Table(name = "contractor")
@Getter @Setter @NoArgsConstructor @AllArgsConstructor @Builder
public class Contractor {
    @Id
    @GeneratedValue
    private UUID id;
    @Column(name = "project_id", nullable = false)
    private UUID projectId;
    @Column(name = "company_name", nullable = false)
    private String companyName;
    private String contactName;
    private String email;
    private String phone;
    private String tradeType;
}
