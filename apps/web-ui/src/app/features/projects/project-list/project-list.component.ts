import { Component, DestroyRef, OnInit, inject } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { HttpClient } from '@angular/common/http';

interface ProjectCard {
  projectId: string;
  name: string;
  type: string;
  status: 'Active' | 'Review' | 'Planning' | string;
  progress: number;
  risk?: string;
  delayedTasks?: number;
}

@Component({
  selector: 'app-project-list',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './project-list.component.html',
  styleUrls: ['./project-list.component.css']
})
export class ProjectListComponent implements OnInit {
  private readonly http = inject(HttpClient);
  private readonly destroyRef = inject(DestroyRef);

  projects: ProjectCard[] = [];
  quickStats = [
    { label: 'Overall active projects', value: '0', sub: 'workspace' },
    { label: 'Milestones at risk', value: '0', sub: '' },
    { label: 'Open discrepancies', value: '0', sub: '' },
    { label: 'AI recovery actions', value: '0', sub: '' },
  ];

  loading = false;
  error: string | null = null;

  ngOnInit(): void {
    this.loadProjects();
  }

  loadProjects(): void {
    this.loading = true;
    this.error = null;
    // API: GET /api/projects?userId=... -> expected to return an array of project summaries
    const DEFAULT_USER_ID = '00000000-0000-0000-0000-000000000001';
    const url = `/api/projects?userId=${encodeURIComponent(DEFAULT_USER_ID)}`;
    this.http.get<any[]>(url).pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: list => {
        // Map incoming shape defensively to our ProjectCard interface
        const mapped = (list || []).map((p, i) => ({
          projectId: p.projectId || p.id || p.project_id || String(p.id || i + 1),
          name: p.name || p.projectName || p.project_name || `Project ${i + 1}`,
          type: p.type || p.projectType || p.project_type || 'Unknown',
          status: p.status || 'Active',
          progress: typeof p.progress === 'number' ? p.progress : (p.completion || 0),
          risk: p.risk || p.riskSignal || undefined,
          delayedTasks: typeof p.delayedTasks === 'number' ? p.delayedTasks : (p.taskDelayCount || 0),
  }));

        // De-duplicate by project name (keep the first occurrence from the backend, which
        // is already ordered by createdAt desc). Use case-insensitive comparison.
        const seen = new Set<string>();
        this.projects = [];
        for (const p of mapped) {
          const key = (p.name || '').trim().toLowerCase();
          if (!seen.has(key)) {
            seen.add(key);
            this.projects.push(p);
          }
        }

        // Update quick stats if available
        const total = this.projects.length;
        const atRisk = this.projects.reduce((s, p) => s + (p.risk ? 1 : 0), 0);
        this.quickStats = [
          { label: 'Overall active projects', value: String(total), sub: 'workspace' },
          { label: 'Milestones at risk', value: String(atRisk), sub: '' },
          { label: 'Open discrepancies', value: '0', sub: '' },
          { label: 'AI recovery actions', value: '0', sub: '' },
        ];

        this.loading = false;
      },
      error: err => {
        this.loading = false;
        this.error = err?.message || 'Could not load projects';
      }
    });
  }
}
