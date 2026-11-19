import cv2
import mediapipe as mp
import math

mp_pose = mp.solutions.pose

# Colores en formato BGR
COLOR_LINEA = (20, 150, 220)
COLOR_PUNTO = (20, 20, 235)
COLOR_TEXTO = (255, 255, 255)
COLOR_FONDO = (25, 43, 60)


def angle(a, b, c):
    """Calcula el ángulo interior ABC entre 0 y 180 grados."""
    ax, ay = a
    bx, by = b
    cx, cy = c

    v1 = (ax - bx, ay - by)
    v2 = (cx - bx, cy - by)

    n1 = math.hypot(*v1)
    n2 = math.hypot(*v2)

    if n1 == 0 or n2 == 0:
        return 0.0

    cosine = (
        v1[0] * v2[0] + v1[1] * v2[1]
    ) / (n1 * n2)

    cosine = max(-1.0, min(1.0, cosine))

    return math.degrees(math.acos(cosine))


def clamp(value, minimum, maximum):
    return max(minimum, min(maximum, value))


def posture_band(value, bands):
    for limit, score, label in bands:
        if value <= limit:
            return score, label

    return bands[-1][1], bands[-1][2]


def _pixel(point, width, height):
    return (
        int(point[0] * width),
        int(point[1] * height)
    )


def _draw_label(image, text, anchor, offset=(12, -16)):
    """Dibuja una etiqueta legible sobre la fotografía."""

    h, w = image.shape[:2]

    font = cv2.FONT_HERSHEY_SIMPLEX
    scale = max(0.48, min(0.72, w / 1500))
    thickness = 2

    (tw, th), baseline = cv2.getTextSize(
        text,
        font,
        scale,
        thickness
    )

    x = int(clamp(
        anchor[0] + offset[0],
        4,
        max(4, w - tw - 16)
    ))

    y = int(clamp(
        anchor[1] + offset[1],
        th + 12,
        max(th + 12, h - baseline - 4)
    ))

    cv2.rectangle(
        image,
        (x - 6, y - th - 7),
        (x + tw + 7, y + baseline + 5),
        COLOR_FONDO,
        -1
    )

    cv2.putText(
        image,
        text,
        (x, y),
        font,
        scale,
        COLOR_TEXTO,
        thickness,
        cv2.LINE_AA
    )


def _annotate_angles(image, points, angle_values):
    """Dibuja las articulaciones y sus ángulos calculados."""

    h, w = image.shape[:2]

    px = {
        key: _pixel(value, w, h)
        for key, value in points.items()
    }

    chain = [
        "hombro",
        "codo",
        "muneca",
        "cadera",
        "rodilla",
        "tobillo"
    ]

    for first, second in zip(chain, chain[1:]):
        cv2.line(
            image,
            px[first],
            px[second],
            COLOR_LINEA,
            max(2, int(w / 500)),
            cv2.LINE_AA
        )

    for key in (
        "hombro",
        "codo",
        "cadera",
        "rodilla",
        "tobillo"
    ):
        radius = max(5, int(w / 100))

        cv2.circle(
            image,
            px[key],
            radius,
            COLOR_PUNTO,
            -1,
            cv2.LINE_AA
        )

        cv2.circle(
            image,
            px[key],
            radius,
            COLOR_TEXTO,
            2,
            cv2.LINE_AA
        )

    labels = [
        (
            "hombro",
            f"Hombro: {angle_values['hombro']:.1f}°",
            (12, -24)
        ),
        (
            "codo",
            f"Codo: {angle_values['codo']:.1f}°",
            (14, -22)
        ),
        (
            "cadera",
            f"Tronco: {angle_values['tronco']:.1f}°",
            (-150, -22)
        ),
        (
            "rodilla",
            f"Rodilla: {angle_values['rodilla']:.1f}°",
            (12, -20)
        )
    ]

    for key, text, offset in labels:
        _draw_label(
            image,
            text,
            px[key],
            offset
        )

    cv2.rectangle(
        image,
        (12, 12),
        (300, 48),
        COLOR_FONDO,
        -1
    )

    cv2.putText(
        image,
        "ANGULOS DETECTADOS AUTOMATICAMENTE",
        (22, 36),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.48,
        COLOR_TEXTO,
        1,
        cv2.LINE_AA
    )

    return image


