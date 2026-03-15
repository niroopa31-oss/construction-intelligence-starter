import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';

interface ProjectCard {
  name: string;
  type: string;
  status: 'Active' | 'Review' | 'Planning';
  progress: number;
  risk: string;
  delayedTasks: number;
}

@Component({
  selector: 'app-project-list',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './project-list.component.html',
  styleUrls: ['./project-list.component.css']
})
export class ProjectListComponent {
  readonly projects: ProjectCard[] = [
    {
      name: 'DSR Twins Skymarq',
      type: 'High-rise residential',
      status: 'Active',
      progress: 68,
      risk: '4 milestones at risk',
      delayedTasks: 6,
    },
    {
      name: 'Skyline Tower Phase 2',
      type: 'Commercial tower',
      status: 'Review',
      progress: 44,
      risk: '2 discrepancy clusters',
      delayedTasks: 3,
    },
    {
      name: 'Aurora Villas',
      type: 'Villa project',
      status: 'Planning',
      progress: 19,
      risk: 'Import review pending',
      delayedTasks: 0,
    },
  ];

  readonly quickStats = [
    { label: 'Overall active projects', value: '3', sub: '1 client workspace' },
    { label: 'Milestones at risk', value: '6', sub: '2 critical this week' },
    { label: 'Open discrepancies', value: '17', sub: '6 need field review' },
    { label: 'AI recovery actions', value: '9', sub: '3 suggested today' },
  ];
}
