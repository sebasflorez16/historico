/**
 * EJEMPLO DE USO: Sistema de Informes Personalizados con Fechas Exactas
 * 
 * Este archivo muestra cómo usar el sistema desde el frontend (JavaScript)
 */

// ============================================================================
// EJEMPLO 1: INFORME CON FECHAS EXACTAS (Rango personalizado)
// ============================================================================

async function generarInformeConFechasExactas(parcelaId) {
    const fechaInicio = '2025-06-01';  // ✅ Fecha exacta de inicio
    const fechaFin = '2025-11-25';     // ✅ Fecha exacta de fin
    
    const payload = {
        periodo: {
            fecha_inicio: fechaInicio,
            fecha_fin: fechaFin
        },
        configuracion: {
            nivel_detalle: 'completo',
            indices: ['ndvi', 'msavi', 'savi'],
            secciones: ['tendencias', 'recomendaciones_riego']
        }
    };
    
    try {
        const response = await fetch(
            `/informes/parcelas/${parcelaId}/generar-informe-personalizado/`,
            {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify(payload)
            }
        );
        
        const data = await response.json();
        
        if (data.success) {
            console.log('✅ Informe generado:', data.pdf_url);
            // Abrir PDF en nueva ventana
            window.open(data.pdf_url, '_blank');
        }
    } catch (error) {
        console.error('❌ Error:', error);
    }
}

// ============================================================================
// EJEMPLO 2: INFORME EJECUTIVO RÁPIDO (Solo NDVI, sin secciones extra)
// ============================================================================

async function generarInformeEjecutivo(parcelaId) {
    const payload = {
        periodo: {
            meses_rapidos: 6  // ✅ Últimos 6 meses (alternativa a fechas exactas)
        },
        configuracion: {
            nivel_detalle: 'ejecutivo',
            indices: ['ndvi'],  // Solo NDVI
            secciones: []       // Sin secciones adicionales
        }
    };
    
    const response = await fetch(
        `/informes/parcelas/${parcelaId}/generar-informe-personalizado/`,
        {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify(payload)
        }
    );
    
    const data = await response.json();
    
    if (data.success) {
        console.log('✅ PDF ejecutivo generado (ligero):', data.pdf_url);
        console.log('📄 Tamaño esperado: ~60 KB (vs 250 KB completo)');
    }
}

// ============================================================================
// EJEMPLO 3: INFORME ESTÁNDAR CON TODOS LOS ÍNDICES
// ============================================================================

async function generarInformeCompleto(parcelaId) {
    const haceUnAño = new Date();
    haceUnAño.setFullYear(haceUnAño.getFullYear() - 1);
    
    const payload = {
        periodo: {
            fecha_inicio: haceUnAño.toISOString().split('T')[0],
            fecha_fin: new Date().toISOString().split('T')[0]
        },
        configuracion: {
            nivel_detalle: 'completo',
            indices: ['ndvi', 'msavi', 'ndmi', 'savi', 'ndre', 'gndvi'],
            secciones: [
                'tendencias',
                'recomendaciones_riego',
                'recomendaciones_fertilizacion',
                'salud_cultivo'
            ]
        }
    };
    
    const response = await fetch(
        `/informes/parcelas/${parcelaId}/generar-informe-personalizado/`,
        {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify(payload)
        }
    );
    
    const data = await response.json();
    
    if (data.success) {
        console.log('✅ Informe completo generado');
        console.log('📊 Período:', payload.periodo);
        console.log('📄 PDF:', data.pdf_url);
    }
}

// ============================================================================
// EJEMPLO 4: INFORME DE COMPARACIÓN ESTACIONAL
// ============================================================================

async function generarInformeVerano2024(parcelaId) {
    // Analizar solo el verano de 2024
    const payload = {
        periodo: {
            fecha_inicio: '2024-06-01',  // Inicio del verano
            fecha_fin: '2024-08-31'      // Fin del verano
        },
        configuracion: {
            nivel_detalle: 'estandar',
            indices: ['ndvi', 'ndmi'],  // Vigor y agua
            secciones: ['tendencias', 'recomendaciones_riego'],
            personalizacion: {
                enfoque_especial: 'Análisis de estrés hídrico durante el verano 2024',
                notas_adicionales: 'Evaluar impacto de ola de calor'
            }
        }
    };
    
    const response = await fetch(
        `/informes/parcelas/${parcelaId}/generar-informe-personalizado/`,
        {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify(payload)
        }
    );
    
    const data = await response.json();
    
    if (data.success) {
        console.log('✅ Informe de verano generado');
        console.log('📅 Período analizado: Jun-Ago 2024');
        console.log('🌡️ Enfoque: Estrés hídrico');
    }
}

