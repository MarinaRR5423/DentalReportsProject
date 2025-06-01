document.addEventListener('DOMContentLoaded', function() {
    // Referencias a elementos del DOM
    const workspace = document.querySelector('.workspace');
    const blocksPalette = document.querySelector('.blocks-palette');
    let selectedBlock = null;
    let isDragging = false;
    let offsetX, offsetY;

    // Inicializar la interfaz si hay bloques de paleta
    if (blocksPalette && blocksPalette.querySelectorAll('.block').length > 0) {
        // Agregar eventos a los bloques de la paleta
        const paletteBlocks = blocksPalette.querySelectorAll('.block');
        paletteBlocks.forEach(block => {
            block.addEventListener('mousedown', startDragNewBlock);
        });
    }

    // Función para comenzar a arrastrar un nuevo bloque desde la paleta
    function startDragNewBlock(e) {
        const original = e.target;
        const clone = original.cloneNode(true);

        // Posicionamiento inicial del clon
        clone.style.position = 'absolute';
        clone.style.width = `${original.offsetWidth}px`;

        // Cálculo del desplazamiento para posicionar el ratón en el centro del bloque
        offsetX = e.clientX - original.getBoundingClientRect().left;
        offsetY = e.clientY - original.getBoundingClientRect().top;

        // Añadir el clon al documento para arrastrarlo
        document.body.appendChild(clone);

        // Posicionar el clon inicialmente
        updateClonePosition(clone, e);

        // Evento para mover el clon con el ratón
        function moveClone(e) {
            updateClonePosition(clone, e);
        }

        // Evento para soltar el clon
        function releaseClone(e) {
            document.removeEventListener('mousemove', moveClone);
            document.removeEventListener('mouseup', releaseClone);

            const workspaceRect = workspace.getBoundingClientRect();

            // Verificar si el clon está sobre el workspace
            if (e.clientX > workspaceRect.left && e.clientX < workspaceRect.right &&
                e.clientY > workspaceRect.top && e.clientY < workspaceRect.bottom) {

                // Crear un nuevo contenedor de bloque en el workspace
                createBlockInWorkspace(clone.dataset.type, clone.dataset.template, clone.textContent, {
                    x: e.clientX - workspaceRect.left - offsetX + workspace.scrollLeft,
                    y: e.clientY - workspaceRect.top - offsetY + workspace.scrollTop
                });
            }

            // Eliminar el clon temporal
            document.body.removeChild(clone);
        }

        document.addEventListener('mousemove', moveClone);
        document.addEventListener('mouseup', releaseClone);

        // Evitar comportamientos por defecto
        e.preventDefault();
    }
       // Función para actualizar la posición del clon durante el arrastre
    function updateClonePosition(clone, e) {
        clone.style.left = `${e.clientX - offsetX}px`;
        clone.style.top = `${e.clientY - offsetY}px`;
    }

    // Función para crear un bloque en el workspace
    function createBlockInWorkspace(type, template, blockName, position) {
        const blockContainer = document.createElement('div');
        blockContainer.className = 'block-container';
        blockContainer.dataset.type = type;

        // Estructura del bloque
        const blockHeader = document.createElement('div');
        blockHeader.className = 'block-header';

        const blockTitle = document.createElement('div');
        blockTitle.className = `block ${type}`;
        blockTitle.textContent = blockName;
        blockTitle.style.display = 'inline-block';
        blockTitle.style.padding = '5px 10px';

        const blockControls = document.createElement('div');
        blockControls.className = 'block-controls';

        const editButton = document.createElement('button');
        editButton.className = 'btn btn-sm btn-outline-primary';
        editButton.innerHTML = '<i class="fas fa-edit"></i>';
        editButton.addEventListener('click', () => openBlockSettings(blockContainer));

        const deleteButton = document.createElement('button');
        deleteButton.className = 'btn btn-sm btn-outline-danger';
        deleteButton.innerHTML = '<i class="fas fa-trash"></i>';
        deleteButton.addEventListener('click', () => blockContainer.remove());

        blockControls.appendChild(editButton);
        blockControls.appendChild(deleteButton);

        blockHeader.appendChild(blockTitle);
        blockHeader.appendChild(blockControls);

        const blockContent = document.createElement('div');
        blockContent.className = 'block-content';
        blockContent.innerHTML = template;

        blockContainer.appendChild(blockHeader);
        blockContainer.appendChild(blockContent);

        // Posicionar el bloque
        blockContainer.style.position = 'absolute';
        blockContainer.style.left = `${position.x}px`;
        blockContainer.style.top = `${position.y}px`;

        // Eventos para selección y movimiento
        blockContainer.addEventListener('mousedown', function(e) {
            // Evitar conflictos con botones
            if (e.target.tagName === 'BUTTON' || e.target.closest('button')) {
                return;
            }

            selectBlock(blockContainer);

            // Iniciar arrastre si se hace clic en el encabezado del bloque
            if (e.target === blockTitle || e.target.closest('.block-header')) {
                startDragBlock(e, blockContainer);
            }
        });

        workspace.appendChild(blockContainer);
        selectBlock(blockContainer);

        return blockContainer;
    }
        // Función para seleccionar un bloque
    function selectBlock(block) {
        // Desseleccionar bloque anterior
        if (selectedBlock) {
            selectedBlock.classList.remove('selected');
        }

        // Seleccionar el nuevo bloque
        selectedBlock = block;
        selectedBlock.classList.add('selected');
    }

    // Función para iniciar el arrastre de un bloque ya existente
    function startDragBlock(e, block) {
        if (e.button !== 0) return; // Solo botón izquierdo

        isDragging = true;

        // Calcular offset para mantener posición relativa
        const blockRect = block.getBoundingClientRect();
        const workspaceRect = workspace.getBoundingClientRect();

        offsetX = e.clientX - blockRect.left;
        offsetY = e.clientY - blockRect.top;

        // Función de movimiento
        function moveBlock(e) {
            if (isDragging) {
                const x = e.clientX - workspaceRect.left - offsetX + workspace.scrollLeft;
                const y = e.clientY - workspaceRect.top - offsetY + workspace.scrollTop;

                block.style.left = `${x}px`;
                block.style.top = `${y}px`;
            }
        }

        // Función para soltar
        function releaseBlock() {
            isDragging = false;
            document.removeEventListener('mousemove', moveBlock);
            document.removeEventListener('mouseup', releaseBlock);
        }

        document.addEventListener('mousemove', moveBlock);
        document.addEventListener('mouseup', releaseBlock);

        e.preventDefault();
    }

    // Función para abrir el panel de configuración de un bloque
    function openBlockSettings(block) {
        // Obtener el tipo de bloque
        const blockType = block.dataset.type;
        const blockContent = block.querySelector('.block-content');

        // Crear o mostrar el panel de configuración
        let settingsPanel = block.querySelector('.block-settings');

        if (!settingsPanel) {
            settingsPanel = document.createElement('div');
            settingsPanel.className = 'block-settings';
            block.appendChild(settingsPanel);
        }

        // Limpiar panel
        settingsPanel.innerHTML = '';
                // Generar campos según el tipo de bloque
        switch (blockType) {
            case 'text-block':
                // Campo para editar el texto
                const contentLabel = document.createElement('label');
                contentLabel.textContent = 'Contenido de texto:';

                const contentInput = document.createElement('textarea');
                contentInput.value = blockContent.innerText;
                contentInput.rows = 3;

                const fontSizeLabel = document.createElement('label');
                fontSizeLabel.textContent = 'Tamaño de fuente:';

                const fontSizeInput = document.createElement('select');
                [10, 12, 14, 16, 18, 20, 24, 28, 32].forEach(size => {
                    const option = document.createElement('option');
                    option.value = size;
                    option.textContent = `${size}px`;
                    fontSizeInput.appendChild(option);
                });

                // Botón para aplicar
                const applyButton = document.createElement('button');
                applyButton.className = 'btn btn-sm btn-primary mt-2';
                applyButton.textContent = 'Aplicar';
                applyButton.addEventListener('click', function() {
                    blockContent.innerHTML = contentInput.value;
                    blockContent.style.fontSize = `${fontSizeInput.value}px`;
                    settingsPanel.remove();
                });

                settingsPanel.appendChild(contentLabel);
                settingsPanel.appendChild(contentInput);
                settingsPanel.appendChild(fontSizeLabel);
                settingsPanel.appendChild(fontSizeInput);
                settingsPanel.appendChild(applyButton);
                break;

            case 'condition-block':
                // Campo para editar la condición
                const conditionLabel = document.createElement('label');
                conditionLabel.textContent = 'Expresión de condición:';

                const conditionInput = document.createElement('input');
                conditionInput.type = 'text';
                conditionInput.value = block.querySelector('.condition-expression') ?
                    block.querySelector('.condition-expression').textContent.replace('Si ', '') : '';

                const ifContentLabel = document.createElement('label');
                ifContentLabel.textContent = 'Contenido si se cumple:';

                const ifContentInput = document.createElement('textarea');
                ifContentInput.value = block.querySelector('.condition-content') ?
                    block.querySelector('.condition-content').textContent : '';
                ifContentInput.rows = 2;

                const elseContentLabel = document.createElement('label');
                elseContentLabel.textContent = 'Contenido si no se cumple:';

                const elseContentInput = document.createElement('textarea');
                elseContentInput.value = block.querySelector('.condition-else-content') ?
                    block.querySelector('.condition-else-content').textContent : '';
                elseContentInput.rows = 2;

                // Botón para aplicar
                const applyCondButton = document.createElement('button');
                applyCondButton.className = 'btn btn-sm btn-primary mt-2';
                applyCondButton.textContent = 'Aplicar';
                applyCondButton.addEventListener('click', function() {
                    blockContent.innerHTML = `
                        <div class="condition-wrapper">
                            <div class="condition-expression">Si ${conditionInput.value}</div>
                            <div class="condition-content">${ifContentInput.value}</div>
                            <div class="condition-else-content">${elseContentInput.value}</div>
                        </div>
                    `;
                    settingsPanel.remove();
                });

                settingsPanel.appendChild(conditionLabel);
                settingsPanel.appendChild(conditionInput);
                settingsPanel.appendChild(ifContentLabel);
                settingsPanel.appendChild(ifContentInput);
                settingsPanel.appendChild(elseContentLabel);
                settingsPanel.appendChild(elseContentInput);
                settingsPanel.appendChild(applyCondButton);
                break;
                    case 'variable-block':
                // Lista de variables disponibles
                const variableLabel = document.createElement('label');
                variableLabel.textContent = 'Seleccionar variable:';

                const variableSelect = document.createElement('select');
                const variables = [
                    {name: 'nombrePaciente', label: 'Nombre del Paciente'},
                    {name: 'edadPaciente', label: 'Edad del Paciente'},
                    {name: 'fechaConsulta', label: 'Fecha de Consulta'},
                    {name: 'diagnostico', label: 'Diagnóstico'},
                    {name: 'tratamiento', label: 'Tratamiento'},
                    {name: 'dentistaNombre', label: 'Nombre del Dentista'},
                    {name: 'proximaCita', label: 'Fecha de Próxima Cita'}
                ];

                variables.forEach(variable => {
                    const option = document.createElement('option');
                    option.value = variable.name;
                    option.textContent = variable.label;
                    variableSelect.appendChild(option);
                });

                // Botón para aplicar
                const applyVarButton = document.createElement('button');
                applyVarButton.className = 'btn btn-sm btn-primary mt-2';
                applyVarButton.textContent = 'Aplicar';
                applyVarButton.addEventListener('click', function() {
                    blockContent.innerHTML = `{${variableSelect.value}}`;
                    settingsPanel.remove();
                });

                settingsPanel.appendChild(variableLabel);
                settingsPanel.appendChild(variableSelect);
                settingsPanel.appendChild(applyVarButton);
                break;

            case 'image-block':
                // Campo para URL de imagen
                const urlLabel = document.createElement('label');
                urlLabel.textContent = 'URL de la imagen:';

                const urlInput = document.createElement('input');
                urlInput.type = 'text';
                urlInput.value = block.querySelector('img') ?
                    block.querySelector('img').src : '';

                const sizeLabel = document.createElement('label');
                sizeLabel.textContent = 'Tamaño (px):';

                const widthLabel = document.createElement('span');
                widthLabel.textContent = 'Ancho: ';

                const widthInput = document.createElement('input');
                widthInput.type = 'number';
                widthInput.style.width = '80px';
                widthInput.value = block.querySelector('img') ?
                    block.querySelector('img').width : '200';

                const heightLabel = document.createElement('span');
                heightLabel.textContent = ' Alto: ';
                heightLabel.style.marginLeft = '10px';

                const heightInput = document.createElement('input');
                heightInput.type = 'number';
                heightInput.style.width = '80px';
                heightInput.value = block.querySelector('img') ?
                    block.querySelector('img').height : '';

                const sizeContainer = document.createElement('div');
                sizeContainer.appendChild(widthLabel);
                sizeContainer.appendChild(widthInput);
                sizeContainer.appendChild(heightLabel);
                sizeContainer.appendChild(heightInput);

                // Botón para aplicar
                const applyImgButton = document.createElement('button');
                applyImgButton.className = 'btn btn-sm btn-primary mt-2';
                applyImgButton.textContent = 'Aplicar';
                applyImgButton.addEventListener('click', function() {
                    blockContent.innerHTML = `
                        <div class="image-container">
                            <img src="${urlInput.value}" alt="Imagen" width="${widthInput.value}" ${heightInput.value ? `height="${heightInput.value}"` : ''}>
                        </div>
                    `;
                    settingsPanel.remove();
                });

                settingsPanel.appendChild(urlLabel);
                settingsPanel.appendChild(urlInput);
                settingsPanel.appendChild(sizeLabel);
                settingsPanel.appendChild(sizeContainer);
                settingsPanel.appendChild(applyImgButton);
                break;
        }
    }

    // Función para guardar la plantilla
    window.saveTemplate = function() {
        // Recopilar bloques y su contenido
        const blocks = Array.from(workspace.querySelectorAll('.block-container'));

        const template = {
            template_id: document.getElementById('template-id').value,
            name: document.getElementById('template-name').value || 'Mi Plantilla Dental',
            blocks: blocks.map(block => {
                return {
                    type: block.dataset.type,
                    content: block.querySelector('.block-content').innerHTML,
                    position: {
                        x: parseInt(block.style.left),
                        y: parseInt(block.style.top)
                    }
                };
            })
        };

        // Obtener el token CSRF para Django
        const csrfToken = document.querySelector('[name="csrfmiddlewaretoken"]').value;

        // Enviar la plantilla al servidor Django
        fetch('/informes/guardar-plantilla/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify(template)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Actualizar el ID de la plantilla si es nuevo
                if (data.id) {
                    document.getElementById('template-id').value = data.id;
                }
                alert('Plantilla guardada con éxito!');
            } else {
                alert('Error al guardar: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error al guardar la plantilla');
        });
    };

    // Función para limpiar el workspace
    window.clearWorkspace = function() {
        if (confirm('¿Estás seguro de que quieres limpiar el workspace? Se perderán todos los cambios no guardados.')) {
            workspace.innerHTML = '';
        }
    };

    // Función para cargar datos de una plantilla existente
    window.loadTemplateData = function(blocks) {
        // Limpiar el workspace primero
        workspace.innerHTML = '';

        // Recrear los bloques
        if (Array.isArray(blocks)) {
            blocks.forEach(blockData => {
                const blockContainer = document.createElement('div');
                blockContainer.className = 'block-container';
                blockContainer.dataset.type = blockData.type;

                // Crear la estructura del bloque
                const blockHeader = document.createElement('div');
                blockHeader.className = 'block-header';

                const blockTitle = document.createElement('div');
                blockTitle.className = `block ${blockData.type}`;

                // Determinar el nombre del bloque según su tipo
                let blockName;
                switch (blockData.type) {
                    case 'text-block': blockName = 'Texto'; break;
                    case 'condition-block': blockName = 'Condición'; break;
                    case 'variable-block': blockName = 'Variable'; break;
                    case 'layout-block': blockName = 'Diseño'; break;
                    case 'image-block': blockName = 'Imagen'; break;
                    case 'table-block': blockName = 'Tabla'; break;
                    default: blockName = 'Bloque';
                }

                blockTitle.textContent = blockName;
                blockTitle.style.display = 'inline-block';
                blockTitle.style.padding = '5px 10px';

                const blockControls = document.createElement('div');
                blockControls.className = 'block-controls';

                const editButton = document.createElement('button');
                editButton.className = 'btn btn-sm btn-outline-primary';
                editButton.innerHTML = '<i class="fas fa-edit"></i>';
                editButton.addEventListener('click', () => openBlockSettings(blockContainer));

                const deleteButton = document.createElement('button');
                deleteButton.className = 'btn btn-sm btn-outline-danger';
                deleteButton.innerHTML = '<i class="fas fa-trash"></i>';
                deleteButton.addEventListener('click', () => blockContainer.remove());

                blockControls.appendChild(editButton);
                blockControls.appendChild(deleteButton);

                blockHeader.appendChild(blockTitle);
                blockHeader.appendChild(blockControls);

                const blockContent = document.createElement('div');
                blockContent.className = 'block-content';
                blockContent.innerHTML = blockData.content;

                blockContainer.appendChild(blockHeader);
                blockContainer.appendChild(blockContent);

                // Posicionar el bloque
                blockContainer.style.position = 'absolute';
                if (blockData.position) {
                    blockContainer.style.left = `${blockData.position.x}px`;
                    blockContainer.style.top = `${blockData.position.y}px`;
                } else {
                    blockContainer.style.left = '10px';
                    blockContainer.style.top = '10px';
                }

                // Eventos para selección y movimiento
                blockContainer.addEventListener('mousedown', function(e) {
                    // Evitar conflictos con botones
                    if (e.target.tagName === 'BUTTON' || e.target.closest('button')) {
                        return;
                    }

                    selectBlock(blockContainer);

                    // Iniciar arrastre si se hace clic en el encabezado del bloque
                    if (e.target === blockTitle || e.target.closest('.block-header')) {
                        startDragBlock(e, blockContainer);
                    }
                });

                workspace.appendChild(blockContainer);
            });
        }
    };
});