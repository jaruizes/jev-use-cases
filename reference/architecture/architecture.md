# Architecture — Jev Decision Lab

> **Estado:** propuesta inicial · **Alcance de esta versión:** arquitectura frontend.  
> **Principio:** una arquitectura fácil de leer y evolucionar, con un enfoque *Specification-Driven Development* (SDD) ligero, sin burocracia innecesaria.

## 1. Objetivos y principios

Jev Decision Lab es una PoC visual para comparar Jev, Claude y reglas deterministas en cuatro casos de uso: **Model Routing**, **Lead Scoring**, **Semantic Guardrails** y **Architecture Decision & Planning**.

La arquitectura debe permitir que alguien nuevo en el proyecto pueda identificar rápidamente:
1. Qué pantalla implementa una funcionalidad.
2. Dónde está la lógica de presentación.
3. Qué servicio llama al backend.
4. Qué contrato de datos intercambian frontend y API.
5. Cómo se prueba y amplía un caso de uso.

**Decisiones guía:**
- **Sencillez antes que abstracción.** No crear capas, interfaces o patrones sin una necesidad concreta.
- **Organización por funcionalidad (feature-first)** en lugar de agrupar toda la aplicación por tipos técnicos.
- **Componentes pequeños, con una responsabilidad identificable.** Evitar un componente raíz con toda la interfaz y lógica.
- **Servicios específicos** para la comunicación HTTP con el backend; los componentes no usan `HttpClient` directamente.
- **Tipado estricto** y contratos explícitos en el límite de la API.
- **Reutilización con criterio:** compartir lo que verdaderamente es común, no anticipar una plataforma genérica.
- **Separación de responsabilidades:** el frontend presenta y orquesta la interacción; el backend ejecuta proveedores, protege claves, calcula costes/métricas y persiste ejecuciones.

## 2. Enfoque SDD pragmático

Usaremos especificaciones cortas y vivas, **no** un proceso rígido.

Antes de desarrollar una funcionalidad:
- Redactar un pequeño apartado o ficha con **objetivo, comportamiento, entradas/salidas, estados de UI y criterios de aceptación**.
- Acordar el **contrato de API** que necesita (o indicar que todavía es provisional).
- Implementar el cambio en su módulo funcional con las pruebas relevantes.
- Actualizar la especificación si el comportamiento finalmente implementado cambia.

Esta página recoge las decisiones arquitectónicas. Las fichas funcionales podrán vivir en `reference/specifications/<feature>.md` cuando el código empiece a crecer. No exigimos una ficha para cambios triviales. Los detalles de implementación que no afecten a contratos o decisiones no necesitan documentación adicional.

**Definition of Done (ligera):** el caso se puede ejecutar visualmente, los estados de carga/error se muestran, el contrato está tipado, la lógica está en su lugar y las pruebas del cambio pasan.

## 3. Arquitectura frontend

### 3.1 Tecnologías y estilo

- **Angular** con TypeScript en modo estricto.
- **Standalone components** y **rutas con lazy loading** por funcionalidad. La palabra «módulo» se refiere aquí a un **módulo funcional**, no necesariamente a un `NgModule` de Angular.
- **Angular Router** para navegación.
- **HttpClient** en servicios de acceso a API.
- **Signals** y estado local de componentes para comenzar. No incorporar NgRx ni una solución global compleja sin evidencia de necesidad.
- **Reactive Forms** para entradas editables y validaciones.
- Estilos por componente y un pequeño sistema de variables/tokens compartidos; elegir biblioteca visual en una decisión separada si procede.
- Pruebas unitarias de servicios y lógica de UI, más unas pocas pruebas end-to-end de los recorridos principales.

No se fija una versión concreta de Angular hasta crear el proyecto y verificar compatibilidades.

### 3.2 Vista por capas

```text
                         Angular frontend
┌──────────────────────────────────────────────────────────────┐
│ App Shell / Router                                           │
│ navegación, layout, configuración global                     │
├──────────────────────────────────────────────────────────────┤
│ Features (módulos funcionales con carga diferida)             │
│ Dashboard | Playground | Benchmarks | Results                │
│                                                              │
│ Pages / containers  →  UI components  →  view models         │
│         │                                                    │
│         └──────────→ Feature facade/state (solo si aporta)   │
├──────────────────────────────────────────────────────────────┤
│ Services (acceso a API del backend)                          │
│ use-cases-api | executions-api | benchmarks-api | results-api│
│         │                                                    │
│         └──────────→ HttpClient / interceptors               │
├──────────────────────────────────────────────────────────────┤
│ Core (configuración, errores globales) | Shared (UI reusable)│
└───────────────────────────┬──────────────────────────────────┘
                            │ HTTP JSON / SSE cuando haga falta
                       FastAPI backend
                   Proveedores / métricas / datos
```

