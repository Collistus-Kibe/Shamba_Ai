---
name: Shamba AI
colors:
  surface: '#f9f9ff'
  surface-dim: '#d3daea'
  surface-bright: '#f9f9ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f0f3ff'
  surface-container: '#e7eefe'
  surface-container-high: '#e2e8f8'
  surface-container-highest: '#dce2f3'
  on-surface: '#151c27'
  on-surface-variant: '#404944'
  inverse-surface: '#2a313d'
  inverse-on-surface: '#ebf1ff'
  outline: '#707974'
  outline-variant: '#bfc9c3'
  surface-tint: '#2b6954'
  primary: '#003527'
  on-primary: '#ffffff'
  primary-container: '#064e3b'
  on-primary-container: '#80bea6'
  inverse-primary: '#95d3ba'
  secondary: '#006c49'
  on-secondary: '#ffffff'
  secondary-container: '#6cf8bb'
  on-secondary-container: '#00714d'
  tertiary: '#442800'
  on-tertiary: '#ffffff'
  tertiary-container: '#623c00'
  on-tertiary-container: '#f69f0d'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#b0f0d6'
  primary-fixed-dim: '#95d3ba'
  on-primary-fixed: '#002117'
  on-primary-fixed-variant: '#0b513d'
  secondary-fixed: '#6ffbbe'
  secondary-fixed-dim: '#4edea3'
  on-secondary-fixed: '#002113'
  on-secondary-fixed-variant: '#005236'
  tertiary-fixed: '#ffddb8'
  tertiary-fixed-dim: '#ffb95f'
  on-tertiary-fixed: '#2a1700'
  on-tertiary-fixed-variant: '#653e00'
  background: '#f9f9ff'
  on-background: '#151c27'
  surface-variant: '#dce2f3'
typography:
  display-lg:
    fontFamily: Inter
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: -0.01em
  headline-lg-mobile:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  headline-md:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  label-md:
    fontFamily: JetBrains Mono
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
    letterSpacing: 0.02em
  label-sm:
    fontFamily: JetBrains Mono
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  base: 4px
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 32px
  2xl: 48px
  gutter: 24px
  margin-mobile: 16px
  margin-desktop: 40px
---

## Brand & Style
The design system for this platform focuses on bridging high-end technology with the grounded reality of modern agriculture. The brand personality is "The Precise Steward"—authoritative and technically advanced, yet approachable and rooted in the earth. 

The aesthetic is **Modern Corporate with a Tactile Twist**, drawing heavily from the functional density of Linear and the conversational clarity of ChatGPT. It utilizes high-contrast interfaces to ensure readability under outdoor sunlight while maintaining a premium, "SaaS-forward" feel through sophisticated layering and subtle depth. 

The emotional response should be one of confidence and growth. We achieve this through expansive white space, precise data visualization, and a "living" color palette that feels organic rather than synthetic.

## Colors
This design system utilizes a hierarchical green palette supported by earthy accents.
- **Primary (Deep Forest):** Used for core branding, sidebars, and primary navigation to provide a sense of stability and depth.
- **Secondary (Vibrant Emerald):** The action color. Reserved for "Growth" metrics, primary buttons, and success states. It provides the high-energy "AI" spark.
- **Tertiary (Harvest Gold):** An earth-toned accent for warnings, pending states, and highlighting specific yield data.
- **Neutral (Slate/Stone):** A range of cool-grays that prevent the interface from feeling overly "grassy," maintaining a professional software feel.

**Dark Mode Strategy:** In dark mode, the Deep Forest (#064E3B) becomes the container color, while the background shifts to a near-black green (#022C22) to maintain brand identity without causing eye strain.

## Typography
We use **Inter** for all primary interface elements to ensure maximum legibility and a modern, neutral tone. For data-heavy contexts—such as GPS coordinates, pH levels, or sensor IDs—we introduce **JetBrains Mono**. This monospaced addition reinforces the "AI/Technical" nature of the platform.

Headlines should use tighter letter spacing to appear more "designed" and authoritative. Body text maintains standard spacing for high readability in field conditions.

## Layout & Spacing
The layout follows a **Hybrid Grid System**. 
- **Desktop:** A 12-column fluid grid with 40px outer margins. The sidebar is fixed at 280px to emulate the "Linear" efficiency.
- **Content Density:** High-density data views (tables/lists) use the 8px (sm) unit, while dashboard marketing/summary views use 24px (lg) to create "breathable" premium layouts.
- **Mobile:** Elements reflow to a single column with 16px margins. Cards become full-width to maximize touch targets for users who may be wearing gloves or are in motion.

## Elevation & Depth
This design system uses **Tonal Layering** combined with **Ambient Shadows** to create a sense of organized hierarchy.
- **Level 0 (Base):** The main background color (Light or Dark).
- **Level 1 (Cards):** Pure white (light) or Forest-offset (dark) surfaces with a subtle 1px border (#E5E7EB) and a very soft, diffused shadow (10% opacity primary color tint).
- **Level 2 (Popovers/Modals):** High-elevation surfaces with a 15% opacity shadow and a 24px blur.
- **Interactions:** Buttons use a "pressed" depth effect—moving from a subtle drop shadow to a flat state to simulate a physical click.

## Shapes
In line with the "farmer-friendly" and "premium SaaS" requirement, we utilize a generous **16px (rounded-lg)** radius for all primary containers and cards. This softens the technical nature of the data and makes the UI feel more approachable and modern.
- **Small components (Chips/Inputs):** 8px radius.
- **Large components (Dashboard Cards):** 16px radius.
- **Floating Action Buttons:** Full pill-shaped (999px).

## Components
- **Buttons:** Primary buttons use the Vibrant Emerald background with white text. They feature a subtle inner glow on the top edge to create a "tactile" feel. Secondary buttons use a ghost style with a 1px Forest Green border.
- **Cards:** Dashboard cards must include a 16px padding and a "header" area that uses the JetBrains Mono label for category tagging.
- **Input Fields:** Use a light-gray fill (#F3F4F6) that transitions to a white background with an Emerald border on focus. This provides a clear "active" signal.
- **Data Visualizations:** Charts should use a gradient fill of Emerald-to-Transparent. Grid lines in charts should be kept at 5% opacity to minimize visual noise.
- **Status Chips:** Use a pill shape with 10% opacity backgrounds of the status color (e.g., a light green background for a "Healthy" status) and 100% opacity text for high contrast.
- **Agricultural Specials:** Include "Weather Strips" and "Soil Health Gauges" as custom components that use a semi-circular progress bar style.