def analizar_postura(
    path,
    carga="ligera",
    acoplamiento="regular",
    actividad="estatica"
):

    image = cv2.imread(path)

    if image is None:
        raise ValueError("No se pudo leer la imagen.")

    rgb = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2RGB
    )

    with mp_pose.Pose(
        static_image_mode=True,
        model_complexity=2,
        min_detection_confidence=0.45
    ) as pose:

        result = pose.process(rgb)

    if not result.pose_landmarks:
        raise ValueError(
            "No se detectó una postura corporal con suficiente claridad. "
            "Prueba con una fotografía donde se observe el cuerpo "
            "de lado o en tres cuartos."
        )

    lm = result.pose_landmarks.landmark
    P = mp_pose.PoseLandmark

    def pt(name):
        p = lm[getattr(P, name).value]
        return (p.x, p.y)

    def vis(name):
        return lm[getattr(P, name).value].visibility

    sides = [
        (
            "RIGHT",
            [
                "RIGHT_SHOULDER",
                "RIGHT_ELBOW",
                "RIGHT_WRIST",
                "RIGHT_HIP",
                "RIGHT_KNEE",
                "RIGHT_ANKLE"
            ]
        ),
        (
            "LEFT",
            [
                "LEFT_SHOULDER",
                "LEFT_ELBOW",
                "LEFT_WRIST",
                "LEFT_HIP",
                "LEFT_KNEE",
                "LEFT_ANKLE"
            ]
        )
    ]

    side = max(
        sides,
        key=lambda s: sum(vis(n) for n in s[1])
    )

    shoulder, elbow, wrist, hip, knee, ankle = [
        pt(n) for n in side[1]
    ]

    shoulder_vis = vis(side[1][0])
    hip_vis = vis(side[1][3])
    knee_vis = vis(side[1][4])
    ankle_vis = vis(side[1][5])

    # Cálculo de ángulos articulares
    elbow_angle = angle(
        shoulder,
        elbow,
        wrist
    )

    shoulder_angle = angle(
        hip,
        shoulder,
        elbow
    )

    hip_angle = angle(
        shoulder,
        hip,
        knee
    )

    knee_angle = angle(
        hip,
        knee,
        ankle
    )

    trunk_deviation = abs(180 - hip_angle)

    # Clasificación estimada de segmentos
    upper_score, upper_label = posture_band(
        shoulder_angle,
        [
            (20, 1, "Brazo próximo al tronco"),
            (45, 2, "Flexión ligera del brazo"),
            (90, 3, "Elevación moderada del brazo"),
            (180, 4, "Elevación marcada del brazo")
        ]
    )

    lower_score, lower_label = posture_band(
        elbow_angle,
        [
            (60, 2, "Codo muy flexionado"),
            (100, 1, "Codo dentro de un rango funcional"),
            (180, 2, "Codo extendido")
        ]
    )

    trunk_score, trunk_label = posture_band(
        trunk_deviation,
        [
            (10, 1, "Tronco cercano a posición neutra"),
            (20, 2, "Flexión o inclinación leve del tronco"),
            (60, 3, "Flexión o inclinación moderada del tronco"),
            (180, 4, "Flexión o inclinación marcada del tronco")
        ]
    )

    knee_score, knee_label = posture_band(
        knee_angle,
        [
            (30, 3, "Rodilla muy flexionada"),
            (60, 2, "Rodilla flexionada"),
            (120, 1, "Rodilla con flexión moderada"),
            (180, 2, "Rodilla extendida")
        ]
    )

    # Factores complementarios declarados por el evaluador
    load_score = {
        "ninguna": 0,
        "ligera": 0,
        "moderada": 1,
        "alta": 2
    }.get(carga, 0)

    coupling_score = {
        "bueno": 0,
        "regular": 1,
        "deficiente": 2
    }.get(acoplamiento, 1)

    activity_score = {
        "estatica": 1,
        "repetitiva": 1,
        "cambios": 1
    }.get(actividad, 1)

    total = int(clamp(
        upper_score
        + lower_score
        + trunk_score
        + knee_score
        + load_score
        + coupling_score
        + activity_score,
        1,
        15
    ))

    if total <= 3:
        level = "Bajo"
        color = "success"
        action = (
            "Mantener las condiciones y realizar pausas "
            "y seguimiento preventivo."
        )

    elif total <= 6:
        level = "Moderado"
        color = "warning"
        action = (
            "Conviene revisar la estación de trabajo "
            "y aplicar mejoras preventivas."
        )

    elif total <= 9:
        level = "Alto"
        color = "danger"
        action = (
            "Se recomienda intervenir la postura y las "
            "condiciones de trabajo a corto plazo."
        )

    else:
        level = "Muy alto"
        color = "danger"
        action = (
            "Se recomienda priorizar cambios ergonómicos "
            "y una revisión presencial."
        )

    findings = [
        {
            "name": "Tronco",
            "value": f"{trunk_deviation:.1f}° de desviación estimada",
            "angle": round(trunk_deviation, 1),
            "label": trunk_label,
            "score": trunk_score
        },
        {
            "name": "Brazo superior",
            "value": f"{shoulder_angle:.1f}°",
            "angle": round(shoulder_angle, 1),
            "label": upper_label,
            "score": upper_score
        },
        {
            "name": "Codo",
            "value": f"{elbow_angle:.1f}°",
            "angle": round(elbow_angle, 1),
            "label": lower_label,
            "score": lower_score
        },
        {
            "name": "Rodilla",
            "value": f"{knee_angle:.1f}°",
            "angle": round(knee_angle, 1),
            "label": knee_label,
            "score": knee_score
        }
    ]

    # Recomendaciones automáticas
    recs = []

    if trunk_score >= 2:
        recs.append(
            "Ajustar la altura y distancia de la superficie de trabajo "
            "para mantener el tronco erguido y evitar inclinarse "
            "hacia delante."
        )

    if upper_score >= 2:
        recs.append(
            "Acercar los elementos de uso frecuente y ajustar la altura "
            "de la superficie para mantener los hombros relajados."
        )

    if lower_score == 2:
        recs.append(
            "Revisar la ubicación de herramientas y materiales para "
            "favorecer un ángulo cómodo del codo, sin flexión "
            "o extensión extrema."
        )

    if knee_score >= 2:
        recs.append(
            "Verificar el apoyo de los pies y la altura del asiento "
            "o superficie para evitar posturas forzadas de las piernas."
        )

    if carga in ("moderada", "alta"):
        recs.append(
            "Reducir el peso manipulado cuando sea posible, "
            "dividir la carga y mantenerla cerca del cuerpo."
        )

    if actividad == "estatica":
        recs.append(
            "Incorporar pausas breves y cambios de postura "
            "durante la jornada."
        )

    elif actividad == "repetitiva":
        recs.append(
            "Alternar tareas y programar micropausas para disminuir "
            "la repetición continua."
        )

    else:
        recs.append(
            "Organizar el área para evitar cambios posturales bruscos "
            "y alcances repentinos."
        )

    if not recs:
        recs.append(
            "Mantener la organización actual y revisar periódicamente "
            "la postura durante la tarea."
        )

    # Valores que se muestran en la imagen, la página y el informe
    angle_values = {
        "hombro": round(shoulder_angle, 1),
        "codo": round(elbow_angle, 1),
        "cadera": round(hip_angle, 1),
        "tronco": round(trunk_deviation, 1),
        "rodilla": round(knee_angle, 1)
    }

    annotated = _annotate_angles(
        image.copy(),
        {
            "hombro": shoulder,
            "codo": elbow,
            "muneca": wrist,
            "cadera": hip,
            "rodilla": knee,
            "tobillo": ankle
        },
        angle_values
    )

    out = path.rsplit(".", 1)[0] + "_analizada.jpg"

    if not cv2.imwrite(out, annotated):
        raise ValueError(
            "No se pudo guardar la imagen con los ángulos calculados."
        )

    return {
        "metodo": "Evaluación postural automatizada basada en REBA",
        "indice": total,
        "nivel": level,
        "color": color,
        "accion": action,
        "hallazgos": findings,
        "recomendaciones": recs,
        "carga": carga,
        "acoplamiento": acoplamiento,
        "actividad": actividad,
        "angulos": angle_values,
        "lado": side[0],
        "imagen_analizada": out,
        "visibilidad": {
            "hombro": round(shoulder_vis, 2),
            "cadera": round(hip_vis, 2),
            "rodilla": round(knee_vis, 2),
            "tobillo": round(ankle_vis, 2)
        }
    }