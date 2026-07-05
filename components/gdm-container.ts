import { LitElement, css, html } from 'lit';
import { customElement, property } from 'lit/decorators.js';

@customElement('gdm-container')
export class GdmStageContainer extends LitElement {
  @property({ type: String }) direction = 'row';
  @property({ type: String }) justify = 'flex-start';
  @property({ type: String }) align = 'stretch';
  @property({ type: String }) gap = '0';
  @property({ type: String }) padding = '0';
  @property({ type: String }) background = 'transparent';
  @property({ type: String }) border = 'none';
  @property({ type: String }) borderRadius = '0';
  @property({ type: String }) width = 'auto';
  @property({ type: String }) height = 'auto';
  @property({ type: Boolean }) glass = false;
  @property({ type: Boolean }) scrollable = false;
  @property({ type: Number }) grow = 0;
  @property({ type: Number }) shrink = 1;
  @property({ type: String }) margin = '0';
  @property({ type: String, reflect: true }) reveal = '';
  @property({ type: Number }) revealDelay = 0; // seconds — stagger panels for a staged "set the stage" entrance
  @property({ type: Number }) columns = 0; // 0 = no columns, > 0 = use CSS column-count
  @property({ type: String }) columnGap = ''; // gap between columns (defaults to gap or 16px)


  static styles = css`
    :host {
      display: flex;
      box-sizing: border-box;
    }
    ::slotted(*) {
      break-inside: avoid;
      page-break-inside: avoid;
    }
    :host(.scrollable) {
      overflow: auto;
    }
    /* Scrollbar decoration */
    :host(.scrollable):-webkit-scrollbar {
      width: 6px;
      height: 6px;
    }
    :host(.scrollable)::-webkit-scrollbar {
      width: 6px;
      height: 6px;
    }
    :host(.scrollable)::-webkit-scrollbar-track {
      background: rgba(255, 255, 255, 0.01);
    }
    :host(.scrollable)::-webkit-scrollbar-thumb {
      background: rgba(0, 242, 255, 0.15);
      border-radius: 3px;
    }
    :host(.scrollable)::-webkit-scrollbar-thumb:hover {
      background: rgba(0, 242, 255, 0.35);
    }

    /* --- Entrance reveals: play once on mount. 'both' holds the start state
       during revealDelay so staggered panels stay hidden until their turn,
       producing a choreographed "set the stage" cascade. Animations don't
       replay on data re-renders (the element is reused), so it's a clean intro. */
    :host([reveal])             { animation: rv-fade-up 0.55s cubic-bezier(0.16, 1, 0.3, 1) both; }
    :host([reveal="scale-in"])  { animation-name: rv-scale-in; }
    :host([reveal="slide-left"]){ animation-name: rv-slide-left; }
    :host([reveal="slide-right"]){ animation-name: rv-slide-right; }
    :host([reveal="blur-in"])   { animation-name: rv-blur-in; }
    :host([reveal="flip"])      { animation-name: rv-flip; transform-origin: top center; }
    @keyframes rv-fade-up     { from { opacity: 0; transform: translateY(18px); } to { opacity: 1; transform: none; } }
    @keyframes rv-scale-in    { from { opacity: 0; transform: scale(0.92); }      to { opacity: 1; transform: none; } }
    @keyframes rv-slide-left  { from { opacity: 0; transform: translateX(48px); } to { opacity: 1; transform: none; } }
    @keyframes rv-slide-right { from { opacity: 0; transform: translateX(-48px); }to { opacity: 1; transform: none; } }
    @keyframes rv-blur-in     { from { opacity: 0; filter: blur(14px); }          to { opacity: 1; filter: none; } }
    @keyframes rv-flip        { from { opacity: 0; transform: rotateX(-90deg); }  to { opacity: 1; transform: none; } }
  `;

  updated(changedProperties: Map<string, any>) {
    // Dynamic Host Layout styling — writes inline CSS directly onto the <gdm-container> element
    this.style.boxSizing = 'border-box';
    this.style.padding = this.padding;
    this.style.width = this.width;
    this.style.height = this.height;
    this.style.flexGrow = String(this.grow);
    this.style.flexShrink = String(this.shrink);
    this.style.margin = this.margin;

    console.log(`[gdm-container] updated ID: ${this.id}, columns: ${this.columns}, type: ${typeof this.columns}`);

    const cols = Number(this.columns);
    if (!isNaN(cols) && cols > 0) {
      console.log(`[gdm-container] ID: ${this.id} applying block layout with ${cols} columns`);
      this.style.display = 'block';
      this.style.columnCount = String(cols);
      this.style.columnGap = this.columnGap || this.gap || '16px';
      
      // Force height constraints to prevent column collapse in flexbox parents
      this.style.height = (this.height && this.height !== 'auto') ? this.height : '100%';
      this.style.minHeight = '0';
      
      // Clear flex attributes
      this.style.flexDirection = '';
      this.style.justifyContent = '';
      this.style.alignItems = '';
      this.style.gap = '';
    } else {
      console.log(`[gdm-container] ID: ${this.id} applying flex layout`);
      this.style.display = 'flex';
      this.style.flexDirection = this.direction;
      this.style.justifyContent = this.justify;
      this.style.alignItems = this.align;
      this.style.gap = this.gap;
      
      // Clear column and height constraints
      this.style.columnCount = '';
      this.style.columnGap = '';
      this.style.minHeight = '';
    }

    if (this.scrollable) {
      this.classList.add('scrollable');
      this.style.overflow = 'auto';
    } else {
      this.classList.remove('scrollable');
      this.style.overflow = 'visible';
    }

    if (this.glass) {
      // Ultra-premium glassmorphism values
      this.style.background = 'rgba(10, 14, 32, 0.72)';
      this.style.backdropFilter = 'blur(20px) saturate(1.5)';
      this.style.setProperty('-webkit-backdrop-filter', 'blur(20px) saturate(1.5)');
      this.style.border = '1px solid rgba(255, 255, 255, 0.08)';
      this.style.borderRadius = this.borderRadius !== '0' ? this.borderRadius : '16px';
      this.style.boxShadow = '0 12px 40px rgba(0, 0, 0, 0.5)';
    } else {
      // Clean fallback layout styling
      this.style.background = this.background;
      this.style.border = this.border;
      this.style.borderRadius = this.borderRadius;
      
      if (changedProperties.has('glass')) {
        this.style.backdropFilter = '';
        this.style.setProperty('-webkit-backdrop-filter', '');
        this.style.boxShadow = '';
      }
    }

    // Stagger the entrance. Set once; re-applying the same delay won't replay
    // the animation, so data re-renders don't re-trigger the intro.
    if (this.reveal) {
      this.style.animationDelay = `${this.revealDelay || 0}s`;
    }
  }

  render() {
    return html`<slot></slot>`;
  }
}
