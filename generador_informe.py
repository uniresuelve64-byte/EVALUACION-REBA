import os
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image
)
from reportlab.graphics.shapes import Drawing, Rect, String


NAVY = colors.HexColor("#17324d")
TEAL = colors.HexColor("#168f88")
PALE = colors.HexColor("#eaf2f7")
GRID = colors.HexColor("#cbd5e1")
MUTED = colors.HexColor("#526273")


def _chart_hallazgos(r):
    """Construye una gráfica de barras para el informe PDF."""

    width = 16.6 * cm
    height = 5.0 * cm

    drawing = Drawing(width, height)

    drawing.add(
        String(
            0,
            height - 12,
            "Puntos estimados por segmento",
            fontName="Helvetica-Bold",
            fontSize=10,
            fillColor=NAVY
        )
    )

    items = r.get("hallazgos", [])

    max_score = max(
        [int(x.get("score", 0)) for x in items] + [1]
    )

    label_w = 3.2 * cm
    chart_w = width - label_w - 1.0 * cm
    row_h = 0.82 * cm
    start_y = height - 1.15 * cm

    for i, item in enumerate(items):

        y = start_y - i * row_h

        label = str(item.get("name", ""))[:22]
        score = int(item.get("score", 0))

        drawing.add(
            String(
                0,
                y + 3,
                label,
                fontName="Helvetica",
                fontSize=8,
                fillColor=NAVY
            )
        )

        drawing.add(
            Rect(
                label_w,
                y,
                chart_w,
                0.34 * cm,
                fillColor=PALE,
                strokeColor=None
            )
        )

        bar_w = chart_w * score / max_score

        drawing.add(
            Rect(
                label_w,
                y,
                bar_w,
                0.34 * cm,
                fillColor=TEAL,
                strokeColor=None
            )
        )

        drawing.add(
            String(
                label_w + chart_w + 4,
                y + 3,
                str(score),
                fontName="Helvetica-Bold",
                fontSize=8,
                fillColor=NAVY
            )
        )

    return drawing


def _styles():

    styles = getSampleStyleSheet()

    styles.add(
        ParagraphStyle(
            name="TitleCenterREBA",
            parent=styles["Title"],
            alignment=TA_CENTER,
            textColor=NAVY,
            fontSize=16,
            leading=20,
            spaceAfter=7
        )
    )

    styles.add(
        ParagraphStyle(
            name="SmallNoteREBA",
            parent=styles["BodyText"],
            fontSize=7.5,
            leading=10,
            textColor=MUTED
        )
    )

    styles.add(
        ParagraphStyle(
            name="CellREBA",
            parent=styles["BodyText"],
            fontSize=8,
            leading=10,
            wordWrap="CJK",
            spaceAfter=0
        )
    )

    styles.add(
        ParagraphStyle(
            name="CellHeaderREBA",
            parent=styles["BodyText"],
            fontSize=8,
            leading=10,
            textColor=colors.white,
            fontName="Helvetica-Bold"
        )
    )

    styles.add(
        ParagraphStyle(
            name="BodyREBA",
            parent=styles["BodyText"],
            fontSize=9,
            leading=12,
            textColor=NAVY
        )
    )

    return styles


