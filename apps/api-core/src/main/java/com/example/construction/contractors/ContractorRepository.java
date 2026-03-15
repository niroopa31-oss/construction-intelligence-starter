package com.example.construction.contractors;

import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;
import java.util.UUID;

public interface ContractorRepository extends JpaRepository<Contractor, UUID> {
    List<Contractor> findByProjectIdOrderByCompanyNameAsc(UUID projectId);
}