// ============================================================================
// EJEMPLO 5: INFORME CON PLANTILLA PREDEFINIDA
// ============================================================================

async function generarInformeDesdePlantilla(parcelaId, plantillaId) {
    // Cargar configuración de plantilla
    const plantilla = await fetch(`/informes/plantillas/${plantillaId}/`);
    const config = await plantilla.json();
    
    const payload = {
        periodo: {
            meses_rapidos: 12  // Último año
        },
        configuracion: config.configuracion  // Usar config de plantilla
    };
    
    const response = await fetch(
        `/informes/parcelas/${parcelaId}/generar-informe-personalizado/`,
        {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify(payload)
        }
    );
    
    const data = await response.json();
    
    if (data.success) {
        console.log(`✅ Informe generado con plantilla: ${config.nombre}`);
    }
}

// ============================================================================
// FUNCIÓN HELPER: Obtener CSRF Token
// ============================================================================

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// ============================================================================
// EJEMPLO 6: VALIDACIÓN ANTES DE GENERAR
// ============================================================================

async function validarYGenerarInforme(parcelaId, fechaInicio, fechaFin) {
    // Validar fechas
    const inicio = new Date(fechaInicio);
    const fin = new Date(fechaFin);
    
    if (inicio >= fin) {
        alert('❌ La fecha de inicio debe ser anterior a la fecha de fin');
        return;
    }
    
    // Calcular diferencia en meses
    const diffMeses = (fin.getFullYear() - inicio.getFullYear()) * 12 + 
                     (fin.getMonth() - inicio.getMonth());
    
    if (diffMeses < 1) {
        alert('⚠️ El período debe ser de al menos 1 mes');
        return;
    }
    
    if (diffMeses > 24) {
        const confirmar = confirm(
            `📊 Vas a generar un informe de ${diffMeses} meses (${Math.round(diffMeses/12)} años).\n` +
            'Esto puede tardar más tiempo. ¿Continuar?'
        );
        if (!confirmar) return;
    }
    
    console.log(`✅ Validación OK: ${diffMeses} meses de análisis`);
    
    // Generar informe
    await generarInformeConFechasExactas(parcelaId);
}

// ============================================================================
// EJEMPLO 7: GENERACIÓN CON FEEDBACK AL USUARIO
// ============================================================================

async function generarInformeConFeedback(parcelaId, config) {
    // Mostrar modal de carga
    mostrarModalCarga('Generando informe personalizado...');
    
    try {
        const response = await fetch(
            `/informes/parcelas/${parcelaId}/generar-informe-personalizado/`,
            {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify(config)
            }
        );
        
        const data = await response.json();
        
        ocultarModalCarga();
        
        if (data.success) {
            // Mostrar modal de éxito con opciones
            mostrarModalExito({
                titulo: '✅ Informe Generado',
                mensaje: `Tu informe personalizado está listo`,
                pdf_url: data.pdf_url,
                opciones: [
                    {
                        texto: '👁️ Ver en navegador',
                        accion: () => window.open(data.pdf_url, '_blank')
                    },
                    {
                        texto: '⬇️ Descargar PDF',
                        accion: () => descargarArchivo(data.pdf_url, data.nombre_archivo)
                    },
                    {
                        texto: '📋 Ver detalle',
                        accion: () => window.location.href = data.url_detalle
                    }
                ]
            });
        } else {
            mostrarError('Error generando informe: ' + data.error);
        }
    } catch (error) {
        ocultarModalCarga();
        mostrarError('Error de conexión: ' + error.message);
    }
}

// ============================================================================
// EJEMPLO DE USO EN PÁGINA
// ============================================================================

// En el HTML:
// <button onclick="generarInformeConFechasExactas(1)">
//   Generar Informe Personalizado
// </button>

console.log('✅ Sistema de Informes Personalizados listo');
console.log('📖 Ejemplos disponibles:');
console.log('   - generarInformeConFechasExactas(parcelaId)');
console.log('   - generarInformeEjecutivo(parcelaId)');
console.log('   - generarInformeCompleto(parcelaId)');
console.log('   - generarInformeVerano2024(parcelaId)');
