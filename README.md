# ERGONOMÍA PRO – Evaluación postural basada en REBA

Aplicación web Flask para cargar una fotografía, detectar puntos corporales mediante MediaPipe Pose, estimar ángulos articulares y generar un informe PDF con hallazgos y recomendaciones.

## Método
La aplicación utiliza una evaluación postural automatizada basada en los componentes del método REBA. El índice de cribado implementado es una estimación programática basada en ángulos visibles y factores complementarios declarados en el formulario. No debe presentarse como una aplicación oficial o validada de las tablas REBA ni como diagnóstico médico.

## Instalación local (Python 3.11)
```bash
python -m venv venv
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
python app.py
```
Abrir http://127.0.0.1:5000

## Despliegue en Render
- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn app:app`
- Runtime: Python 3.11.11

## Privacidad
Las fotografías se almacenan en `static/uploads` y los PDF en `informes`. Para uso público, configura almacenamiento persistente, políticas de retención, autenticación y consentimiento antes de procesar fotografías de trabajadores.
