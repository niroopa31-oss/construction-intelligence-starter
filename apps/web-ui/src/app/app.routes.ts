import { Routes } from '@angular/router';
import { ProjectListComponent } from './features/projects/project-list/project-list.component';
import { ProjectImportWizardComponent } from './features/projects/project-import-wizard/project-import-wizard.component';
import { ProjectOverviewComponent } from './features/projects/project-overview/project-overview.component';

export const routes: Routes = [
  { path: '', component: ProjectListComponent },
  { path: 'projects', component: ProjectListComponent },
  { path: 'projects/import', component: ProjectImportWizardComponent },
  { path: 'projects/:id', component: ProjectOverviewComponent },
  { path: '**', redirectTo: '' },
];
