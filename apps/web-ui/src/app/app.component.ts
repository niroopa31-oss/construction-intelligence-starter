import { Component, signal, computed, OnDestroy } from '@angular/core';
import { RouterOutlet, RouterLink } from '@angular/router';
import { NgIf } from '@angular/common';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, RouterLink, NgIf],
  template: `
    <header class="app-header">
      <a routerLink="/" class="brand" aria-label="Construction Intelligence home">
        <!-- runtime-bound logo (switches immediately when theme or width changes) -->
        <img [src]="logoSrc()" alt="Construction Intelligence" class="brand-logo" [attr.height]="logoHeight" />
      </a>

      <nav class="main-nav">
        <a routerLink="/">Projects</a>
        <a routerLink="/projects/import">Import</a>
      </nav>

      <div class="header-actions">
        <button class="theme-toggle" (click)="toggleTheme()" [attr.aria-pressed]="theme() === 'dark'" title="Toggle theme">
          <span *ngIf="theme() === 'dark'">☀️</span>
          <span *ngIf="theme() === 'light'">🌙</span>
        </button>
      </div>
    </header>
    <main>
      <router-outlet />
    </main>
  `,
  styles: [`
    .app-header {
      background: #0b1220; /* deeper navy like reference */
      color: #e6eefc;
      padding: 0.6rem 1.2rem;
      display: flex;
      align-items: center;
      gap: 18px;
      height: 64px;
    }
    .brand { display:flex; align-items:center; gap:12px; text-decoration:none; }
    .brand-logo { display:inline-block; vertical-align:middle; height:40px; transition: opacity .28s ease, transform .28s ease; }
    .main-nav { display:flex; gap:18px; margin-left:8px; }
    .main-nav a { color:#94a3b8; text-decoration:none; font-size:.95rem; font-weight:600; }
    .main-nav a:hover { color:#ffffff }
    .header-actions { margin-left:auto; display:flex; gap:8px; align-items:center; }
    .theme-toggle { background:transparent; border:1px solid rgba(255,255,255,0.06); color:#cbd5e1; padding:6px 8px; border-radius:8px; cursor:pointer }
    .theme-toggle:hover { border-color: rgba(255,255,255,0.12); color:#fff }

    /* small screens: hide nav text and show compact monogram via logoSrc logic */
    @media (max-width: 360px) {
      .main-nav { display:none; }
      .brand-logo { height:36px }
    }
    @media (max-width: 480px) and (min-width: 361px) {
      /* tablet: keep nav but reduce spacing */
      .main-nav { gap:12px }
    }
    /* print: make logo monochrome friendly */
    @media print {
      .brand-logo { filter: grayscale(1) brightness(0.9); }
    }
    main { padding:0 }
  `]
})
export class AppComponent implements OnDestroy {
  // theme signal: 'light' or 'dark'
  theme = signal<( 'light' | 'dark' )>(
    (typeof window !== 'undefined' && window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) ? 'dark' : 'light'
  );

  // track screen width to pick compact monogram on small devices
  screenWidth = signal<number>(typeof window !== 'undefined' ? window.innerWidth : 1024);

  // computed logo src updates instantly when signals change
  logoSrc = computed(() => {
    const w = this.screenWidth();
    if (w <= 360) return '/assets/logo-construction-intelligence-square.svg';
    return this.theme() === 'dark' ? '/assets/logo-construction-intelligence-inverse.svg' : '/assets/logo-construction-intelligence-futuristic.svg';
  });

  // small helper for img height (keeps template simpler)
  logoHeight = 40;

  private _prefListener: any;
  private _resizeListener: any;
  private manualTheme = false;

  constructor() {
    // If user previously saved a preference, respect it and mark manualTheme
    try {
      const saved = typeof window !== 'undefined' ? window.localStorage.getItem('ci_theme') : null;
      if (saved === 'dark' || saved === 'light') {
        this.theme.set(saved as any);
        this.manualTheme = true;
      }
    } catch {
      // ignore storage errors
    }

    // keep document class in sync for global theming
    this.applyThemeClass(this.theme());

    // respond to OS theme changes unless user manually toggled
    if (typeof window !== 'undefined' && window.matchMedia) {
      const mq = window.matchMedia('(prefers-color-scheme: dark)');
      this._prefListener = (e: MediaQueryListEvent) => {
        if (!this.manualTheme) {
          this.theme.set(e.matches ? 'dark' : 'light');
          this.applyThemeClass(this.theme());
        }
      };
      try { mq.addEventListener('change', this._prefListener); } catch { mq.addListener(this._prefListener); }
    }

    // resize watcher for responsive logo switching
    this._resizeListener = () => this.screenWidth.set(window.innerWidth);
    window.addEventListener('resize', this._resizeListener);
  }

  toggleTheme() {
    this.manualTheme = true;
    const next = this.theme() === 'dark' ? 'light' : 'dark';
    this.theme.set(next);
    try { window.localStorage.setItem('ci_theme', next); } catch {}
    this.applyThemeClass(this.theme());
  }

  private applyThemeClass(t: 'light'|'dark') {
    try {
      document.documentElement.classList.toggle('dark', t === 'dark');
    } catch (e) {
      // ignore (server-rendering / no document)
    }
  }


  ngOnDestroy(): void {
    if (this._prefListener && window.matchMedia) {
      const mq = window.matchMedia('(prefers-color-scheme: dark)');
      try { mq.removeEventListener('change', this._prefListener); } catch { mq.removeListener(this._prefListener as any); }
    }
    if (this._resizeListener) window.removeEventListener('resize', this._resizeListener);
  }
}
