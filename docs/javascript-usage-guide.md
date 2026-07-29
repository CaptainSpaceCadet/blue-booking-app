# JavaScript Usage Guide

## 📋 Table of Contents
- [Overview](#overview)
- [Architecture](#architecture)
- [Libraries & Dependencies](#libraries--dependencies)
- [CodeMirror Editor Singleton](#codemirror-editor-singleton)
- [HTMX Integration](#htmx-integration)
- [Alpine.js Integration](#alpinejs-integration)
- [Webpack Configuration](#webpack-configuration)
- [Development vs Production](#development-vs-production)
- [Troubleshooting](#troubleshooting)

---

## 🎯 Overview

This project uses a **JavaScript-first approach** with modern ES6 modules, dynamic imports, and a singleton pattern for the rich text editor. The JavaScript is bundled using Webpack and loaded asynchronously to optimize performance.

### Key Features
- **Singleton CodeMirror Editor** - Single editor instance reused across the application
- **Dynamic Module Loading** - Lazy-load heavy dependencies (KaTeX, CodeMirror plugins)
- **HTMX Integration** - Seamless interaction with Django's HTMX views
- **Alpine.js** - Lightweight reactive components for UI interactions

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Browser                              │
│                                                              │
│  ┌────────────────────────────────────────────────────┐     │
│  │              Webpack Bundle (index.js)              │     │
│  │                                                     │     │
│  │  ┌──────────────────────────────────────────┐      │     │
│  │  │         Alpine.js (Lightweight UI)       │      │     │
│  │  │   - Reactive components                  │      │     │
│  │  │   - DOM interactions                     │      │     │
│  │  └──────────────────────────────────────────┘      │     │
│  │                                                     │     │
│  │  ┌──────────────────────────────────────────┐      │     │
│  │  │      CodeMirror Editor Singleton         │      │     │
│  │  │   - Single instance across pages         │      │     │
│  │  │   - Markdown with live preview           │      │     │
│  │  │   - KaTeX math rendering                 │      │     │
│  │  │   - Tables, images, links, lists        │      │     │
│  │  └──────────────────────────────────────────┘      │     │
│  │                                                     │     │
│  │  ┌──────────────────────────────────────────┐      │     │
│  │  │         HTMX Event Handlers              │      │     │
│  │  │   - beforeSwap: Hide editor              │      │     │
│  │  │   - afterSwap: Show editor              │      │     │
│  │  └──────────────────────────────────────────┘      │     │
│  └────────────────────────────────────────────────────┘     │
│                                                              │
│  ┌────────────────────────────────────────────────────┐     │
│  │         Dynamic Imports (Lazy Loading)             │     │
│  │   - @codemirror/state                             │     │
│  │   - @codemirror/view                              │     │
│  │   - @codemirror/lang-markdown                     │     │
│  │   - codemirror-live-markdown                      │     │
│  │   - katex (math rendering)                        │     │
│  └────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

---

## 📚 Libraries & Dependencies

### Core Libraries
| Library | Purpose | Loading Method |
|---------|---------|----------------|
| **Alpine.js** | Lightweight reactive UI framework | Dynamic import (eager) |
| **CodeMirror 6** | Rich text/Markdown editor | Dynamic import (lazy) |
| **KaTeX** | Math formula rendering | Dynamic import (lazy) |

### CodeMirror Plugins (Lazy Loaded)
| Plugin | Purpose |
|--------|---------|
| `@codemirror/state` | Editor state management |
| `@codemirror/view` | Editor view rendering |
| `@codemirror/lang-markdown` | Markdown language support |
| `@lezer/markdown` | Markdown parser |
| `codemirror-live-markdown` | Live preview, math, tables, links, lists |
| `katex` | Math formula rendering |

---

## 📝 CodeMirror Editor Singleton

### Why a Singleton?

The editor is implemented as a singleton for several reasons:

1. **Performance** - Single editor instance reused across the application
2. **State Persistence** - Preserves editor state between page swaps
3. **Resource Efficiency** - Loads heavy dependencies once
4. **Consistent UX** - Maintains editor state across navigation

### Editor Lifecycle

```javascript
┌─────────────────────────────────────────────────────────────┐
│                    Editor Lifecycle                         │
│                                                              │
│  1. INITIALIZATION (window.initEditor)                     │
│     ├── Store containerId & textareaId                     │
│     └── Editor remains hidden until shown                  │
│                                                              │
│  2. HIDE (window.hideEditor)                               │
│     ├── Move editor to hidden container                   │
│     └── Preserve state                                     │
│                                                              │
│  3. SHOW (window.showEditor)                               │
│     ├── Move editor to visible container                  │
│     ├── Load content from hidden textarea                 │
│     └── Initialize if first time                          │
│                                                              │
│  4. DESTROY (window.destroyEditor)                        │
│     ├── Destroy editor instance                           │
│     └── Clear cached plugins                              │
└─────────────────────────────────────────────────────────────┘
```

### Key Functions

#### `window.initEditor(options)`
Sets up editor configuration without initializing the instance.

```javascript
window.initEditor({
    containerId: 'editor-container',
    textareaId: 'hidden-content'
});
```

#### `window.showEditor(options)`
Shows the editor in the specified container. Initializes if not already created.

```javascript
await window.showEditor({
    containerId: 'editor-container',
    textareaId: 'hidden-content'
});
```

#### `window.hideEditor()`
Hides the editor by moving it to a hidden container.

```javascript
window.hideEditor();
```

#### `window.destroyEditor()`
Destroys the editor instance and clears cached data.

```javascript
window.destroyEditor();
```

### Plugin Loading

Plugins are loaded lazily with caching:

```javascript
async function getPlugins() {
    if (cachedPlugins) {
        return cachedPlugins;  // Return cached plugins
    }
    
    // Load KaTeX first
    const katexModule = await import('katex');
    window.katex = katexModule.default || katexModule;
    await import('katex/dist/katex.min.css');
    
    // Load all CodeMirror plugins
    const plugins = await Promise.all([
        import('@codemirror/state'),
        import('@codemirror/view'),
        import('@codemirror/lang-markdown'),
        import('@lezer/markdown'),
        import('codemirror-live-markdown')
    ]);
    
    cachedPlugins = plugins;
    return plugins;
}
```

### Extension Building

Extensions are built conditionally based on available plugins:

```javascript
function getExtensionsAndTools(plugins) {
    const [
        {EditorState},
        {EditorView},
        {markdown},
        {Table},
        liveMarkdownModule
    ] = plugins;
    
    // Extract plugins
    const {
        livePreviewPlugin,
        markdownStylePlugin,
        editorTheme,
        mathPlugin,
        tableEditorPlugin,
        imageField,
        linkPlugin,
        listPlugin,
    } = liveMarkdownModule;
    
    // Build extensions
    const extensions = [
        markdown({extensions: [Table]}),
        livePreviewPlugin,
        markdownStylePlugin,
        editorTheme,
        mathPlugin,
        tableEditorPlugin(),
        imageField(),
        linkPlugin({showPreview: true}),
        listPlugin
    ];
    
    return { extensions, EditorView, EditorState };
}
```

---

## 🔄 HTMX Integration

HTMX is used for dynamic page updates without full reloads. The editor handles HTMX events to manage its lifecycle.

### Event Handlers

#### Before Swap (hide editor)
```javascript
document.addEventListener('htmx:beforeSwap', function(event) {
    window.hideEditor();  // Hide before content swaps
});
```

#### After Swap (show editor)
```javascript
document.addEventListener('htmx:afterSwap', async function(event) {
    await window.showEditor();  // Show after new content loads
});
```

### HTMX + Editor Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    HTMX Request Flow                        │
│                                                              │
│  1. User clicks button                                      │
│         ↓                                                   │
│  2. HTMX: beforeSwap event triggered                       │
│         ↓                                                   │
│  3. window.hideEditor()                                    │
│     └── Editor moved to hidden container                  │
│         ↓                                                   │
│  4. HTMX swaps content                                     │
│         ↓                                                   │
│  5. HTMX: afterSwap event triggered                        │
│         ↓                                                   │
│  6. window.showEditor()                                    │
│     ├── Editor moved to new container                     │
│     └── Content updated from textarea                     │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎨 Alpine.js Integration

Alpine.js is loaded dynamically for lightweight reactive components.

### Loading Strategy

```javascript
// Dynamically import Alpine with Webpack
import(/* webpackMode: "eager" */ 'alpinejs')
    .then(module => {
        const Alpine = module.default || module;
        window.Alpine = Alpine;
        Alpine.start();
        console.log('Alpine.js loaded successfully!');
    })
    .catch(error => {
        console.error('Failed to load Alpine.js:', error);
    });
```

### Usage in Templates

```html
<div x-data="{ open: false }">
    <button @click="open = !open">Toggle</button>
    <div x-show="open" x-transition>
        Content
    </div>
</div>
```

---

## ⚙️ Webpack Configuration

### Output Configuration
```javascript
output: {
    path: path.resolve(__dirname, 'assets/webpack_bundles/'),
    publicPath: '/static/webpack_bundles/',
    filename: '[name].[contenthash].js',
    clean: true,
}
```

### Entry Point
```javascript
entry: './assets/src/js/index.js',
```

### Module Loading Strategy
| Module | Loading Strategy |
|--------|------------------|
| Alpine.js | Eager (loads immediately) |
| CodeMirror | Lazy (loads on demand) |
| KaTeX | Lazy (loads on demand) |
| Plugins | Lazy with caching |

### Production Build
```bash
npx webpack --mode=production
```

### Development Build
```bash
npx webpack --mode=development --watch
```

---

## 🔧 Development vs Production

### Development Mode
```bash
# Watch mode with hot reload
npx webpack --mode=development --watch

# DEBUG=True in Django
# ALLOWED_HOSTS=['*']
```

### Production Mode
```bash
# Optimized build
npx webpack --mode=production

# DEBUG=False in Django
# Specific ALLOWED_HOSTS
```

### Environment Detection
```javascript
// In index.js
const isDevelopment = process.env.NODE_ENV === 'development';

if (isDevelopment) {
    console.log('🔧 Development mode');
    // Enable debugging
}
```

---

## 🐛 Troubleshooting

### Common Issues

#### 1. Editor Not Initializing
**Symptoms**: Editor doesn't appear when expected.

**Solutions**:
```javascript
// Check if container exists
const container = document.getElementById(containerId);
console.log('Container:', container);

// Check if textarea exists
const textarea = document.getElementById(textareaId);
console.log('Textarea:', textarea);

// Check if editor is initialized
console.log('Editor View:', editorView);
```

#### 2. Plugins Not Loading
**Symptoms**: Console errors or missing features (math, tables, etc.)

**Solutions**:
```bash
# Clear cache and reload
window.destroyEditor();
await window.showEditor({...});

# Check plugin loading
console.log('Cached plugins:', cachedPlugins);
```

#### 3. HTMX Not Triggering
**Symptoms**: Editor not hiding/showing on page swaps.

**Solutions**:
```javascript
// Check if HTMX is loaded
console.log('HTMX:', window.htmx);

// Check event listeners
document.addEventListener('htmx:beforeSwap', function(event) {
    console.log('HTMX beforeSwap:', event);
});
```

#### 4. Webpack Build Failing
**Symptoms**: Build errors or missing bundles.

**Solutions**:
```bash
# Clean and rebuild
rm -rf assets/webpack_bundles/
rm -rf node_modules/
npm install
npx webpack --mode=development
```

### Debugging Tips

#### Enable Verbose Logging
```javascript
// Add to index.js
console.log('🔍 Editor State:', {
    isHidden,
    editorView: !!editorView,
    currentContainerId,
    currentTextareaId,
    cachedPlugins: !!cachedPlugins
});
```

#### Check Webpack Stats
```javascript
// Access webpack stats
console.log('Webpack Stats:', window.webpackStats);
```

---

## 📁 File Structure

```
assets/
├── src/
│   └── js/
│       ├── index.js           # Main entry point
│       ├── editor.js          # Editor singleton logic
│       └── htmx-handlers.js   # HTMX event handlers
└── webpack_bundles/           # Built bundles (generated)
    ├── main.[hash].js
    └── main.[hash].js.map

templates/
└── includes/
    └── editor.html            # Editor template
```

---

## 🎯 Best Practices

### 1. Use the Singleton Pattern
Always use the global editor instance:
```javascript
// ✅ Good
await window.showEditor({...});

// ❌ Bad - creates duplicate instances
new EditorView({...});
```

### 2. Lazy Load Heavy Dependencies
```javascript
// ✅ Good - loads only when needed
const plugins = await import('@codemirror/state');

// ❌ Bad - loads immediately
import * as state from '@codemirror/state';
```

### 3. Clean Up Resources
```javascript
// ✅ Good
window.destroyEditor();

// ❌ Bad - memory leak
editorView = new EditorView({...});
// Never destroy
```

### 4. Handle HTMX Events Properly
```javascript
// ✅ Good
document.addEventListener('htmx:afterSwap', async function() {
    await window.showEditor();
});

// ❌ Bad - no async/await
document.addEventListener('htmx:afterSwap', function() {
    window.showEditor();  // Might not complete
});
```

---

## 🔗 Related Documentation

- [CodeMirror 6 Documentation](https://codemirror.net/docs/)
- [Alpine.js Documentation](https://alpinejs.dev/)
- [HTMX Documentation](https://htmx.org/docs/)
- [KaTeX Documentation](https://katex.org/docs/)
- [Webpack Documentation](https://webpack.js.org/concepts/)