# Pre-entrega 6: Orquestador multi-agente especializado

## ¿Qué debes construir?

Prototipo funcional de un **Orquestador Multi-Agente de Análisis e Investigación**. El sistema debe procesar una solicitud de usuario que requiera:

- Al menos **dos dominios de especialización** distintos
- Una **fase de síntesis final**

---

## Requerimientos técnicos

### Topología jerárquica

- Un nodo **Supervisor** que actúa como router inteligente y controlador de flujo

### Mínimo de 2 agentes especialistas

| Agente                       | Rol                                                                                                |
| ---------------------------- | -------------------------------------------------------------------------------------------------- |
| **Búsqueda / Investigación** | Consultar fuentes externas (Tavily o búsqueda simulada sobre Vector DB de pre-entregas anteriores) |
| **Análisis / Cómputo**       | Procesar datos obtenidos (sentimiento, cálculos o validación de esquemas)                          |

### Estado compartido estructurado

- Esquema de `State` en LangGraph que rastree qué agente aportó qué información
- Evitar pérdida de contexto en comunicación asíncrona

### Flujo de supervisión

- El supervisor decide si la tarea está completa o si un especialista debe refinar su output antes de la respuesta final

---

## Pasos sugeridos

1. **Define tu Estado** — Clase `TypedDict` que herede de `MessagesState`. Evalúa campos extra (`next_agent`, `task_completed`, etc.).
2. **Crea los Agentes Especialistas** — Funciones con `create_react_agent` o prompts por rol. Cada uno con herramientas acotadas.
3. **Implementa el Supervisor** — Prompt claro: _"Dada la conversación actual, ¿quién debe intervenir ahora o es momento de finalizar?"_. Mapear respuestas a nombres de nodos del grafo.
4. **Construye el Grafo** — `add_node` por agente y supervisor. `Conditional Edges` del supervisor a los especialistas.
5. **Prueba la Interacción** — Consulta que fuerce: Investigador → Analista → cierre.

---

## Errores comunes a evitar

| Error                         | Descripción                                  | Tip                                                                     |
| ----------------------------- | -------------------------------------------- | ----------------------------------------------------------------------- |
| **Supervisor infinito**       | Sin condición de parada clara → bucle eterno | Contador de pasos o criterio de "suficiencia" estricto                  |
| **Contaminación de contexto** | Pasar todo el historial a todos los agentes  | El especialista solo recibe instrucción específica + contexto necesario |

---

## Qué entregás y en qué formato

| Campo                 | Detalle                                                                                                                        |
| --------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| **Tipo**              | Código — repositorio de GitHub                                                                                                 |
| **Artefacto**         | Repo con `state.py`, carpeta `agents/` (investigación + análisis), grafo con nodo Supervisor, `README.md` con diagrama Mermaid |
| **Demo**              | Video corto o notebook que demuestre el flujo de delegación                                                                    |
| **Qué NO hace falta** | Informe escrito (el video/notebook es solo demo del flujo)                                                                     |

---

## Instrucciones de la práctica

### Estructura del repositorio

```
├── state.py                 # Esquema de datos compartido
├── agents/
│   ├── research_agent.py    # Especialista de investigación
│   └── analyst_agent.py     # Especialista de análisis
├── main.py / graph.py       # Grafo principal
└── README.md                # Topología + diagrama Mermaid
```

### Implementación del grafo

- Usar `StateGraph` de LangGraph
- Nodo **Supervisor** que decida el flujo dinámicamente con `Literal` en el retorno de aristas condicionales

### Herramientas (Tools)

- Cada agente con al menos **una herramienta funcional** (`TavilySearchResults` o función propia sobre DB)

### Validación

- Nodo de **Validation**, o rúbrica en el prompt del Supervisor para validar resultados antes de `END`

### Documentación

- Diagrama del grafo (ej. `graph.get_graph().draw_mermaid_png()`)
- Explicar por qué se eligió esa topología y cómo se manejan conflictos entre agentes