def generar_pdf(r, destino):

    styles = _styles()

    doc = SimpleDocTemplate(
        destino,
        pagesize=A4,
        rightMargin=1.55 * cm,
        leftMargin=1.55 * cm,
        topMargin=1.35 * cm,
        bottomMargin=1.35 * cm
    )

    cell = styles["CellREBA"]

    story = [
        Paragraph(
            "INFORME DE EVALUACIÓN ERGONÓMICA",
            styles["TitleCenterREBA"]
        ),
        Paragraph(
            "Análisis postural automatizado basado en componentes del método REBA",
            styles["Heading2"]
        ),
        Spacer(1, 8)
    ]

    # Información del trabajador
    data = [
        [
            Paragraph("Trabajador/a", cell),
            Paragraph(escape(str(r.get("nombre", ""))), cell),
            Paragraph("Fecha", cell),
            Paragraph(escape(str(r.get("fecha", ""))), cell)
        ],
        [
            Paragraph("Edad", cell),
            Paragraph(escape(str(r.get("edad", ""))), cell),
            Paragraph("Cargo", cell),
            Paragraph(escape(str(r.get("cargo", ""))), cell)
        ],
        [
            Paragraph("Área", cell),
            Paragraph(escape(str(r.get("area", ""))), cell),
            Paragraph("Lado analizado", cell),
            Paragraph(escape(str(r.get("lado", ""))), cell)
        ]
    ]

    info_table = Table(
        data,
        colWidths=[
            2.25 * cm,
            5.8 * cm,
            2.5 * cm,
            5.0 * cm
        ],
        hAlign="LEFT"
    )

    info_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), PALE),
            ("BACKGROUND", (2, 0), (2, -1), PALE),
            ("GRID", (0, 0), (-1, -1), 0.4, GRID),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6)
        ])
    )

    story += [
        info_table,
        Spacer(1, 12),
        Paragraph("Resultado general", styles["Heading2"])
    ]

    score_data = [
        [
            Paragraph(
                f"<b>Índice postural: {r['indice']} / 15</b>",
                styles["BodyREBA"]
            ),
            Paragraph(
                f"<b>Nivel: {escape(str(r['nivel']))}</b>",
                styles["BodyREBA"]
            )
        ],
        [
            Paragraph(
                escape(str(r["accion"])),
                styles["BodyREBA"]
            ),
            ""
        ]
    ]

    score_table = Table(
        score_data,
        colWidths=[7.8 * cm, 7.8 * cm]
    )

    score_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), PALE),
            ("SPAN", (0, 1), (-1, 1)),
            ("GRID", (0, 0), (-1, -1), 0.4, GRID),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("PADDING", (0, 0), (-1, -1), 7)
        ])
    )

    story += [
        score_table,
        Spacer(1, 11),
        Paragraph("Hallazgos posturales", styles["Heading2"])
    ]

    # Tabla corregida: textos ajustables y columnas separadas
    rows = [[
        Paragraph("Segmento", styles["CellHeaderREBA"]),
        Paragraph("Medición estimada", styles["CellHeaderREBA"]),
        Paragraph("Observación", styles["CellHeaderREBA"]),
        Paragraph("Puntos", styles["CellHeaderREBA"])
    ]]

    for item in r.get("hallazgos", []):

        rows.append([
            Paragraph(
                escape(str(item.get("name", ""))),
                cell
            ),
            Paragraph(
                escape(str(item.get("value", ""))),
                cell
            ),
            Paragraph(
                escape(str(item.get("label", ""))),
                cell
            ),
            Paragraph(
                str(item.get("score", "")),
                cell
            )
        ])

    findings_table = Table(
        rows,
        colWidths=[
            2.5 * cm,
            4.0 * cm,
            7.0 * cm,
            1.5 * cm
        ],
        repeatRows=1,
        hAlign="LEFT"
    )

    findings_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), NAVY),
            ("GRID", (0, 0), (-1, -1), 0.4, GRID),
            ("LEFTPADDING", (0, 0), (-1, -1), 7),
            ("RIGHTPADDING", (0, 0), (-1, -1), 7),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (-1, 1), (-1, -1), "CENTER")
        ])
    )

    story += [
        findings_table,
        Spacer(1, 12),
        _chart_hallazgos(r),
        Spacer(1, 8)
    ]

    # Ángulos
    story.append(
        Paragraph(
            "Ángulos calculados",
            styles["Heading2"]
        )
    )

    angles = r.get("angulos", {})

    angle_data = [
        [
            Paragraph("<b>Articulación</b>", styles["CellREBA"]),
            Paragraph("<b>Ángulo</b>", styles["CellREBA"])
        ],
        ["Hombro", f"{angles.get('hombro', 'N/D')}°"],
        ["Codo", f"{angles.get('codo', 'N/D')}°"],
        ["Cadera", f"{angles.get('cadera', 'N/D')}°"],
        ["Rodilla", f"{angles.get('rodilla', 'N/D')}°"],
        [
            "Desviación estimada del tronco",
            f"{angles.get('tronco', 'N/D')}°"
        ]
    ]

    angle_table = Table(
        angle_data,
        colWidths=[8 * cm, 7 * cm]
    )

    angle_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), PALE),
            ("GRID", (0, 0), (-1, -1), 0.4, GRID),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("PADDING", (0, 0), (-1, -1), 6)
        ])
    )

    story += [
        angle_table,
        Spacer(1, 10),
        Paragraph("Factores complementarios", styles["Heading2"]),
        Paragraph(
            escape(
                f"Carga o fuerza declarada: {r['carga']}. "
                f"Acoplamiento: {r['acoplamiento']}. "
                f"Actividad: {r['actividad']}."
            ),
            styles["BodyREBA"]
        ),
        Spacer(1, 10),
        Paragraph("Recomendaciones de mejora", styles["Heading2"])
    ]

    for i, rec in enumerate(
        r.get("recomendaciones", []),
        1
    ):

        story.append(
            Paragraph(
                f"{i}. {escape(str(rec))}",
                styles["BodyREBA"]
            )
        )

        story.append(Spacer(1, 4))

    # Fotografía con ángulos calculados
    annotated = r.get("imagen_analizada")

    if annotated and os.path.exists(annotated):

        story += [
            Spacer(1, 10),
            Paragraph(
                "Fotografía analizada con ángulos detectados",
                styles["Heading2"]
            ),
            Image(
                annotated,
                width=15.8 * cm,
                height=10.5 * cm,
                kind="proportional"
            )
        ]

    elif os.path.exists(r.get("imagen_archivo", "")):

        story += [
            Spacer(1, 10),
            Paragraph(
                "Fotografía original",
                styles["Heading2"]
            ),
            Image(
                r["imagen_archivo"],
                width=10 * cm,
                height=7 * cm,
                kind="proportional"
            )
        ]

    story += [
        Spacer(1, 10),
        Paragraph(
            "Nota metodológica: el índice presentado es una estimación "
            "automatizada de cribado postural basada en segmentos "
            "corporales visibles y factores complementarios declarados. "
            "No equivale a una aplicación certificada de las tablas "
            "oficiales REBA ni sustituye la valoración profesional.",
            styles["SmallNoteREBA"]
        )
    ]

    doc.build(story)