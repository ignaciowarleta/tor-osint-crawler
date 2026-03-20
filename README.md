# Tor OSINT Crawler

![Python](https://img.shields.io/badge/Python-3.x-blue?logo=python)
![Tor Network](https://img.shields.io/badge/Tor-Network-7D4698?logo=torproject&logoColor=white)
![OSINT](https://img.shields.io/badge/OSINT-Analysis-2C7BE5)
![Cybersecurity](https://img.shields.io/badge/Cybersecurity-Research-D7263D)
![Status](https://img.shields.io/badge/Status-Active-2ECC71)

<img width="1280" height="640" alt="image" src="https://github.com/user-attachments/assets/32e090e5-b0dd-4187-91a5-a79e14b2a37a" />


Herramienta en Python para el crawling de servicios `.onion` a través de la red Tor, orientada a la recopilación de metadatos y análisis básico OSINT.

El proyecto permite analizar páginas onion de forma controlada, extrayendo información relevante como enlaces, palabras clave y clasificación de contenido.

---

## Características

- Conexión a la red Tor mediante proxy SOCKS5
- Crawling limitado de servicios `.onion`
- Extracción de:
  - Título de la página
  - Enlaces internos
  - Contenido textual
- Detección de palabras clave relevantes
- Clasificación automática de páginas
- Exportación de resultados en:
  - JSON
  - CSV
- Control de profundidad (número de páginas)
- Manejo de errores de conexión

---

## Tecnologías utilizadas

- Python
- Requests
- BeautifulSoup
- Tor (SOCKS5 Proxy)

---

## Instalación

### 1. Clonar el repositorio

```
git clone https://github.com/tu-usuario/tor-osint-crawler.git
cd tor-osint-crawler
```

### 2. Crear entorno virtual

```
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Instalar dependencias

```
pip install -r requirements.txt
```

---

## Configuración de Tor

Es necesario tener Tor ejecutándose en local.

### Instalar Tor (Mac)

```
brew install tor
```

### Ejecutar Tor

```
tor
```

Deberías ver:

```
Bootstrapped 100% (done): Done
```

Esto indica que Tor está funcionando en:

```
127.0.0.1:9050
```

---

## Uso

Ejecutar el crawler indicando una URL `.onion`:

```
python crawler.py <url_onion> [max_pages]
```

### Ejemplo

```
python crawler.py https://duckduckgogg42xjoc72x3sjasowoarfbgcmvfimaftt6twagswzczad.onion 2
```

---

## Salida

### Consola

```
=== Resumen del crawl ===
Páginas analizadas: 2

URL: ...
Status: 200
Título: ...
Categoría: search_engine
Keywords: {'search': 3}
Enlaces encontrados: 5
```

---

## Archivos generados

```
results/
├── crawl_results.json
├── crawl_results.csv
```

---

## Ejemplo JSON

```
{
  "url": "...",
  "status_code": 200,
  "title": "...",
  "category": "login_page",
  "keywords": {
    "login": 3,
    "password": 1
  }
}
```

---

## Ejemplo CSV

```
url,status,title,category,num_links,keywords
http://...,200,Login Page,login_page,5,login,password
```

---

## Clasificación de páginas

El sistema clasifica automáticamente las páginas en función de palabras clave detectadas:

- **login_page** → Formularios de acceso
- **forum** → Foros o discusiones
- **marketplace** → Páginas relacionadas con transacciones
- **service** → Servicios o contacto
- **leak_site** → Posibles filtraciones
- **general** → Contenido genérico
- **unknown** → Sin clasificación

---

## Estructura del proyecto

```
tor-osint-crawler/
│
├── crawler.py
├── requirements.txt
│
├── utils/
│   ├── keywords.py
│   └── classifier.py
│
├── results/
│   ├── crawl_results.json
│   └── crawl_results.csv
│
└── README.md
```

---

## Consideraciones éticas

Este proyecto está diseñado exclusivamente para:

- uso educativo
- investigación OSINT
- análisis de metadatos

No está destinado a:

- crawling agresivo
- scraping masivo
- acceso a contenido ilegal

Se recomienda:

- limitar el número de páginas analizadas
- no almacenar contenido sensible
- respetar el uso responsable de la red Tor

---

## Posibles mejoras

- Análisis de riesgo por página
- Visualización de relaciones entre enlaces
- Detección de idioma
- Integración con fuentes de threat intelligence
- Soporte para crawling multi-dominio
- Dashboard de resultados

---

## Autor

Ignacio Warleta Murcia  
Ingeniero Informático | Ciberseguridad

---