Los componentes **no acceden a los SDK de Jev ni Anthropic**; tampoco almacenan claves API. El backend centraliza esa responsabilidad.

### 3.3 Organización del código propuesta

```text
frontend/
└── src/
    └── app/
        ├── app.component.ts              # Solo el shell/router-outlet
        ├── app.config.ts                 # Providers globales
        ├── app.routes.ts                 # Rutas lazy
        ├── core/
        │   ├── config/                   # URL base, configuración runtime
        │   ├── http/                     # Interceptores, error mapping
        │   └── layout/                   # Cabecera, navegación, shell
        ├── shared/
        │   ├── ui/                       # Button, status, cards, loaders...
        │   ├── models/                   # Solo tipos realmente transversales
        │   └── utils/                    # Funciones puras compartidas
        ├── services/                     # Acceso HTTP a la API backend
        │   ├── use-cases-api.service.ts
        │   ├── executions-api.service.ts
        │   ├── benchmarks-api.service.ts
        │   └── results-api.service.ts
        └── features/
            ├── dashboard/
            │   ├── dashboard.page.ts
            │   └── components/
            ├── playground/
            │   ├── playground.page.ts
            │   ├── components/
            │   │   ├── use-case-selector/
            │   │   ├── provider-selector/
            │   │   ├── input-editor/
            │   │   └── execution-comparison/
            │   ├── use-cases/
            │   │   ├── model-routing/
            │   │   ├── lead-scoring/
            │   │   ├── semantic-guardrails/
            │   │   └── architecture-design/
            │   ├── models/
            │   └── state/                # Solo si la complejidad lo pide
            ├── benchmarks/
            │   ├── benchmarks.page.ts
            │   ├── components/
            │   └── models/
            └── results/
                ├── results.page.ts
                ├── components/
                └── models/
```

**Regla práctica:** si una pieza solo se utiliza dentro de una feature, permanece en esa feature. Pasará a `shared/` únicamente cuando se reutilice de verdad. Los modelos de datos de una API no se duplicarán en distintas features: tendrán un único origen bien identificado.

### 3.4 Responsabilidades

| Elemento | Responsabilidad | Qué NO debe hacer |
| --- | --- | --- |
| `app.component.ts` | Composición del shell y outlet | Implementar los cuatro casos de uso |
| `features/*/*.page.ts` | Coordinar la pantalla, navegación y eventos | Llamadas HTTP directas o cálculos de benchmark |
| `features/*/components/` | Renderizar partes pequeñas, emitir interacciones | Conocer credenciales o endpoints |
| `features/playground/use-cases/` | Formularios y presentación específicos de cada caso | Duplicar componentes comunes o invocar proveedores |
| `services/*-api.service.ts` | Construir peticiones HTTP tipadas y devolver respuestas/observables | Gestionar lógica de negocio del backend o controlar el DOM |
| `core/` | Configuración, interceptores y comportamiento global | Almacenar lógica específica de una feature |
| `shared/` | UI y utilidades realmente transversales | Convertirse en un repositorio de todo |

**Flujo recomendado:** página → servicio API → backend → respuesta tipada → estado local de la página → componentes de presentación.

Una feature puede introducir un pequeño **facade/state service** cuando varios componentes necesitan compartir estado o coordinar peticiones. No es obligatorio en todas las features.

### 3.5 Capa `services/`: acceso a backend

La frontera frontend/backend debe ser explícita:

- Usar `environment` o configuración runtime para la **URL base**, nunca URLs dispersas en componentes.
- Definir modelos `request/response` tipados para cada endpoint.
- Mantener llamadas HTTP exclusivamente en los servicios de API.
- Normalizar errores de red y HTTP en un formato consumible por la UI.
- Para benchmarks prolongados, usar un endpoint de inicio y otro de estado o **SSE** para progreso. Evitar mantener una única petición HTTP abierta de manera indefinida.
- No enviar ni exponer API keys de proveedores en el navegador.
- Compartir contratos mediante OpenAPI generado desde FastAPI cuando el backend exista; **preferir tipos TypeScript generados** si eso evita divergencias, sin introducir generación prematura.

**Interfaz orientativa (contrato provisional, no implementado):**

