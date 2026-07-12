// assets/js/editor.js - Minimal debug version
console.log('Webpack bundle loaded successfully!');

document.addEventListener('DOMContentLoaded', async function() {
    console.log('DOM Ready!');

    const container = document.getElementById('editor');
    if (!container) {
        console.warn('Editor container not found');
        return;
    }

    try {
        // Load KaTeX first
        const katexModule = await import('katex');
        // Make it globally available for the math plugin
        window.katex = katexModule.default || katexModule;

        // Import KaTeX CSS (if using Webpack)
        await import('katex/dist/katex.min.css');

        const [
            { EditorState },
            { EditorView },
            { markdown },
            { Table },
            liveMarkdownModule
        ] = await Promise.all([
            import('@codemirror/state'),
            import('@codemirror/view'),
            import('@codemirror/lang-markdown'),
            import('@lezer/markdown'),
            import('codemirror-live-markdown')
        ]);

        // 🔍 DEBUG: Check what's available (remove this block later)
        console.log('📦 Available exports:', Object.keys(liveMarkdownModule));

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

        console.log({table: !!Table});

        // 🔍 DEBUG: Check each plugin (remove this block later)
        console.log('✅ Plugins loaded:', {
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
            markdown({ extensions: [Table] }),
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
        if (linkPlugin) extensions.push(linkPlugin({ showPreview: true }));
        if (listPlugin) extensions.push(listPlugin);

        const view = new EditorView({
            state: EditorState.create({
                doc: '# Hello World\n\nThis is **bold** and *italic* text.',
                extensions: extensions,
            }),
            parent: container,
        });

        // Track mouse selection state
        if (setMouseSelecting) {
            view.contentDOM.addEventListener('mousedown', () => {
                view.dispatch({ effects: setMouseSelecting.of(true) });
            });
            document.addEventListener('mouseup', () => {
                requestAnimationFrame(() => {
                    view.dispatch({ effects: setMouseSelecting.of(false) });
                });
            });
        }

        window.editorView = view;
        console.log('✅ Editor initialized!');

    } catch (error) {
        console.error('❌ Editor initialization failed:', error.message);
    }
});

/*
console.log('Webpack bundle loaded successfully!');

/!*
    Dynamically load codemirror packages as webpack+babel expects all packages to be modules while codemirror uses a
    composition of plugins as it's design strategy.
 *!/

// Add codemirror-live-markdown to ONE editor container element whose id is #editor
document.addEventListener('DOMContentLoaded', async function() {
    console.log('DOM Ready!');

    const container = document.getElementById('editor');
    if (!container) {
        console.warn('Editor container not found');
        return;
    }

    try {
        // Load dynamic dependencies
        const [{ EditorState }, { EditorView }, { markdown }, { Table }, liveMarkdownModule] =
            await Promise.all([
                import('@codemirror/view'),
                import('@codemirror/state'),
                import('@codemirror/lang-markdown'),
                import('@lezer/markdown'),
                import('codemirror-live-markdown')
            ]);

        // Extract plugins from codemirror-live-markdown
        const {
            livePreviewPlugin,
            markdownStylePlugin,
            editorTheme,
            mouseSelectingField,
            collapseOnSelectionFacet,
            mathPlugin,
            blockMathField,
            tableField,
            tableEditorPlugin,
            imageField,
            linkPlugin,
            listPlugin,
        } = liveMarkdownModule;

        const view = new EditorView({
            state: EditorState.create({
                doc: '# Hello World\\n\\nThis is **bold** and *italic* text.',
                extensions: [
                    markdown([ Table ]),
                    livePreviewPlugin,
                    markdownStylePlugin,
                    editorTheme,
                    mouseSelectingField,
                    collapseOnSelectionFacet.on(true),
                    blockMathField,
                    tableField,
                    tableEditorPlugin,
                    imageField,
                    linkPlugin({
                        showPreview: true
                    }),
                    listPlugin,
                ],
            }),
            parent: container,
        })

        // Required: Track mouse selection state
        view.contentDOM.addEventListener('mousedown', () => {
            view.dispatch({ effects: setMouseSelecting.of(true) });
        });
        document.addEventListener('mouseup', () => {
            requestAnimationFrame(() => {
                view.dispatch({ effects: setMouseSelecting.of(false) });
            });
        });
    } catch (error) {
        console.error('Editor element on page but failed to initialise editor!');
        console.error('Error Details:' + error.message)
    }
});*/
