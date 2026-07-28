console.log('Webpack bundle loaded successfully!');

//region AlpineJS
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
//endregion

let hiddenEditorContainer = document.getElementById('editor-hidden-container');
let isHidden = true;

let editorView = null;
let cachedPlugins = null;

let currentContainerId = null;
let currentTextareaId = null;

//region Helper Functions
async function getPlugins() {
    if (cachedPlugins) {
        console.log('- Using cached plugins');
        return cachedPlugins;
    }

    console.log('- Loading plugins');
    // Load KaTeX first
    const katexModule = await import('katex');
    // Make it globally available for the math plugin
    window.katex = katexModule.default || katexModule;
    await import('katex/dist/katex.min.css');

    // Load other plugins dynamically
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
function getExtensionsAndTools(plugins) {
    const [
        {EditorState},
        {EditorView},
        {markdown},
        {Table},
        liveMarkdownModule
    ] = plugins;

    const {
        livePreviewPlugin,
        markdownStylePlugin,
        editorTheme,
        mouseSelectingField,
        collapseOnSelectionFacet,
        setMouseSelecting,
        mathPlugin,
        blockMathField,
        tableField,
        tableEditorPlugin,
        imageField,
        linkPlugin,
        listPlugin,
    } = liveMarkdownModule;

    // Check each plugin (remove this block later)
    console.log('- Extensions loaded:', {
        livePreview: !!livePreviewPlugin,
        markdownStyle: !!markdownStylePlugin,
        theme: !!editorTheme,
        mouseSelecting: !!mouseSelectingField,
        collapseOnSelection: !!collapseOnSelectionFacet,
        setMouseSelecting: !!setMouseSelecting,
        math: !!mathPlugin,
        blockMath: !!blockMathField,
        table: !!tableField,
        tableEditor: !!tableEditorPlugin,
        image: !!imageField,
        link: !!linkPlugin,
        list: !!listPlugin,
    });

    // Build extensions - only add plugins that exist
    const extensions = [
        markdown({extensions: [Table]}),
    ];

    // Add plugins conditionally
    if (livePreviewPlugin) extensions.push(livePreviewPlugin);
    if (markdownStylePlugin) extensions.push(markdownStylePlugin);
    if (editorTheme) extensions.push(editorTheme);
    if (mouseSelectingField) extensions.push(mouseSelectingField);
    if (collapseOnSelectionFacet) extensions.push(collapseOnSelectionFacet.of(true));
    if (mathPlugin) extensions.push(mathPlugin);
    if (blockMathField) extensions.push(blockMathField);
    if (tableField) extensions.push(tableField);
    if (tableEditorPlugin) extensions.push(tableEditorPlugin());
    if (imageField) extensions.push(imageField());
    if (linkPlugin) extensions.push(linkPlugin({showPreview: true}));
    if (listPlugin) extensions.push(listPlugin);

    return { extensions, setMouseSelecting, EditorView, EditorState };
}
//endregion

window.initEditor = function (options) {
    currentContainerId = options.containerId;
    currentTextareaId = options.textareaId;
    console.log('Initializing editor with container:', currentContainerId, 'textarea:', currentTextareaId);
}
window.hideEditor = function () {
    console.log('Hiding editor');
    isHidden = true;

    if (!editorView) {
        console.warn('- Editor not initialized');
        return;
    }

    // Get the current parent of the editor
    const currentParent = editorView.dom.parentNode;
    if (currentParent === hiddenEditorContainer) {
        console.warn('- Editor already hidden');
        return;
    }

    // Remove the editor from the current container
    if (currentParent) {
        currentParent.removeChild(editorView.dom);
    }

    // Attach the editor to the hidden container
    hiddenEditorContainer.appendChild(editorView.dom);
    return editorView;
}
window.showEditor = async function (options) {
    // If currentContainerId is not provided, then editor remains hidden
    if (!currentContainerId) {
        console.log("- Container id not provided thus editor remains hidden");
        return editorView;
    }

    isHidden = false;

    // CASE 1: If the editor is already initialized, attach it to the container
    if (editorView) {
        console.log('Attaching editor to:', currentContainerId, currentTextareaId);

        if (!currentTextareaId) console.warn("- Hidden text area id not provided", currentTextareaId);

        let content = "";
        const currentTextArea = document.getElementById(currentTextareaId);
        if (!currentTextArea) {
            console.warn('- Hidden text area not found:', currentTextareaId)
        } else {
            content = currentTextArea.value;
        }

        // Get the current parent of the editor
        const container = document.getElementById(currentContainerId);
        if (!container) {
            console.error('- Container element id is provided but not found:', currentContainerId);
            return null;
        }

        // Attach the editor to the container
        const currentParent = editorView.dom.parentNode;
        if (currentParent !== hiddenEditorContainer) {
            console.warn('- Editor attached to the non-hidden container');
        }

        // Remove the editor from the previous container
        if (currentParent) {
            currentParent.removeChild(editorView.dom);
        }

        // Attach the editor to the new container
        container.appendChild(editorView.dom);

        // Update content
        editorView.dispatch({
            changes: {
                from: 0,
                to: editorView.state.doc.length,
                insert: content
            }
        });

        return editorView;
    }

    const container = document.getElementById(currentContainerId);
    if (!container) {
        console.error('- Container element not found:', currentContainerId);
        return null;
    }

    // CASE 2: If the editor is not initialized, initialize it
    try {
        const textarea = document.getElementById(currentTextareaId);
        if (!textarea) console.warn('- Hidden text area element not found:', currentTextareaId);
        const content = textarea ? textarea.value : "";

        const { extensions, setMouseSelecting, EditorView, EditorState } = getExtensionsAndTools(await getPlugins());

        // If text area is defined, create extension to synch content with hidden textarea
        const hiddenInputExtension = EditorView.updateListener.of((update) => {
            if (update.docChanged) {
                if (!currentTextareaId) return;
                const currentTextArea = document.getElementById(currentTextareaId);
                currentTextArea.value = update.state.doc.toString();
            }
        })

        extensions.push(hiddenInputExtension);

        const view = new EditorView({
            state: EditorState.create({
                doc: content,
                extensions: extensions,
            }),
            parent: container,
        });

        // Track mouse selection state
        if (setMouseSelecting) {
            view.contentDOM.addEventListener('mousedown', () => {
                view.dispatch({effects: setMouseSelecting.of(true)});
            });
            document.addEventListener('mouseup', () => {
                requestAnimationFrame(() => {
                    view.dispatch({effects: setMouseSelecting.of(false)});
                });
            });
        }

        // Set state
        editorView = view;
        return editorView;
    } catch (error) {
        console.error('❌ Editor initialization failed:', error.message, error.stack);
        return null;
    }
};
window.destroyEditor = function () {
    if (editorView) {
        editorView.destroy();
        editorView = null;
        currentTextareaId = null;
        cachedPlugins = null;
        console.log('Editor destroyed');
    }
}

//region HTMX
document.addEventListener('htmx:beforeSwap', function(event) {
    window.hideEditor();
})

document.addEventListener('htmx:afterSwap', async function(event) {
    await window.showEditor();
})
//endregion