```ts
export interface ExecuteUseCaseRequest {
  useCaseId: 'model-routing' | 'lead-scoring' |
             'semantic-guardrails' | 'architecture-design';
  providerIds: string[];
  input: Record<string, unknown>;
}

export interface ProviderExecutionResult {
  providerId: string;
  status: 'success' | 'error';
  output?: unknown;
  latencyMs?: number;
  estimatedCostUsd?: number;
  error?: string;
}

export interface ExecuteUseCaseResponse {
  executionId: string;
  results: ProviderExecutionResult[];
}
```

El tipo `Record<string, unknown>` se utiliza aquí solo como **borrador transversal**; antes de implementar cada caso se crearán DTO específicos y validación de entrada para evitar propagar estructuras sin tipar.

**Ejemplo de uso previsto:**

```ts
@Injectable({ providedIn: 'root' })
export class ExecutionsApiService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = inject(API_BASE_URL);

  execute(request: ExecuteUseCaseRequest) {
    return this.http.post<ExecuteUseCaseResponse>(
      `${this.baseUrl}/executions`, request
    );
  }
}
```

Este snippet ilustra responsabilidades y dependencia; no pretende fijar todavía el contrato REST definitivo.

### 3.6 Navegación y estados de UI

Rutas iniciales propuestas:
- `/` — Dashboard, explicación y navegación a los cuatro casos.
- `/playground/:useCaseId` — Editor, selección de proveedores y comparación de respuestas.
- `/benchmarks` — Configuración e inicio de ejecuciones masivas.
- `/benchmarks/:runId` — Progreso e indicadores del benchmark.
- `/results/:executionId` — Inspección detallada de una ejecución.

Cada pantalla que invoque el backend debe contemplar **idle, loading, success, empty y error**. Evitar que los errores desaparezcan silenciosamente o que un resultado parcial parezca una ejecución completa.

### 3.7 Legibilidad y convenciones

- Cada componente tendrá nombre y propósito claros, con archivos `.ts`, `.html` y `.scss` separados cuando el template deje de ser trivial.
- Evitar grandes templates inline, condicionales anidados y métodos extensos que mezclen renderizado, transformación de datos y API.
- Nombres de componentes y servicios en inglés; comentarios para explicar el **porqué**, no repetir el código.
- Mantener la lógica de dominio/normalización en funciones puras o servicios claramente identificados.
- Aplicar lint y formato automáticos. No obsesionarse con tamaños fijos de archivos: **dividir cuando aparecen responsabilidades diferentes**.
- No introducir una clase base, repositorio genérico ni framework de estado por cada feature sin necesidad real.

### 3.8 Testing frontend

**Mínimos:**
- Unit tests de transformaciones/presentadores y validaciones no triviales.
- Tests de componentes de formularios y estados (loading, error, results).
- Tests de servicios API con respuestas HTTP simuladas (sin llamadas reales en CI).
- E2E de apertura de la app, selección de caso, edición, ejecución simulada y visualización comparada.
- Accesibilidad básica: etiquetas, foco, estados y teclado.

Las pruebas de proveedores externos corresponden al backend; no se llaman desde los tests frontend.

### 3.9 Decisiones diferidas

No fijamos todavía:
- Librería de componentes UI y librería de gráficas.
- Versión exacta de Angular y librerías.
- Contratos finales de endpoints/DTO, pendientes del diseño backend.
- Necesidad de estado global, autenticación o despliegue público.

Se resolverán cuando exista un caso concreto y se documentará brevemente el motivo.

## 4. Arquitectura backend (pendiente)

En una siguiente iteración se definirán FastAPI, adaptadores de Jev/Claude, evaluación, ejecución de benchmarks, almacenamiento, contratos OpenAPI y observabilidad. El frontend no asumirá detalles internos de esos componentes.

## 5. Decisiones registradas

| ID | Decisión | Estado |
| --- | --- | --- |
| FE-001 | Arquitectura Angular **feature-first** y standalone components | Propuesta inicial |
| FE-002 | `services/` como capa exclusiva de acceso a API | Propuesta inicial |
| FE-003 | Estado local con signals; complejidad adicional solo cuando sea necesaria | Propuesta inicial |
| FE-004 | Lazy routes y separación en páginas/componentes pequeños | Propuesta inicial |
| FE-005 | Backend como responsable de claves, proveedores, costes y persistencia | Propuesta inicial |
| FE-006 | Especificaciones breves y contratos explícitos (SDD pragmático) | Propuesta inicial |

Cuando se revise una decisión, se actualizará esta tabla y su apartado correspondiente, evitando documentación paralela contradictoria.
