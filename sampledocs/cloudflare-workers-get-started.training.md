---
id: cloudflare-workers-get-started
domain: training
subtype: tool-kt
name: "Get started - CLI"
source: "Cloudflare Workers Documentation"
license: "CC-BY-4.0"
---

Set up and deploy your first Worker with Wrangler, the Cloudflare Developer Platform CLI.

# Concepts {#key_value}
- **C3 (create-cloudflare-cli)** — A command-line tool designed to help you set up and deploy new applications to Cloudflare.
- **Wrangler** — The Workers command-line interface that allows you to create, test, and deploy your Workers projects.
- **fetch() handler** — An event handler called when your Worker receives an HTTP request, which expects a Response object or a Promise resolving to one.

# Steps

## 1 · Create a new Worker project

### 1. Run C3 to create your Worker project {#command_step}
cmd: npm create cloudflare@latest my-first-worker
expect: A new project is set up

### 2. Move into the project folder {#command_step}
cmd: cd my-first-worker

**Files created by C3**
- wrangler.jsonc :: Your Wrangler configuration file.
- index.js (in /src) :: A minimal 'Hello World!' Worker written in ES module syntax.
- package.json :: A minimal Node dependencies configuration file.
- package-lock.json :: Node package lock configuration file.
- node_modules :: Node dependencies folder.

## 2 · Develop with Wrangler CLI

### 1. Start a local server for developing your Worker {#command_step}
cmd: npx wrangler dev
note: If you have never used Wrangler before, it will open your web browser so you can login to your Cloudflare account.
verify: Go to http://localhost:8787 to view your Worker.

## 3 · Write code
**Code explanation**
- export default :: JavaScript syntax required for defining JavaScript modules with properties corresponding to handled events.
- fetch() handler :: Handler called when your Worker receives an HTTP request, passed request, env, and context parameters.

### 1. Update the Worker output text {#command_step}
do: Replace the content in your current index.js file with the updated code block that returns "Hello Worker!"
expect: Your Worker's output will have changed to the new text after saving the file and reloading the page.

## 4 · Deploy your project

### 1. Deploy your Worker via Wrangler {#command_step}
cmd: npx wrangler deploy
note: If you have not configured any subdomain or domain, Wrangler will prompt you during the publish process to set one up.
verify: Preview your Worker at <YOUR_WORKER>.<YOUR_SUBDOMAIN>.workers.dev

# Troubleshooting {#accordion_item}
- Browser issues or no access to a browser interface :: Refer to the wrangler login documentation.
- The output for your Worker does not change :: Make sure that you saved the changes to index.js, have wrangler dev running, and reloaded your browser.
- Seeing 523 errors when pushing your *.workers.dev subdomain for the first time :: Wait a minute or so and the errors will resolve themselves.

# References {#resources_list}
- C3 GitHub repository — https://github.com/cloudflare/workers-sdk/tree/main/packages/create-cloudflare
- View local Worker development — http://localhost:8787
- MDN JavaScript modules export guide — https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Modules#default_exports_versus_named_exports
- Cloudflare dashboard — https://dash.cloudflare.com/
