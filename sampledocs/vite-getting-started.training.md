---
id: vite-getting-started
domain: training
subtype: tool-kt
name: "Vite Getting Started Guide"
audience: "Developers setting up a modern web project with Vite"
source: "vite-getting-started.md documentation, 2026"
license: "MIT"
est_minutes: 20
---

Learn how to set up, scaffold, and build web projects using the Vite build tool, covering both automated and manual project installation methods.

# Prerequisites {#prerequisite_checklist}
- Node.js version 20.19+ or 22.12+ installed (some templates may require a higher version)

# Concepts {#key_value}
- **Vite** — Build tool that aims to provide a faster and leaner development experience for modern web projects
- **Dev server** — A server providing rich feature enhancements over native ES modules, such as fast Hot Module Replacement (HMR)
- **Build command** — A command that bundles your code with Rolldown, pre-configured to output highly optimized static assets for production
- **Root directory** — The concept of a directory which files are served from, where index.html acts as the front-and-central entry point

# Steps

## 1 · Automatic Scaffolding
**Supported Template Presets**
- vanilla :: https://vite.new/vanilla
- vue :: https://vite.new/vue
- react :: https://vite.new/react
- svelte :: https://vite.new/svelte

### 1. Scaffold a new project interactively {#command_step}
cmd: npm create vite@latest
note: Follow the terminal prompts to select your framework and variant.

### 2. Scaffold a project with explicit command line options {#command_step}
cmd: npm create vite@latest my-vue-app -- --template vue
note: You can use . for the project name to scaffold in the current directory, or use the --no-interactive flag to skip interactive prompts.

## 2 · Community Templates

### 1. Clone a community template via tiged {#command_step}
cmd: npx tiged user/project my-project

### 2. Navigate into the cloned project directory {#command_step}
cmd: cd my-project

### 3. Install project dependencies {#command_step}
cmd: npm install

### 4. Launch the local development server {#command_step}
cmd: npm run dev

## 3 · Manual Installation

### 1. Install Vite as a development dependency {#command_step}
cmd: npm install -D vite

### 2. Create the index.html entry point {#command_step}
do: Create an index.html file in your project root containing <p>Hello Vite!</p>.
note: Vite treats index.html as source code and part of the module graph, automatically resolving script elements and rebasing URLs.

### 3. Start the development server manually {#command_step}
cmd: npx vite
expect: The index.html will be served on http://localhost:5173.

## 4 · Command Line Interface & Production Build
**Default npm Scripts**
- dev :: vite
- build :: vite build
- preview :: vite preview

### 1. Build the project for production {#command_step}
cmd: npx vite build
note: Bundles code with Rolldown, targeting Baseline Widely Available browsers by default.

### 2. Preview the production build locally {#command_step}
cmd: npx vite preview

### 3. Specify an alternative project root directory {#command_step}
cmd: vite serve some/sub/dir
note: Vite will also resolve its config file (i.e. vite.config.js) inside the specified project root.

## 5 · Using Unreleased Commits

### 1. Install a specific commit from pkg.pr.new {#command_step}
cmd: npm install -D https://pkg.pr.new/vite@SHA
note: Replace SHA with an active Vite commit SHA from the last month.

### 2. Clone the Vite repository locally {#command_step}
cmd: git clone https://github.com/vitejs/vite.git

### 3. Change directory to the cloned repo {#command_step}
cmd: cd vite

### 4. Install repository dependencies using pnpm {#command_step}
cmd: pnpm install

### 5. Navigate to the core Vite package directory {#command_step}
cmd: cd packages/vite

### 6. Build the Vite package locally {#command_step}
cmd: pnpm run build

### 7. Create a global package link {#command_step}
cmd: pnpm link
note: Run pnpm link vite in your local project directory afterward to use this edge build.

# Troubleshooting {#accordion_item}
- Package manager warns about Node.js version :: Upgrade your Node.js version to 20.19+, 22.12+, or higher as required by the template
- Configuration file not found after changing root :: Move your vite.config.js file into the newly specified alternative project root directory

# References {#resources_list}
- Vite Online Playground — https://vite.new/
- Rolldown Bundler — https://rolldown.rs
- Vite GitHub Repository — https://github.com/vitejs/vite
- Free Vite Course on Scrimba — https://scrimba.com/intro-to-vite-c03p6pbbdq?via=vite
- Discord Community — https://chat.vite.dev
- GitHub Discussions — https://github.com/vitejs/vite/discussions
